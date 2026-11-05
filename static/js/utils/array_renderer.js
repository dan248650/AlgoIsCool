import { BaseRenderer } from './base_renderer.js';

export class ArrayRenderer extends BaseRenderer {
    // --- Специфические методы для массивов ---
    async _handleSpecificCommand(command, skipAnimation) {
        switch (command.component) {
            case 'create_elements':
                await this.createElements(command.params.array, skipAnimation);
                break;
            case 'update_element':
                await this.updateElement(command.params, skipAnimation);
                break;
            case 'create_element':
                await this.createElement(command.params, skipAnimation);
                break;
            case 'remove_element':
                await this.removeElement(command.params, skipAnimation);
                break;
            case 'replace_elements':
                await this.applySnapshot(command.params, skipAnimation);
                break;
            case 'highlight':
                await this.highlight(command.params, skipAnimation);
                break;
            case 'unhighlight':
                await this.unhighlight(command.params, skipAnimation);
                break;
            case 'set_opacity':
                await this.setOpacity(command.params, skipAnimation);
                break;
            case 'swap_elements':
                await this.swapElements(command.params, skipAnimation);
                break;
            default:
                throw new Error(`Unknown array component: ${command.component}`);
        }
    }

    clear() {
        super.clear();
        this._pendingReveal = false;
    }

    _onSettingsChanged() {
        for (const element of this.elements.values()) {
            element.style.width = `${this.settings.elementSize}px`;
            element.style.height = `${this.settings.elementSize}px`;
            element.style.fontSize = `${Math.max(12, this.settings.elementSize / 3)}px`;
            const valueDiv = element.querySelector('.value');
            if (valueDiv) valueDiv.style.fontSize = `${Math.max(12, this.settings.elementSize / 3)}px`;
            const indexDiv = element.querySelector('.index');
            if (indexDiv) indexDiv.style.fontSize = `${Math.max(10, this.settings.elementSize / 4)}px`;
        }
    }

    // --- Применение снапшота ---

    applySnapshot(snapshot, skipAnimation = false) {
        const anim = snapshot?.animation;
        if (skipAnimation || !anim || !anim.type) {
            this.applySnapshotImmediate(snapshot);
            return;
        }
        if (anim.type === 'insert') return this._animateInsert(snapshot, anim.at);
        if (anim.type === 'remove') return this._animateRemove(snapshot, anim.at);
        this.applySnapshotImmediate(snapshot);
    }

    applySnapshotImmediate(snapshot) {
        this.clear();
        if (!snapshot || !snapshot.elements) return;
        for (const elem of snapshot.elements) {
            const element = this._createDomElement(elem, elem.x, elem.y);
            this.container.appendChild(element);
            this.elements.set(elem.id, element);
        }
        this.updateLayout();
    }

    // --- FLIP-анимации ---

    async _animateInsert(snapshot, at) {
        const dur = 300 / this.settings.speedFactor;

        // Снимаем старые визуальные позиции по индексам
        const oldRects = new Map();
        for (const [id, el] of this.elements) {
            const idx = parseInt(id.split('_')[1], 10);
            oldRects.set(idx, el.getBoundingClientRect());
        }

        // Жёстко перестраиваем — новые id и позиции
        this.applySnapshotImmediate(snapshot);

        // FLIP: смещаем каждый новый элемент обратно к старой визуальной позиции
        const anims = [];
        for (const [id, el] of this.elements) {
            const newIdx = parseInt(id.split('_')[1], 10);
            let oldIdx = null;
            if (newIdx < at) oldIdx = newIdx;
            else if (newIdx > at) oldIdx = newIdx - 1;

            if (oldIdx !== null) {
                const oldRect = oldRects.get(oldIdx);
                if (oldRect) {
                    const newRect = el.getBoundingClientRect();
                    const dx = oldRect.left - newRect.left;
                    const dy = oldRect.top - newRect.top;
                    if (Math.abs(dx) > 0.5 || Math.abs(dy) > 0.5) {
                        el.style.transition = 'none';
                        el.style.transform = `translate(${dx}px, ${dy}px)`;
                        anims.push(el);
                    }
                }
            }
        }
        void this.container.offsetHeight;

        for (const el of anims) {
            el.style.transition = `transform ${dur}ms cubic-bezier(0.4, 0, 0.2, 1)`;
            el.style.transform = '';
        }

        // Новый элемент — scale от 0
        const newEl = this.elements.get(`elem_${at}`);
        if (newEl) {
            newEl.style.transform = 'scale(0)';
            newEl.style.opacity = '0';
            void newEl.offsetHeight;
            newEl.style.transition = `transform ${dur}ms ease, opacity ${dur}ms ease`;
            newEl.style.transform = 'scale(1)';
            newEl.style.opacity = '1';
        }

        await this.sleep(dur);

        // Сбрасываем transition у ВСЕХ элементов, а не только у двигавшихся:
        // элементы до точки вставки не в anims, но у них остался
        // 'none' из _createDomElement. Без сброса они не будут
        // анимироваться при следующей операции.
        for (const el of this.elements.values()) {
            el.style.transition = '';
        }
        if (newEl) {
            newEl.style.transform = '';
            newEl.style.opacity = '';
        }
    }

