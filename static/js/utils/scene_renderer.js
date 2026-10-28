import { ArrayRenderer } from './array_renderer.js';
import { GraphRenderer } from './graph_renderer.js';
import { WindowRenderer } from './window_renderer.js';

const RENDERER_BY_TYPE = {
    'vector': ArrayRenderer,
    'graph': GraphRenderer,
};

export class SceneRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.container.classList.add('scene-container');

        this.windows = new Map();            // windowId  → WindowRenderer
        this.renderers = new Map();          // structureName → BaseRenderer
        this.windowByStructure = new Map();  // structureName → windowId

        this.activeTab = 'all';   // 'all' | 'window:<id>'
        this.onWindowsChanged = null;

        this.settings = {
            speedFactor: 1.0,
            elementSize: 40,
            spacing: 12,
            colors: {
                comparing: '#9400D3',
                swapping: '#FF6B6B',
                sorted: '#4169E1',
                default: '#e0e0e0'
            },
            showIndices: true,
        };

        this.snapshots = [];
    }

    setSnapshots(snapshots) {
        this.snapshots = snapshots || [];
    }

    clear() {
        for (const r of this.renderers.values()) {
            if (r.clear) r.clear();
        }
        this.renderers.clear();
        this.windowByStructure.clear();
        for (const w of this.windows.values()) w.remove();
        this.windows.clear();
        this.container.innerHTML = '';
    }

    // ---------- Восстановление всей картины ----------
    applySnapshot(snapshot) {
        this.clear();
        if (!snapshot || !snapshot.structures) return;

        // 1) Окна
        for (const [wid, wData] of Object.entries(snapshot.windows || {})) {
            const wr = new WindowRenderer(wid, wData.title || wid);
            wr.setVisible(wData.visible);
            wr.appendTo(this.container);
            this.windows.set(wid, wr);
            if (wData.structureName) {
                this.windowByStructure.set(wData.structureName, wid);
            }
        }
        this._applyActiveTabClasses();

        // 2) Структуры
        for (const [name, frag] of Object.entries(snapshot.structures)) {
            const RendererClass = RENDERER_BY_TYPE[frag.type];
            if (!RendererClass) continue;

            const wid = this.windowByStructure.get(name);
            let host;
            if (wid && this.windows.has(wid)) {
                host = this.windows.get(wid).content;
            } else {
                host = this._createHiddenHost();
            }

            const r = new RendererClass(host);
            r.updateSettings(this.settings);
            this.renderers.set(name, r);
            r.applySnapshot(frag);
        }

        if (this.onWindowsChanged) this.onWindowsChanged();
    }

    // Единая точка для всех сценариев, меняющих геометрию сцены.
    // Гарантирует:
    //   1. Изменение видно на экране сразу, без transition.
    //   2. К моменту возврата управления вызывающему коду
    //      no-transition снят → следующая команда (highlight,
    //      swap) снова анимируется обычным образом.
    //
    // mutator   — функция, меняющая DOM/классы (может быть null).
    // targets   — итератор рендереров для updateLayout.
    //             Если не передан — обновляются все.
    commitLayout(mutator = null, targets = null) {
        // 1. Отключаем все transition на сцене.
        this.container.classList.add('no-transition');
        void this.container.getBoundingClientRect();     // reflow

        // 2. Мутируем DOM / классы.
        if (typeof mutator === 'function') mutator();

        // 3. Фиксируем изменения (иначе updateLayout прочитает старые размеры).
        void this.container.getBoundingClientRect();

        // 4. Пересчёт layout у нужных рендереров.
        const list = targets ? Array.from(targets) : Array.from(this.renderers.values());
        for (const r of list) {
            if (r && r.updateLayout) r.updateLayout();
        }

        // 5. Фиксируем новые позиции — без анимации.
        void this.container.getBoundingClientRect();

        // 6. Синхронно снимаем no-transition.
        this.container.classList.remove('no-transition');
    }

    // ---------- Проигрывание команд ----------
    async executeCommand(command, skipAnimation = false, commandIndex = null) {
        if (!command) return;

        // Верхнеуровневые команды — обрабатываются первыми
        switch (command.component) {
            case 'wait':
                await this._sleep((command.params?.duration || 0) / this.settings.speedFactor);
                return;
            case 'condition_true':
            case 'condition_false':
                await this._notify(
                    command.params?.condition || '',
                    command.component === 'condition_true'
                );
                return;
            case 'set_variable':
                await this._notify(
                    `${command.params?.variable} = ${command.params?.value}`,
                    null
                );
                return;
            case 'create_window':
                this._handleCreateWindow(command);
                return;
            case 'add_structure_to_window':
                this._handleAttach(command, skipAnimation);
                return;
            case 'show_window':
                this._handleWindowVisibility(command.window, true, skipAnimation);
                return;
            case 'hide_window':
                this._handleWindowVisibility(command.window, false, skipAnimation);
                return;
        }

        // Команды, адресованные структуре
        if (command.structure) {
            if (!this.renderers.has(command.structure)) {
                const type = command.component === 'create_graph' ? 'graph' : 'vector';
                this._ensureRenderer(command.structure, type, commandIndex);
            }
            const r = this.renderers.get(command.structure);
            if (r) {
                const effectiveSkip = skipAnimation
                    || this._shouldSkipForStructure(command.structure);
                await r.executeCommand(command, effectiveSkip, commandIndex);
            }
            return;
        }

        // Ничего не подошло — игнорируем
    }

    // ---------- Ленивое создание рендерера ----------
    _ensureRenderer(structureName, type, commandIndex) {
        if (this.renderers.has(structureName)) {
            return this.renderers.get(structureName);
        }

        // Куда монтировать: если структура уже привязана к окну — в его
        // content, иначе — в скрытый host. Перенос в окно выполняет
        // _handleAttach, когда придёт команда add_structure_to_window.
        const wid = this.windowByStructure.get(structureName);
        let host;
        if (wid && this.windows.has(wid)) {
            host = this.windows.get(wid).content;
        } else {
            host = this._createHiddenHost();
        }

        const RendererClass = RENDERER_BY_TYPE[type];
        if (!RendererClass) return null;

        const r = new RendererClass(host);
        r.updateSettings(this.settings);
        this.renderers.set(structureName, r);
        return r;
    }

    _createHiddenHost() {
        const host = document.createElement('div');
        host.style.display = 'none';
        // Заполняем родителя через absolute+inset: 0 — это работает
        // независимо от того, как у родителя резолвится высота
        // (в отличие от height: 100%, которое в All-режиме даёт 0).
        host.style.position = 'absolute';
        host.style.top = '0';
        host.style.right = '0';
        host.style.bottom = '0';
        host.style.left = '0';
        this.container.appendChild(host);
        return host;
    }

    _handleCreateWindow(command) {
        const wid = command.window;
        if (this.windows.has(wid)) return;

        const wr = new WindowRenderer(wid, command.title || wid);
        wr.setVisible(true);
        wr.appendTo(this.container);
        this.windows.set(wid, wr);

        this._applyActiveTabClasses();
        if (this.onWindowsChanged) this.onWindowsChanged();
    }

    async _handleAttach(command, skipAnimation = false) {
        const name = command.structure;
        const wid = command.window;

        // Окно могло быть не создано (например, плеер начал
        // воспроизводить с середины без create_window) — создаём.
        if (!this.windows.has(wid)) {
            const wr = new WindowRenderer(wid, wid);
            wr.setVisible(true);
            wr.appendTo(this.container);
            this.windows.set(wid, wr);
        }

        this.windowByStructure.set(name, wid);

        const r = this.renderers.get(name);
        const wr = this.windows.get(wid);

        if (r && wr && r.container.parentNode !== wr.content) {
            this.commitLayout(() => {
                r.container.style.display = '';
                wr.content.appendChild(r.container);
                this._applyActiveTabClasses();
            }, [r]);
        } else {
            // Рендерера ещё нет (структура создана командой позже) —
            // layout пересчитывать нечего, но классы вкладки обновить надо.
            this._applyActiveTabClasses();
        }

        if (this._isWindowActuallyVisible(wid)) {
            await this._notifyVisibilityChanged(skipAnimation);
        } else {
            const r2 = this.renderers.get(name);
            if (r2 && typeof r2.cancelPendingReveal === 'function') {
                r2.cancelPendingReveal();
            }
        }

        if (this.onWindowsChanged) this.onWindowsChanged();
    }

    async _handleWindowVisibility(wid, visible, skipAnimation = false) {
        const wr = this.windows.get(wid);
        if (!wr) return;

        const targets = [];
        for (const [name, r] of this.renderers) {
            if (this.windowByStructure.get(name) === wid) targets.push(r);
        }

        this.commitLayout(() => {
            wr.setVisible(visible);
            this._applyActiveTabClasses();
        }, targets);

        await this._notifyVisibilityChanged(skipAnimation);

        if (this.onWindowsChanged) this.onWindowsChanged();
    }

    _shouldSkipForStructure(structureName) {
        if (this.activeTab === 'all') return false;
        const wid = this.windowByStructure.get(structureName);
        if (wid === undefined) return false;
        return this.activeTab !== 'window:' + wid;
    }

    // Реальная видимость окна с учётом активной вкладки.
    // Window.visible — это «окно включено», а не «окно показано сейчас».
    _isWindowActuallyVisible(wid) {
        if (!wid) return false;
        const wr = this.windows.get(wid);
        if (!wr || !wr.visible) return false;
        if (this.activeTab === 'all') return true;
        return this.activeTab === 'window:' + wid;
    }

    // Оповещает рендереры структур о том, что видимость могла измениться.
    // Каждый рендерер сам решает, реагировать ли (обычно — только
    // на первый показ). Пропускаем невидимые контейнеры.
    async _notifyVisibilityChanged(skipAnimation = false) {
        const promises = [];
        for (const [name, r] of this.renderers) {
            if (!r || !r.onBecameVisible) continue;
            const wid = this.windowByStructure.get(name);
            if (!this._isWindowActuallyVisible(wid)) continue;
            if (r.container.offsetWidth === 0) continue;
            promises.push(r.onBecameVisible(skipAnimation));
        }
        await Promise.all(promises);
    }

    // ---------- Настройки / layout ----------
    updateSettings(newSettings) {
        if (!newSettings) return;
        Object.assign(this.settings, newSettings);
        for (const r of this.renderers.values()) {
            r.updateSettings(newSettings);
        }
    }

    async setActiveTab(tabId, skipAnimation = false) {
        this.activeTab = tabId;

        let targets;
        if (tabId === 'all') {
            targets = Array.from(this.renderers.values());
        } else {
            const wid = tabId.replace('window:', '');
            targets = [];
            for (const [name, r] of this.renderers) {
                if (this.windowByStructure.get(name) === wid) targets.push(r);
            }
        }

        this.commitLayout(
            () => this._applyActiveTabClasses(),
            targets,
        );

        await this._notifyVisibilityChanged(skipAnimation);
    }

    _applyActiveTabClasses() {
        const isAll = this.activeTab === 'all';
        this.container.classList.toggle('mode-all', isAll);
        this.container.classList.toggle('mode-single', !isAll);

        const parent = this.container.parentElement;
        if (parent) {
            parent.classList.toggle('mode-all', isAll);
            parent.classList.toggle('mode-single', !isAll);
        }

        const activeWid = isAll ? null : this.activeTab.replace('window:', '');
        for (const [id, wr] of this.windows) {
            wr.element.classList.toggle('active-window', id === activeWid);
        }
    }

    updateLayout() {
        for (const r of this.renderers.values()) {
            if (r.updateLayout) r.updateLayout();
        }
    }

    // ---------- Служебное ----------
    _sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async _notify(text, positive) {
        if (!text) return;
        const n = document.createElement('div');
        n.className = 'scene-notification';
        n.textContent = text;
        if (positive === true) n.style.background = '#4CAF50';
        else if (positive === false) n.style.background = '#f44336';
        else n.style.background = '#2196F3';
        document.body.appendChild(n);
        setTimeout(() => {
            n.style.opacity = '0';
            setTimeout(() => n.remove(), 300);
        }, 1500 / this.settings.speedFactor);
    }
}
