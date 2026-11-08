import { ArrayRenderer } from './array_renderer.js';
import { GraphRenderer } from './graph_renderer.js';
import { WindowRenderer } from './window_renderer.js';

const RENDERER_BY_TYPE = {
    'vector': ArrayRenderer,
    'graph': GraphRenderer,
    'tree': GraphRenderer,
};

export class SceneRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.container.classList.add('scene-container');

        this.container.innerHTML = '';

        // Обёртка для глобального pan (CSS transform).
        this._inner = document.createElement('div');
        this._inner.className = 'scene-inner';
        this.container.appendChild(this._inner);

        this._sceneOffsetX = 0;
        this._sceneOffsetY = 0;
        this._scenePanning = false;
        this._scenePanStart = null;
        this._sceneTouchPan = null;
        this._scenePinch = null;
        this._sceneTouchMoved = false;
        this._sceneLastTapTime = 0;
        this._sceneUserPanned = false;

        this.windows = new Map();            // windowId  → WindowRenderer
        this.renderers = new Map();          // structureName → BaseRenderer
        this.windowByStructure = new Map();  // structureName → windowId

        this.activeTab = 'all';   // 'all' | 'window:<id>'
        this.onWindowsChanged = null;
        this.onSizeChanged = null;
        this._notificationContainer = null;
        this._updatingHeights = false;
        this._inCommitLayout = false;
        this._infoMode = false;
        this._tooltip = null;
        this._lastMouse = null;

        this.settings = {
            speedFactor: 1.0,
            elementSize: 40,
            spacing: 10,
            structureGap: 20,
            colors: {
                comparing: '#9400D3',
                swapping: '#FF6B6B',
                sorted: '#4169E1',
                default: '#e0e0e0'
            },
            showIndices: true,
        };

        this.snapshots = [];

        this._bindSceneViewEvents();
        this._bindInfoEvents();

        if (typeof ResizeObserver !== 'undefined') {
            this._sceneResizeObserver = new ResizeObserver(() => {
                if (this.activeTab !== 'all') {
                    this._reclampSceneOffset();
                }
            });
            this._sceneResizeObserver.observe(this.container);
        }
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
        // Опустошаем _inner, но НЕ удаляем его: applySnapshot
        // вызывает clear() и сразу использует _inner дальше.
        // При restart (новый SceneRenderer) старый _inner
        // удаляется через `this.container.innerHTML = ''` в конструкторе.
        if (this._inner) {
            this._inner.innerHTML = '';
        }
        if (this._notificationContainer) {
            this._notificationContainer.remove();
            this._notificationContainer = null;
        }
        if (this._tooltip) {
            this._tooltip.remove();
            this._tooltip = null;
        }
        this._infoMode = false;
        this._lastMouse = null;
    }

    // ---------- Восстановление всей картины ----------
    applySnapshot(snapshot) {
        this.clear();
        this._sceneOffsetX = 0;
        this._sceneOffsetY = 0;
        this._sceneUserPanned = false;

        if (!snapshot || !snapshot.structures) return;

        // Всё создание — в commitLayout: на момент applySnapshotImmediate
        // контейнер структуры ещё не имеет высоты, элементы паркуются
        // «над» контейнером. Финальный updateLayout внутри commitLayout
        // пересчитает их после того, как _updateWindowHeights установит
        // всем structure_host и content правильные высоты.
        this.commitLayout(() => {
            // 1) Окна
            for (const [wid, wData] of Object.entries(snapshot.windows || {})) {
                const wr = new WindowRenderer(wid, wData.title || wid);
                wr.setVisible(wData.visible);
                wr.appendTo(this._inner);
                this.windows.set(wid, wr);
                if (Array.isArray(wData.structureNames)) {
                    for (const name of wData.structureNames) {
                        this.windowByStructure.set(name, wid);
                    }
                }
            }
            this._applyActiveTabClasses();

            // 2) Структуры
            // Порядок внутри окна задаётся wData.structureNames —
            // это JSON-массив, порядок attach сохраняется. Object.entries
            // (snapshot.structures) идёт по алфавиту (Flask jsonify
            // сортирует ключи), поэтому для создания div-ов в правильном
            // порядке используем structureNames.
            const created = [];
            const handled = new Set();

            // 2.1) Сначала — структуры, привязанные к окнам,
            // в порядке structureNames каждого окна.
            for (const [wid, wData] of Object.entries(snapshot.windows || {})) {
                const wr = this.windows.get(wid);
                if (!wr) continue;
                const names = Array.isArray(wData.structureNames) ? wData.structureNames : [];
                for (const name of names) {
                    const frag = snapshot.structures[name];
                    if (!frag || handled.has(name)) continue;
                    handled.add(name);

                    const RendererClass = RENDERER_BY_TYPE[frag.type];
                    if (!RendererClass) continue;

                    const host = wr.ensureStructureHost(name);
                    const r = new RendererClass(host);
                    r.updateSettings(this.settings);
                    r.setZoomEnabled(this.activeTab !== 'all');
                    this.renderers.set(name, r);
                    r.applySnapshot(frag);
                    created.push({ name, r });
                }
            }

            // 2.2) Оставшиеся — структуры без привязки к окну (в hidden host).
            for (const [name, frag] of Object.entries(snapshot.structures)) {
                if (handled.has(name)) continue;
                const RendererClass = RENDERER_BY_TYPE[frag.type];
                if (!RendererClass) continue;

                const host = this._createHiddenHost();
                const r = new RendererClass(host);
                r.updateSettings(this.settings);
                r.setZoomEnabled(this.activeTab !== 'all');
                this.renderers.set(name, r);
                r.applySnapshot(frag);
                created.push({ name, r });
            }

            for (const { r } of created) {
                r.onLayoutChanged = () => this._updateWindowHeights();
                r.onSizeChanged = (size) => {
                    if (this.onSizeChanged) this.onSizeChanged(size);
                };
            }

            this._updateWindowHeights();

            this._sceneOffsetX = 0;
            this._sceneOffsetY = 0;
            this._applySceneOffset();
            void this._inner.getBoundingClientRect();   // reflow

            if (this.activeTab !== 'all') {
                const bounds = this._computeSceneContentBounds();
                this._sceneOffsetX = this._clampSceneOffsetX(0, bounds);
                this._sceneOffsetY = this._clampSceneOffsetY(0, bounds);
            }
            this._applySceneOffset();
        });

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
        // Защита от рекурсии: если уже в commitLayout, не снимаем
        // no-transition раньше времени — иначе внешний вызов
        // останется без защиты (наблюдалось при applySnapshot:
        // onLayoutChanged → _updateWindowHeights → вложенный commitLayout
        // снимал класс до завершения внешнего прохода).
        if (this._inCommitLayout) {
            if (typeof mutator === 'function') mutator();
            const nestedList = targets ? Array.from(targets) : [];
            for (const r of nestedList) {
                if (r && r.updateLayout) r.updateLayout();
            }
            return;
        }
        this._inCommitLayout = true;
        try {
            this.container.classList.add('no-transition');
            void this.container.getBoundingClientRect();

            if (typeof mutator === 'function') mutator();

            void this.container.getBoundingClientRect();

            const list = targets ? Array.from(targets) : Array.from(this.renderers.values());
            for (const r of list) {
                if (r && r.updateLayout) r.updateLayout();
            }

            void this.container.getBoundingClientRect();

            this.container.classList.remove('no-transition');
        } finally {
            this._inCommitLayout = false;
        }
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
                await this._handleAttach(command, skipAnimation);
                return;
            case 'show_window':
                await this._handleWindowVisibility(command.window, true, skipAnimation);
                return;
            case 'hide_window':
                await this._handleWindowVisibility(command.window, false, skipAnimation);
                return;
        }

        // Команды, адресованные структуре
        if (command.structure) {
            if (!this.renderers.has(command.structure)) {
                // Тип берём из снапшота — так дерево (которое тоже
                // порождает create_graph) не спутается с графом.
                const snap = this.snapshots[commandIndex ?? 0];
                const frag = snap && snap.structures
                    ? snap.structures[command.structure] : null;
                const type = frag?.type
                    || (command.component === 'create_graph' ? 'graph' : 'vector');
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
            host = this.windows.get(wid).ensureStructureHost(structureName);
        } else {
            host = this._createHiddenHost();
        }

        const RendererClass = RENDERER_BY_TYPE[type];
        if (!RendererClass) return null;

        const r = new RendererClass(host);
        r.updateSettings(this.settings);
        r.onLayoutChanged = () => this._updateWindowHeights();
        r.onSizeChanged = (size) => {
            if (this.onSizeChanged) this.onSizeChanged(size);
        };
        r.setZoomEnabled(this.activeTab !== 'all');
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
        this._inner.appendChild(host);
        return host;
    }

    _handleCreateWindow(command) {
        const wid = command.window;
        if (this.windows.has(wid)) return;

        const wr = new WindowRenderer(wid, command.title || wid);
        wr.appendTo(this._inner);
        this.windows.set(wid, wr);

        this._applyActiveTabClasses();
        if (this.activeTab !== 'all') this._reclampSceneOffset();
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
            wr.appendTo(this._inner);
            this.windows.set(wid, wr);
        }

        this.windowByStructure.set(name, wid);

        const r = this.renderers.get(name);
        const wr = this.windows.get(wid);

        // Mirror бэкенда: первое attach делает окно видимым.
        if (wr && !wr.visible) {
            wr.setVisible(true);
        }

        if (r && wr) {
            const targetHost = wr.ensureStructureHost(name);
            // targetHost === r.container может быть при seek:
            // рендерер уже создан в ensureStructureHost через applySnapshot.
            // Вставлять элемент в самого себя нельзя.
            if (r.container !== targetHost && r.container.parentNode !== targetHost) {
                this.commitLayout(() => {
                    r.container.style.display = '';
                    targetHost.appendChild(r.container);
                    this._applyActiveTabClasses();
                }, [r]);
            } else {
                this._applyActiveTabClasses();
            }
        } else {
            this._applyActiveTabClasses();
        }

        this._updateWindowHeights();

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

        this._updateWindowHeights();
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

        if ('elementSize' in newSettings) {
            // Слайдер: глобальный размер + сброс localZoom всех структур.
            for (const r of this.renderers.values()) {
                r.localZoom = 1.0;
            }
            this._applyGlobalSize(newSettings.elementSize);
        }
        if ('speedFactor' in newSettings) {
            this.settings.speedFactor = newSettings.speedFactor;
            for (const r of this.renderers.values()) {
                r.settings.speedFactor = newSettings.speedFactor;
            }
        }
        if ('colors' in newSettings) {
            Object.assign(this.settings.colors, newSettings.colors);
            for (const r of this.renderers.values()) {
                Object.assign(r.settings.colors, newSettings.colors);
            }
        }
    }

    _applyGlobalSize(newSize) {
        this.settings.elementSize = newSize;
        for (const r of this.renderers.values()) {
            r.settings.elementSize = newSize;
            r.updateLayout();
            if (r._onSettingsChanged) r._onSettingsChanged();
        }
        // updateLayout внутри renderer'ов обновит contentHeight →
        // onLayoutChanged → _updateWindowHeights (с внутренним reclamp).
        // Вручную _updateWindowHeights не нужен.
        if (this.onSizeChanged) this.onSizeChanged(newSize);
    }

    async setActiveTab(tabId, skipAnimation = false) {
        this.activeTab = tabId;

        // Сброс глобального pan и всех localZoom при любой смене вкладки.
        this._sceneOffsetX = 0;
        this._sceneOffsetY = 0;
        this._sceneUserPanned = false;
        this._applySceneOffset();

        const isSingle = tabId !== 'all';
        for (const r of this.renderers.values()) {
            if (r.localZoom !== undefined) r.localZoom = 1.0;
            if (!isSingle) {
                r._userTransformed = false;
            }
            if (r.updateLayout) r.updateLayout();
            if (r.setZoomEnabled) r.setZoomEnabled(isSingle);
        }

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
        this._updateWindowHeights();

        if (isSingle) {
            this._reclampSceneOffset();
        }
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

    _updateWindowHeights() {
        if (this._updatingHeights) return;
        this._updatingHeights = true;
        try {
            const pending = [];
            const toRelayout = [];

            for (const [wid, wr] of this.windows) {
                // Оба режима (single / all) считают высоты одинаково:
                //   структура = её content-height,
                //   content   = сумма высот + gaps + padding.
                // В single окно центрируется через margin: auto 0
                // (если контент меньше вьюпорта) и уходит в pan
                // (если больше). В All работает нативный скролл по y.

                const heights = [];  // [{ name, h }]
                let totalH = 0;
                const renderersInWindow = [];
                for (const [name, r] of this.renderers) {
                    if (this.windowByStructure.get(name) === wid) {
                        const h = r.getContentHeight ? r.getContentHeight() : 0;
                        heights.push({ name, h });
                        totalH += h;
                        renderersInWindow.push(r);
                    }
                }

                if (heights.length === 0) {
                    // Нет структур в окне — сбрасываем установленные высоты.
                    if (wr._contentHeight !== null) {
                        pending.push({ wr, mode: 'clear' });
                    }
                    continue;
                }

                const gap = this.settings.structureGap;
                const gaps = Math.max(0, heights.length - 1) * gap;
                const contentH = totalH + gaps;
                const totalContent = wr.computeContentHeight(contentH);

                // Определяем, есть ли реальные изменения:
                //  1. wr.content.style.height != totalContent;
                //  2. у какой-то структуры host.style.height != её h.
                let changed = false;
                const curContent = parseInt(wr.content.style.height, 10) || 0;
                if (curContent !== totalContent) changed = true;
                if (!changed) {
                    for (const { name, h } of heights) {
                        const host = wr._structureHosts.get(name);
                        if (!host) continue;
                        const cur = parseInt(host.style.height, 10) || 0;
                        const want = Math.max(0, Math.ceil(h || 0));
                        if (cur !== want) { changed = true; break; }
                    }
                }

                if (changed) {
                    pending.push({
                        wr,
                        mode: 'apply',
                        contentHeight: totalContent,
                        heights,
                        renderers: renderersInWindow,
                    });
                }
            }

            if (pending.length === 0) return;  // нечего делать

            const gap = this.settings.structureGap;
            const mutator = () => {
                for (const p of pending) {
                    if (p.mode === 'clear') {
                        p.wr.clearContentHeight();
                        p.wr.clearStructureHeights();
                    } else {
                        const n = p.heights.length;
                        for (let i = 0; i < n; i++) {
                            const { name, h } = p.heights[i];
                            const mb = (i < n - 1) ? gap : 0;
                            p.wr.setStructureHeight(name, h, mb);
                        }
                        p.wr.setContentHeightDirect(p.contentHeight);
                        toRelayout.push(...p.renderers);
                    }
                }
            };
            this.commitLayout(mutator, toRelayout);

            if (!this._inCommitLayout && this.activeTab !== 'all') {
                this._reclampSceneOffset();
            }
        } finally {
            this._updatingHeights = false;
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

    _ensureNotificationContainer() {
        if (this._notificationContainer) return this._notificationContainer;
        const c = document.createElement('div');
        c.className = 'scene-notification-container';
        document.body.appendChild(c);
        this._notificationContainer = c;
        return c;
    }

    async _notify(text, positive) {
        if (!text) return;
        const container = this._ensureNotificationContainer();

        const n = document.createElement('div');
        n.className = 'scene-notification';

        if (positive === true) {
            n.textContent = '✓ ' + text;
            n.style.background = '#4CAF50';
        } else if (positive === false) {
            n.textContent = '✗ ' + text;
            n.style.background = '#f44336';
        } else {
            n.textContent = text;
            n.style.background = '#2196F3';
        }

        n.style.opacity = '1';
        container.appendChild(n);

        setTimeout(() => {
            n.style.opacity = '0';
            setTimeout(() => n.remove(), 300);
        }, 1500 / this.settings.speedFactor);
    }

    // ---------- pan + dblclick + zoom + touch ----------

    _bindSceneViewEvents() {
        this._onSceneMouseDownBound = this._onSceneMouseDown.bind(this);
        this._onSceneMouseMoveBound = this._onSceneMouseMove.bind(this);
        this._onSceneMouseUpBound = this._onSceneMouseUp.bind(this);
        this._onSceneDblClickBound = this._onSceneDblClick.bind(this);
        this._onSceneWheelBound = this._onSceneWheel.bind(this);
        this._onSceneTouchStartBound = this._onSceneTouchStart.bind(this);
        this._onSceneTouchMoveBound = this._onSceneTouchMove.bind(this);
        this._onSceneTouchEndBound = this._onSceneTouchEnd.bind(this);

        this.container.addEventListener('mousedown', this._onSceneMouseDownBound);
        this.container.addEventListener('dblclick', this._onSceneDblClickBound);
        this.container.addEventListener('wheel', this._onSceneWheelBound, { passive: false });
        this.container.addEventListener('touchstart', this._onSceneTouchStartBound, { passive: false });
        this.container.addEventListener('touchmove', this._onSceneTouchMoveBound, { passive: false });
        this.container.addEventListener('touchend', this._onSceneTouchEndBound);
        this.container.addEventListener('touchcancel', this._onSceneTouchEndBound);
    }

    _onSceneMouseDown(e) {
        if (this.activeTab === 'all') return;   // в All pan отключён
        if (e.button !== 0) return;

        // Alt+pan — делегируем в рендерер hovered-структуры.
        if (e.altKey) {
            const found = this._findHoveredStructure(e.clientX, e.clientY);
            if (found && found.renderer && found.renderer._onMouseDown) {
                found.renderer._onMouseDown(e);
            }
            return;
        }

        // Обычный глобальный pan.
        e.preventDefault();
        this._scenePanning = true;
        this._scenePanStart = {
            x: e.clientX, y: e.clientY,
            ox: this._sceneOffsetX, oy: this._sceneOffsetY,
            bounds: this._computeSceneContentBounds(),
        };
        this._inner.style.cursor = 'grabbing';
        this._inner.style.transition = 'none';
        document.addEventListener('mousemove', this._onSceneMouseMoveBound);
        document.addEventListener('mouseup', this._onSceneMouseUpBound);
    }

    _onSceneMouseMove(e) {
        if (!this._scenePanning) return;
        const dx = e.clientX - this._scenePanStart.x;
        const dy = e.clientY - this._scenePanStart.y;
        if (Math.hypot(dx, dy) > 5) this._sceneUserPanned = true;
        const bounds = this._scenePanStart.bounds;
        this._sceneOffsetX = this._clampSceneOffsetX(this._scenePanStart.ox + dx, bounds);
        this._sceneOffsetY = this._clampSceneOffsetY(this._scenePanStart.oy + dy, bounds);
        this._applySceneOffset();
    }

    _onSceneMouseUp(e) {
        if (!this._scenePanning) return;
        this._scenePanning = false;
        this._scenePanStart = null;
        this._inner.style.cursor = '';
        this._inner.style.transition = '';
        document.removeEventListener('mousemove', this._onSceneMouseMoveBound);
        document.removeEventListener('mouseup', this._onSceneMouseUpBound);
    }

    _onSceneDblClick(e) {
        if (this.activeTab === 'all') return;

        if (e.altKey) {
            const found = this._findHoveredStructure(e.clientX, e.clientY);
            if (found && found.renderer) {
                found.renderer._userTransformed = false;
                if (found.renderer.localZoom !== undefined) found.renderer.localZoom = 1.0;
                if (found.renderer.updateLayout) found.renderer.updateLayout();
            }
            return;
        }

        e.preventDefault();
        this._centerScene();
    }

    _centerScene() {
        if (this.activeTab === 'all') return;
        for (const r of this.renderers.values()) {
            if (r.localZoom !== undefined) r.localZoom = 1.0;
            r._userTransformed = false;
            if (r.updateLayout) r.updateLayout();
        }
        this._sceneUserPanned = false;
        this._sceneOffsetX = 0;
        this._sceneOffsetY = 0;
        this._applySceneOffset();
        void this._inner.getBoundingClientRect();   // reflow

        const bounds = this._computeSceneContentBounds();
        this._sceneOffsetX = this._clampSceneOffsetX(0, bounds);
        this._sceneOffsetY = this._clampSceneOffsetY(0, bounds);
        this._applySceneOffset();
    }

    _onSceneWheel(e) {
        if (this.activeTab === 'all') return;
        e.preventDefault();

        // Alt+wheel — локальный zoom структуры под курсором.
        if (e.altKey) {
            const found = this._findHoveredStructure(e.clientX, e.clientY);
            if (found && found.renderer && found.renderer._onWheel) {
                found.renderer._onWheel(e);
            }
            return;
        }

        // Обычный wheel — глобальный zoom (как слайдер, но без сброса
        // localZoom структур: пользователь сам решил, какие структуры
        // остаются увеличенными).
        const factor = e.ctrlKey ? 1.03 : 1.10;
        const mult = e.deltaY > 0 ? 1 / factor : factor;
        let newSize = this.settings.elementSize * mult;
        newSize = Math.max(15, Math.min(250, newSize));
        if (Math.abs(newSize - this.settings.elementSize) < 0.01) return;
        this._applyGlobalSize(newSize);
    }

    _onSceneTouchStart(e) {
        if (this.activeTab === 'all') return;
        if (e.touches.length === 1) {
            e.preventDefault();
            this._sceneTouchPan = {
                startX: e.touches[0].clientX,
                startY: e.touches[0].clientY,
                startOX: this._sceneOffsetX,
                startOY: this._sceneOffsetY,
                bounds: this._computeSceneContentBounds(),
            };
            this._sceneTouchMoved = false;
            this._scenePinch = null;
        } else if (e.touches.length === 2) {
            e.preventDefault();
            this._sceneTouchPan = null;
            // Pinch — точно не тап, не обрабатываем как двойное касание.
            this._sceneTouchMoved = true;
            const t1 = e.touches[0], t2 = e.touches[1];
            this._scenePinch = {
                startDist: Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY),
                startSize: this.settings.elementSize,
            };
        }
    }

    _onSceneTouchMove(e) {
        if (this.activeTab === 'all') return;

        if (this._scenePinch && e.touches.length === 2) {
            e.preventDefault();
            const t1 = e.touches[0], t2 = e.touches[1];
            const dist = Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);
            const ratio = dist / this._scenePinch.startDist;
            let newSize = this._scenePinch.startSize * ratio;
            newSize = Math.max(15, Math.min(250, newSize));
            if (Math.abs(newSize - this.settings.elementSize) < 0.01) return;
            this._applyGlobalSize(newSize);
        } else if (this._sceneTouchPan && e.touches.length === 1) {
            e.preventDefault();
            const t = e.touches[0];
            const dx = t.clientX - this._sceneTouchPan.startX;
            const dy = t.clientY - this._sceneTouchPan.startY;
            if (Math.hypot(dx, dy) > 5) {
                this._sceneTouchMoved = true;
                this._sceneUserPanned = true;
            }
            this._sceneOffsetX = this._clampSceneOffsetX(this._sceneTouchPan.startOX + dx, this._sceneTouchPan.bounds);
            this._sceneOffsetY = this._clampSceneOffsetY(this._sceneTouchPan.startOY + dy, this._sceneTouchPan.bounds);
            this._applySceneOffset();
        }
    }

    _onSceneTouchEnd(e) {
        if (!this._sceneTouchPan && !this._scenePinch) return;

        if (e.touches.length === 0) {
            const moved = this._sceneTouchMoved;
            const wasPinch = !!this._scenePinch;

            this._sceneTouchPan = null;
            this._scenePinch = null;
            this._sceneTouchMoved = false;

            // НЕ recenter на каждом отпускании — иначе pan «не работает».
            // Только детектор двойного тапа (два тапа < 300ms без движения
            // и без pinch) → центр.
            if (!moved && !wasPinch) {
                const now = Date.now();
                if (this._sceneLastTapTime && now - this._sceneLastTapTime < 300) {
                    this._sceneLastTapTime = 0;
                    this._centerScene();
                } else {
                    this._sceneLastTapTime = now;
                }
            }
        } else if (e.touches.length === 1) {
            // Остался один палец после pinch → переход в pan.
            this._scenePinch = null;
            this._sceneTouchMoved = true;   // завершение pinch — не тап
            this._sceneTouchPan = {
                startX: e.touches[0].clientX,
                startY: e.touches[0].clientY,
                startOX: this._sceneOffsetX,
                startOY: this._sceneOffsetY,
                bounds: this._computeSceneContentBounds(),
            };
        }
    }

    _applySceneOffset() {
        this._inner.style.transform =
            `translate(${this._sceneOffsetX}px, ${this._sceneOffsetY}px)`;
    }

    _reclampSceneOffset() {
        if (this.activeTab === 'all') return;
        if (!this._inner) return;

        let baseOffsetX = this._sceneOffsetX;
        let baseOffsetY = this._sceneOffsetY;

        // Сброс к центру только если пользователь ни разу не панорамировал
        // сцену и ни одна структура не трансформирована. Иначе — сохранить
        // позицию (только clamp в bounds), чтобы pan не терялся при
        // росте контента / смене вкладки / reflow.
        let shouldCenter = false;
        if (!this._sceneUserPanned) {
            let allUntransformed = true;
            for (const r of this.renderers.values()) {
                if (r._userTransformed) { allUntransformed = false; break; }
            }
            if (allUntransformed) shouldCenter = true;
        }
        if (shouldCenter) {
            baseOffsetX = 0;
            baseOffsetY = 0;
        }

        // bounds считаем от «чистого» _inner (без текущего translate):
        // временно снимаем transform, считаем, восстанавливаем.
        const prevTransform = this._inner.style.transform;
        this._inner.style.transform = '';
        void this._inner.getBoundingClientRect();   // reflow
        const bounds = this._computeSceneContentBounds();
        this._inner.style.transform = prevTransform;

        this._sceneOffsetX = this._clampSceneOffsetX(baseOffsetX, bounds);
        this._sceneOffsetY = this._clampSceneOffsetY(baseOffsetY, bounds);
        this._applySceneOffset();
    }

    _clampSceneOffsetX(offset, bounds) {
        if (!bounds) return 0;
        const contentW = bounds.maxX - bounds.minX;
        if (contentW <= 0) return 0;   // пустая сцена
        const cw = this.container.clientWidth;
        if (contentW <= cw) {
            return (cw - contentW) / 2 - bounds.minX;
        }
        return Math.min(Math.max(offset, cw - bounds.maxX), -bounds.minX);
    }

    _clampSceneOffsetY(offset, bounds) {
        if (!bounds) return 0;
        const contentH = bounds.maxY - bounds.minY;
        if (contentH <= 0) return 0;   // пустая сцена
        const ch = this.container.clientHeight;
        if (contentH <= ch) {
            return (ch - contentH) / 2 - bounds.minY;
        }
        return Math.min(Math.max(offset, ch - bounds.maxY), -bounds.minY);
    }

    _findHoveredStructure(x, y) {
        const el = document.elementFromPoint(x, y);
        if (!el || !el.closest) return null;
        const struct = el.closest('.scene-window-structure');
        if (!struct) return null;
        const name = struct.dataset.structureName;
        const renderer = this.renderers.get(name);
        return { name, renderer, host: struct };
    }

    _computeSceneContentBounds() {
        // Координаты внутри .scene-inner (без учёта transform translate).
        // getBoundingClientRect даёт уже трансформированные координаты,
        // но РАЗНИЦА r.left - innerRect.left автоматически убирает
        // текущий translate, потому что оба содержат его одинаково.
        //
        // ВАЖНО: элементы с display: none возвращают rect {0,0,0,0}
        // (координаты viewport). Их нельзя учитывать — иначе получаем
        // «фантомные» координаты, зависящие от позиции viewport, и
        // bounds накапливает сдвиг при каждом пересчёте.
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        const innerRect = this._inner.getBoundingClientRect();

        // Окна (header + content)
        for (const wr of this.windows.values()) {
            if (!wr.visible) continue;
            const r = wr.element.getBoundingClientRect();
            if (r.width === 0 && r.height === 0) continue;  // display: none
            const x1 = r.left - innerRect.left;
            const y1 = r.top - innerRect.top;
            const x2 = x1 + r.width;
            const y2 = y1 + r.height;
            if (x1 < minX) minX = x1;
            if (y1 < minY) minY = y1;
            if (x2 > maxX) maxX = x2;
            if (y2 > maxY) maxY = y2;
        }

        // Элементы структур (могут вылезать за контейнер структуры)
        for (const r of this.renderers.values()) {
            for (const el of r.elements.values()) {
                const er = el.getBoundingClientRect();
                if (er.width === 0 && er.height === 0) continue;  // display: none
                const x1 = er.left - innerRect.left;
                const y1 = er.top - innerRect.top;
                const x2 = x1 + er.width;
                const y2 = y1 + er.height;
                if (x1 < minX) minX = x1;
                if (y1 < minY) minY = y1;
                if (x2 > maxX) maxX = x2;
                if (y2 > maxY) maxY = y2;
            }
        }

        if (minX === Infinity) return { minX: 0, minY: 0, maxX: 0, maxY: 0 };
        return { minX, minY, maxX, maxY };
    }

    _bindInfoEvents() {
        document.addEventListener('keydown', (e) => {
            if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
            if (e.key === 'i' || e.key === 'I' || e.code === 'KeyI') {
                if (!this._infoMode) {
                    this._infoMode = true;
                    if (this._lastMouse) this._refreshTooltipFromPoint(this._lastMouse);
                }
            }
        });
        document.addEventListener('keyup', (e) => {
            if (e.key === 'i' || e.key === 'I' || e.code === 'KeyI') {
                this._infoMode = false;
                this._hideTooltip();
            }
        });
        // При потере фокуса окна keyup может не прийти — сбрасываем.
        window.addEventListener('blur', () => {
            this._infoMode = false;
            this._hideTooltip();
        });

        this.container.addEventListener('mousemove', (e) => {
            this._lastMouse = { x: e.clientX, y: e.clientY, target: e.target };
            if (this._infoMode) this._refreshTooltipFromPoint(this._lastMouse);
        });
        this.container.addEventListener('mouseleave', () => {
            this._hideTooltip();
        });
    }

    _refreshTooltipFromPoint({ x, y, target }) {
        // target мог устареть (mousemove уже случился на другом). Используем
        // document.elementFromPoint — самый надёжный способ найти актуальный
        // элемент под курсором.
        const el = document.elementFromPoint(x, y);
        if (!el) { this._hideTooltip(); return; }
        const visualEl = el.closest && el.closest('.visualization-element');
        if (!visualEl) { this._hideTooltip(); return; }
        const struct = visualEl.closest('.scene-window-structure');
        const name = struct && struct.dataset.structureName;
        if (!name) { this._hideTooltip(); return; }
        this._showTooltip(name, x, y);
    }

    _showTooltip(text, x, y) {
        if (!this._tooltip) {
            this._tooltip = document.createElement('div');
            this._tooltip.className = 'scene-info-tooltip';
            document.body.appendChild(this._tooltip);
        }
        this._tooltip.textContent = text;
        // Небольшой отступ от курсора; при выходе за правый край — сдвиг влево.
        const pad = 14;
        this._tooltip.style.display = 'block';
        const rect = this._tooltip.getBoundingClientRect();
        let left = x + pad;
        let top = y + pad;
        if (left + rect.width > window.innerWidth - 8) left = x - rect.width - pad;
        if (top + rect.height > window.innerHeight - 8) top = y - rect.height - pad;
        this._tooltip.style.left = left + 'px';
        this._tooltip.style.top = top + 'px';
    }

    _hideTooltip() {
        if (this._tooltip) this._tooltip.style.display = 'none';
    }
}