    async _animateRemove(snapshot, at) {
        const dur = 300 / this.settings.speedFactor;

        // Снимаем визуальные позиции до rebuild
        const oldRects = new Map();
        for (const [id, el] of this.elements) {
            const idx = parseInt(id.split('_')[1], 10);
            oldRects.set(idx, el.getBoundingClientRect());
        }

        // Клонируем удаляемый элемент — чтобы он плавно погас, пока
        // остальные едут на новое место. Клон на body, чтобы пережил
        // очистку контейнера в applySnapshotImmediate.
        const removedEl = this.elements.get(`elem_${at}`);
        let clone = null;
        if (removedEl) {
            const rect = removedEl.getBoundingClientRect();
            clone = removedEl.cloneNode(true);
            clone.style.position = 'fixed';
            clone.style.left = `${rect.left}px`;
            clone.style.top = `${rect.top}px`;
            clone.style.width = `${rect.width}px`;
            clone.style.height = `${rect.height}px`;
            clone.style.pointerEvents = 'none';
            clone.style.zIndex = '1000';
            clone.style.transition = `opacity ${dur}ms ease, transform ${dur}ms ease`;
            document.body.appendChild(clone);
        }

        // Жёсткий rebuild
        this.applySnapshotImmediate(snapshot);

        // FLIP для оставшихся
        const anims = [];
        for (const [id, el] of this.elements) {
            const newIdx = parseInt(id.split('_')[1], 10);
            const oldIdx = newIdx >= at ? newIdx + 1 : newIdx;
            const oldRect = oldRects.get(oldIdx);
            if (oldRect) {
                const newRect = el.getBoundingClientRect();
                const dx = oldRect.left - newRect.left;
                const dy = oldRect.top - newRect.top;
                if (Math.abs(dx) > 0.5 || Math.abs(dy) > 0.5) {
                    el.style.transition = 'none';
                    el.style.transform = `translate(${dx}px, ${dy}px)`;
                    anims.push(el);
                }
            }
        }
        void this.container.offsetHeight;

        for (const el of anims) {
            el.style.transition = `transform ${dur}ms cubic-bezier(0.4, 0, 0.2, 1)`;
            el.style.transform = '';
        }

        if (clone) {
            void clone.offsetHeight;
            clone.style.opacity = '0';
            clone.style.transform = 'scale(0.6)';
        }

        await this.sleep(dur);

        // То же: сбрасываем transition у всех, включая элементы
        // до точки удаления, которые не попали в anims.
        for (const el of this.elements.values()) {
            el.style.transition = '';
        }
        if (clone) clone.remove();
    }

    async updateElement(params, skipAnimation = false) {
        const { id, value } = params;
        const el = this.elements.get(id);
        if (!el) return;
        const valueDiv = el.querySelector('.value');
        if (!valueDiv) return;
        valueDiv.textContent = value;
        if (!skipAnimation) {
            valueDiv.style.transition = 'background 0.3s ease';
            valueDiv.style.background = 'rgba(255, 255, 255, 0.6)';
            await this.sleep(300 / this.settings.speedFactor);
            valueDiv.style.background = '';
            valueDiv.style.transition = '';
        }
    }

    _createDomElement(elemData, baseX, baseY) {
        const element = document.createElement('div');
        element.id = elemData.id;
        element.className = 'visualization-element';
        element.style.position = 'absolute';
        element.style.width = `${this.settings.elementSize}px`;
        element.style.height = `${this.settings.elementSize}px`;
        element.style.borderRadius = '8px';
        element.style.backgroundColor = 'rgba(224, 224, 224, 0.5)';
        element.style.display = 'flex';
        element.style.flexDirection = 'column';
        element.style.alignItems = 'center';
        element.style.justifyContent = 'center';
        element.style.fontSize = `${Math.max(12, this.settings.elementSize / 3)}px`;
        element.style.fontWeight = 'bold';
        element.style.color = '#333';
        element.style.transition = 'none';
        element.style.boxShadow = elemData.color && elemData.color !== 'None'
            ? `0 0 12px 4px ${elemData.color}, 0 0 24px 8px ${elemData.color}`
            : '0 2px 8px rgba(0,0,0,0.1)';
        element.dataset.defaultBg = 'rgba(224, 224, 224, 0.5)';
        element.dataset.defaultBs = '0 2px 8px rgba(0,0,0,0.1)';
        element.dataset.baseX = baseX;
        element.dataset.baseY = baseY;
        element.innerHTML = `
            <div class="value">${elemData.value}</div>
            ${this.settings.showIndices ? `<div class="index">${element.id.split('_')[1]}</div>` : ''}
        `;
        const indexDiv = element.querySelector('.index');
        if (indexDiv) indexDiv.style.fontSize = `${Math.max(10, this.settings.elementSize / 4)}px`;
        return element;
    }

    // --- Базовые команды массива ---
    // --- Создание массива. skipAnimation=true → разом; иначе → раскрытие ---
    async createElements(array, skipAnimation = false) {
        this.clear();
        if (!array || array.length === 0) return;

        // Создаём все элементы сразу, но в скрытом виде (scale 0).
        // Показывать будем либо тут же поэтапно, либо позже, когда
        // структура впервые окажется в видимом контейнере.
        const created = [];
        for (let index = 0; index < array.length; index++) {
            const baseX = index * (this.baseElementSize + this.settings.spacing);
            const elem = this._createDomElement(
                { id: `elem_${index}`, value: array[index], color: null },
                baseX,
                50,
            );
            elem.style.transition = 'none';
            elem.style.transform = 'scale(0)';
            this.container.appendChild(elem);
            this.elements.set(`elem_${index}`, elem);
            created.push(elem);
        }
        this.updateLayout();

        const isHidden = this.container.offsetWidth === 0;

        if (skipAnimation) {
            this._revealAllInstantly(created);
            return;
        }

        if (isHidden) {
            // Структура создана, но ещё не привязана к видимому окну.
            // Раскроем при первом onBecameVisible.
            this._pendingReveal = true;
            return;
        }

        await this._revealSequentially(created);
    }

    async createElement(params, skipAnimation = false) {
        const { id, value, x, y } = params;
        const el = this._createDomElement({ id, value, color: null }, x, y);
        this.container.appendChild(el);
        this.elements.set(id, el);

        if (skipAnimation) {
            this.updateLayout();
            el.style.transition = '';
            return;
        }

        // Мгновенно поставить в масштаб 0 и прозрачность 0 — до применения layout.
        el.style.transform = 'scale(0)';
        el.style.opacity = '0';
        this.updateLayout();
        void this.container.offsetHeight;  // commit начального состояния

        el.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
        el.style.transform = 'scale(1)';
        el.style.opacity = '1';
        await this.sleep(300 / this.settings.speedFactor);
        el.style.transition = '';
        el.style.transform = '';
        el.style.opacity = '';
    }

    async removeElement(params, skipAnimation = false) {
        const { id } = params;
        const el = this.elements.get(id);
        if (!el) return;

        if (skipAnimation) {
            el.remove();
            this.elements.delete(id);
            this.updateLayout();
            return;
        }

        const dur = 300 / this.settings.speedFactor;

        // Фейд удаляемого элемента — параллельно со сдвигом остальных.
        el.style.transition = `opacity ${dur}ms ease, transform ${dur}ms ease`;
        el.style.opacity = '0';
        el.style.transform = 'scale(0.6)';

        this.elements.delete(id);
        this.updateLayout();

        await this.sleep(dur);
        el.remove();
    }

    _revealAllInstantly(elements) {
        for (const el of elements) {
            el.style.transition = 'none';
            el.style.transform = 'scale(1)';
        }
        void this.container.offsetHeight;   // применить без анимации
        for (const el of elements) {
            el.style.transition = '';
            el.style.transform = '';
        }
    }

    async _revealSequentially(elements) {
        const n = elements.length;
        if (n === 0) return;

        const speedFactor = this.settings.speedFactor || 1;
        const baseStep = Math.min(150, 50 / speedFactor);       // как в legacy
        const maxTotal = 3000 / speedFactor;     // защита от длинных массивов
        const step = Math.max(1, Math.min(baseStep, maxTotal / n));

        for (const el of elements) {
            el.style.transition = 'transform 0.3s ease-in-out';
        }
        void this.container.offsetHeight;        // transition должен «зацепиться»

        for (let i = 0; i < n; i++) {
            elements[i].style.transform = 'scale(1)';
            await this.sleep(step);
        }

        // После раскрытия даём обычный transition из CSS — чтобы future
        // shift/updateLayout могли анимироваться, если понадобится.
        for (const el of elements) {
            el.style.transition = '';
            el.style.transform = '';
        }
    }

    async onBecameVisible(skipAnimation = false) {
        if (!this._pendingReveal) return;
        this._pendingReveal = false;

        const elements = Array.from(this.elements.values());
        if (elements.length === 0) return;

        if (skipAnimation) {
            this._revealAllInstantly(elements);
        } else {
            await this._revealSequentially(elements);
        }
    }

    cancelPendingReveal() {
        if (!this._pendingReveal) return;
        this._pendingReveal = false;

        // Раскрытие отменяется, но его нужно довести до конца —
        // иначе элементы останутся в scale(0) и структура не покажется.
        const elements = Array.from(this.elements.values());
        if (elements.length === 0) return;
        this._revealAllInstantly(elements);
    }

    async moveStraight(params, skipAnimation = false) {
        const { element_ids, to_x, to_y, duration = 500, easing = 'ease-in-out' } = params;
        if (skipAnimation) {
            for (const id of element_ids) {
                const element = this.elements.get(id);
                if (element) {
                    element.dataset.baseX = to_x;
                    element.dataset.baseY = to_y;
                }
            }
            this.updateLayout();
            return;
        }
        const actualDuration = duration / this.settings.speedFactor;
        for (const id of element_ids) {
            const element = this.elements.get(id);
            if (!element) continue;
            const currentLeft = parseFloat(element.style.left);
            const currentTop = parseFloat(element.style.top);
            const targetScreenX = to_x * this.scale + this.offsetX;
            const targetScreenY = to_y * this.scale + this.offsetY;
            element.style.transition = `transform ${actualDuration}ms ${easing}`;
            element.style.transform = `translate(${targetScreenX - currentLeft}px, ${targetScreenY - currentTop}px)`;
        }
        await this.sleep(actualDuration);
        for (const id of element_ids) {
            const element = this.elements.get(id);
            if (!element) continue;
            element.style.transform = '';
            element.style.transition = '';
            element.dataset.baseX = to_x;
            element.dataset.baseY = to_y;
        }
        this.updateLayout();
    }

    async swapElements(params, skipAnimation = false) {
        const { element1_id, element2_id, duration = 800 } = params;
        const elem1 = this.elements.get(element1_id);
        const elem2 = this.elements.get(element2_id);
        if (!elem1 || !elem2) return;

        if (skipAnimation) {
            const parent = this.container;
            const nextSibling = elem1.nextSibling === elem2 ? elem1 : elem2.nextSibling;
            parent.insertBefore(elem2, elem1);
            parent.insertBefore(elem1, nextSibling);

            const oldId1 = elem1.id;
            const oldId2 = elem2.id;
            this.elements.delete(oldId1);
            this.elements.delete(oldId2);
            elem1.id = oldId2;
            elem2.id = oldId1;
            this.elements.set(elem1.id, elem1);
            this.elements.set(elem2.id, elem2);

            const baseX1 = parseFloat(elem1.dataset.baseX);
            const baseY1 = parseFloat(elem1.dataset.baseY);
            const baseX2 = parseFloat(elem2.dataset.baseX);
            const baseY2 = parseFloat(elem2.dataset.baseY);
            elem1.dataset.baseX = baseX2;
            elem1.dataset.baseY = baseY2;
            elem2.dataset.baseX = baseX1;
            elem2.dataset.baseY = baseY1;

            const color1 = elem1.style.backgroundColor;
            const color2 = elem2.style.backgroundColor;
            elem1.style.backgroundColor = color2;
            elem2.style.backgroundColor = color1;

            if (this.settings.showIndices) {
                const idx1 = elem1.querySelector('.index');
                const idx2 = elem2.querySelector('.index');
                if (idx1) idx1.textContent = elem1.id.split('_')[1];
                if (idx2) idx2.textContent = elem2.id.split('_')[1];
            }
            this.updateLayout();
            return;
        }

        // Анимированная версия
        const rect1 = elem1.getBoundingClientRect();
        const rect2 = elem2.getBoundingClientRect();
        const containerRect = this.container.getBoundingClientRect();
        const pos1 = { x: rect1.left - containerRect.left, y: rect1.top - containerRect.top };
        const pos2 = { x: rect2.left - containerRect.left, y: rect2.top - containerRect.top };
        const actualDuration = duration / this.settings.speedFactor;

        elem1.style.transition = `transform ${actualDuration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
        elem2.style.transition = `transform ${actualDuration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
        elem1.style.transform = `translate(${pos2.x - pos1.x}px, ${pos2.y - pos1.y}px)`;
        elem2.style.transform = `translate(${pos1.x - pos2.x}px, ${pos1.y - pos2.y}px)`;
        await this.sleep(actualDuration);

        const parent = this.container;
        const nextSibling = elem1.nextSibling === elem2 ? elem1 : elem2.nextSibling;
        parent.insertBefore(elem2, elem1);
        parent.insertBefore(elem1, nextSibling);

        const oldId1 = elem1.id;
        const oldId2 = elem2.id;
        this.elements.delete(oldId1);
        this.elements.delete(oldId2);
        elem1.id = oldId2;
        elem2.id = oldId1;
        this.elements.set(elem1.id, elem1);
        this.elements.set(elem2.id, elem2);

        const baseX1 = parseFloat(elem1.dataset.baseX);
        const baseY1 = parseFloat(elem1.dataset.baseY);
        const baseX2 = parseFloat(elem2.dataset.baseX);
        const baseY2 = parseFloat(elem2.dataset.baseY);
        elem1.dataset.baseX = baseX2;
        elem1.dataset.baseY = baseY2;
        elem2.dataset.baseX = baseX1;
        elem2.dataset.baseY = baseY1;

        const newLeft1 = parseFloat(elem1.dataset.baseX) * this.scale + this.offsetX;
        const newTop1 = parseFloat(elem1.dataset.baseY) * this.scale + this.offsetY;
        const newLeft2 = parseFloat(elem2.dataset.baseX) * this.scale + this.offsetX;
        const newTop2 = parseFloat(elem2.dataset.baseY) * this.scale + this.offsetY;

        elem1.style.transition = 'none';
        elem2.style.transition = 'none';
        elem1.style.left = `${newLeft1}px`;
        elem1.style.top = `${newTop1}px`;
        elem2.style.left = `${newLeft2}px`;
        elem2.style.top = `${newTop2}px`;

        elem1.style.transform = '';
        elem2.style.transform = '';
        void elem1.offsetHeight;
        elem1.style.transition = '';
        elem2.style.transition = '';

        if (this.settings.showIndices) {
            const idx1 = elem1.querySelector('.index');
            const idx2 = elem2.querySelector('.index');
            if (idx1) idx1.textContent = elem1.id.split('_')[1];
            if (idx2) idx2.textContent = elem2.id.split('_')[1];
        }
    }

    async highlight(params, skipAnimation = false) {
        const { element_ids, color, duration = 600, opacity = 1 } = params;
        const actualDuration = duration / this.settings.speedFactor;
        for (const id of element_ids) {
            const element = this.elements.get(id);
            if (!element) continue;
            element.style.transition = `box-shadow ${actualDuration}ms ease, opacity ${actualDuration}ms ease`;
            element.style.opacity = opacity;
            element.style.boxShadow = `0 0 12px 4px ${color}, 0 0 24px 8px ${color}`;
        }
        if (!skipAnimation) {
            await this.sleep(actualDuration);
        }
        for (const id of element_ids) {
            const element = this.elements.get(id);
            if (!element) continue;
            element.style.transition = '';
        }
    }

    async unhighlight(params, skipAnimation = false) {
        const { element_ids, duration = 400 } = params;
        const actualDuration = duration / this.settings.speedFactor;
        for (const id of element_ids) {
            const element = this.elements.get(id);
            if (!element) continue;
            element.style.transition = `box-shadow ${actualDuration}ms ease, opacity ${actualDuration}ms ease`;
            const defaultBs = element.dataset.defaultBs || '';
            element.style.opacity = 1;
            element.style.boxShadow = defaultBs;
        }
        if (!skipAnimation) {
            await this.sleep(actualDuration);
        }
        for (const id of element_ids) {
            const element = this.elements.get(id);
            if (!element) continue;
            element.style.transition = '';
        }
    }

    async setOpacity(params, skipAnimation = false) {
        const { element_ids, opacity, duration = 300 } = params;
        const actualDuration = duration / this.settings.speedFactor;
        for (const id of element_ids) {
            const element = this.elements.get(id);
            if (!element) continue;
            element.style.transition = `opacity ${actualDuration}ms ease`;
            element.style.opacity = opacity;
        }
        if (!skipAnimation) {
            await this.sleep(actualDuration);
        }
        for (const id of element_ids) {
            const element = this.elements.get(id);
            if (!element) continue;
            element.style.transition = '';
        }
    }
}
