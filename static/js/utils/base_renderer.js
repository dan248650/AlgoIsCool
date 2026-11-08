export class BaseRenderer {
    constructor(container) {
        this.container = (typeof container === 'string') ? document.getElementById(container) : container;
        this.elements = new Map();                 // id → DOM element (для массивов)
        this.settings = {
            speedFactor: 1.0,
            elementSize: 40,
            spacing: 10,
            colors: {
                comparing: '#9400D3',
                swapping: '#FF6B6B',
                sorted: '#4169E1',
                default: '#e0e0e0'
            },
            showIndices: true
        };
        this.baseElementSize = 40;   // все координаты от сервера рассчитаны для этого размера
        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;

        // Локальный множитель zoom (Alt+wheel). По умолчанию 1.
        // Итоговый размер = settings.elementSize * localZoom.
        this.localZoom = 1.0;

        // Трансформация вьюпорта (single-режим)
        this._userTransformed = false;
        this.zoomEnabled = true;
        this._dragging = false;
        this._dragStart = null;
        this._pinch = null;
        this._touchMoved = false;
        this._lastTapTime = 0;
        this.onSizeChanged = null;

        this._contentHeight = 0;
        this.onLayoutChanged = null;

        this.initContainer();

        // Bound-методы создаём в конструкторе, даже если слушатели
        // навешиваются не здесь (глобальные события — на SceneRenderer,
        // а эти методы вызываются им же при alt+pan / wheel).
        this._onWheelBound = this._onWheel.bind(this);
        this._onMouseDownBound = this._onMouseDown.bind(this);
        this._onMouseMoveBound = this._onMouseMove.bind(this);
        this._onMouseUpBound = this._onMouseUp.bind(this);
        this._onDblClickBound = this._onDblClick.bind(this);
        this._onTouchStartBound = this._onTouchStart.bind(this);
        this._onTouchMoveBound = this._onTouchMove.bind(this);
        this._onTouchEndBound = this._onTouchEnd.bind(this);

        // Наблюдаем за самим контейнером, а не за окном: размер
        // контейнера может меняться без события window.resize
        // (например, при анимации ширины сайдбара).
        if (typeof ResizeObserver !== 'undefined') {
            this._resizeObserver = new ResizeObserver(() => {
                this.updateLayout();
            });
            this._resizeObserver.observe(this.container);
        }

        // Резерв на случай отсутствия ResizeObserver в старых браузерах.
        window.addEventListener('resize', () => this.updateLayout());
    }

    initContainer() {
        if (!this.container.style.position) {
            this.container.style.position = 'relative';
        }
    }

    // === Единый метод пересчёта позиций (масштабирование + центрирование) ===
    updateLayout() {
        if (this.elements.size === 0) return;

        const containerRect = this.container.getBoundingClientRect();
        const targetSize = this._getEffectiveSize();
        this.scale = targetSize / this.baseElementSize;

        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        const items = [];

        for (const [id, el] of this.elements.entries()) {
            const baseX = parseFloat(el.dataset.baseX);
            const baseY = parseFloat(el.dataset.baseY);
            if (isNaN(baseX) || isNaN(baseY)) continue;
            const screenX = baseX * this.scale;
            const screenY = baseY * this.scale;
            items.push({ el, screenX, screenY });
            if (screenX < minX) minX = screenX;
            if (screenX > maxX) maxX = screenX;
            if (screenY < minY) minY = screenY;
            if (screenY > maxY) maxY = screenY;
        }
        if (items.length === 0) return;

        const groupWidth = maxX - minX + targetSize;
        const groupHeight = maxY - minY + targetSize;
        const cw = containerRect.width;
        const ch = containerRect.height;

        if (this._userTransformed) {
            // Пользователь сам управляет позицией — сохраняем offset,
            // но не даём сцене выйти за границы (или "улететь" из вида).
            this.offsetX = this._clampOffset(this.offsetX, minX, maxX, targetSize, cw);
            this.offsetY = this._clampOffset(this.offsetY, minY, maxY, targetSize, ch);
        } else {
            this.offsetX = (cw - groupWidth) / 2 - minX;
            this.offsetY = (ch - groupHeight) / 2 - minY;
        }

        for (const { el, screenX, screenY } of items) {
            el.style.left = `${screenX + this.offsetX}px`;
            el.style.top = `${screenY + this.offsetY}px`;
        }

        // Сохраняем высоту контента для авто-подстройки окна.
        const oldContentHeight = this._contentHeight;
        this._contentHeight = groupHeight;
        if (Math.abs(groupHeight - oldContentHeight) > 0.5) {
            if (this.onLayoutChanged) this.onLayoutChanged();
        }
    }

    _clampOffset(offset, minCoord, maxCoord, targetSize, containerSize) {
        // Положение группы в screen-координатах с учётом offset:
        //   left = minCoord + offset
        //   right = maxCoord + offset + targetSize
        const groupSize = (maxCoord - minCoord) + targetSize;

        if (groupSize <= containerSize) {
            // Группа меньше контейнера — clamp так, чтобы она не "улетала"
            // за границы, но могла быть в любом месте внутри.
            const minAllowed = -minCoord;
            const maxAllowed = containerSize - maxCoord - targetSize;
            if (minAllowed > maxAllowed) return offset; // группа шире — fallback
            return Math.min(Math.max(offset, minAllowed), maxAllowed);
        } else {
            // Группа больше контейнера — не показываем "воздух" по краям.
            const minAllowed = containerSize - maxCoord - targetSize;
            const maxAllowed = -minCoord;
            return Math.min(Math.max(offset, minAllowed), maxAllowed);
        }
    }

    getContentHeight() {
        return this._contentHeight || 0;
    }

    _getEffectiveSize() {
        return this.settings.elementSize * (this.localZoom || 1);
    }

    // Общий шаблон для сценариев, меняющих геометрию контейнера:
    //   1. отключаем transition;
    //   2. применяем мутатор (смена классов, перенос DOM, и т.п.);
    //   3. пересчитываем layout;
    //   4. синхронно снимаем no-transition.
    // Класс .no-transition объявлен в CSS глобально.
    commitLayout(mutator = null) {
        const root = this.container;
        if (!root) {
            if (typeof mutator === 'function') mutator();
            return;
        }

        root.classList.add('no-transition');
        void root.getBoundingClientRect();

        if (typeof mutator === 'function') mutator();

        void root.getBoundingClientRect();
        if (this.updateLayout) this.updateLayout();
        void root.getBoundingClientRect();

        root.classList.remove('no-transition');
    }

    // === Общие методы ===
    updateSettings(newSettings) {
        if (!newSettings) return;
        if ('elementSize' in newSettings) {
            this.settings.elementSize = newSettings.elementSize;
            this.updateLayout();
        }
        if ('speedFactor' in newSettings) {
            this.settings.speedFactor = newSettings.speedFactor;
        }
        if ('colors' in newSettings) {
            Object.assign(this.settings.colors, newSettings.colors);
        }
        this._onSettingsChanged();
    }

    _onSettingsChanged() {
        // переопределяется в наследниках
    }

    clear() {
        this.container.innerHTML = '';
        this.elements.clear();
        this._contentHeight = 0;
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // === Диспетчер команд ===
    async executeCommand(command, skipAnimation = false, commandIndex = null) {
        switch (command.component) {
            case 'update_settings':
                this.updateSettings(command.params);
                break;
            default:
                await this._handleSpecificCommand(command, skipAnimation);
        }
    }

    async onBecameVisible(skipAnimation = false) {
        // Переопределяется в наследниках, которым нужна реакция
        // на первое появление структуры в видимом контейнере.
    }

    cancelPendingReveal() {
        // Переопределяется в наследниках, у которых есть отложенное
        // раскрытие. По умолчанию — ничего.
    }

    _setTransition(el, base) {
        const suffix =
            ', left var(--lt-speed, 0.3s) ease-in-out' +
            ', top var(--lt-speed, 0.3s) ease-in-out' +
            ', width var(--lt-speed, 0.3s) ease-in-out' +
            ', height var(--lt-speed, 0.3s) ease-in-out' +
            ', font-size var(--lt-speed, 0.3s) ease-in-out';
        el.style.transition = base ? (base + suffix) : suffix.slice(2);
    }

    async _handleSpecificCommand(command, skipAnimation) {
        throw new Error(`Unhandled command: ${command.component}`);
    }

    // Абстрактные методы, которые должны быть переопределены
    applySnapshot(snapshot) {
        throw new Error('applySnapshot must be implemented in subclass');
    }

    // ---------- Трансформация вьюпорта (single-режим) ----------

    _onWheel(e) {
        if (!this.zoomEnabled) return;
        e.preventDefault();

        const rect = this.container.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        const oldSize = this._getEffectiveSize();
        const oldScale = oldSize / this.baseElementSize;
        const wx = (mx - this.offsetX - oldSize / 2) / oldScale;
        const wy = (my - this.offsetY - oldSize / 2) / oldScale;

        const factor = e.ctrlKey ? 1.03 : 1.10;
        const mult = e.deltaY > 0 ? 1 / factor : factor;
        let newSize = oldSize * mult;
        newSize = Math.max(15, Math.min(250, newSize));
        if (Math.abs(newSize - oldSize) < 0.01) return;

        // Локальный zoom: меняется только localZoom этой структуры.
        // settings.elementSize не трогаем — слайдер не двигается,
        // глобальный zoom не задет.
        this.localZoom = newSize / this.settings.elementSize;
        this._userTransformed = true;

        const newScale = newSize / this.baseElementSize;
        this.offsetX = mx - newSize / 2 - wx * newScale;
        this.offsetY = my - newSize / 2 - wy * newScale;

        this._onSettingsChanged();
        this.updateLayout();
    }

    _onMouseDown(e) {
        if (!this.zoomEnabled || e.button !== 0) return;
        e.preventDefault();
        this._dragging = true;
        this._dragStart = {
            x: e.clientX, y: e.clientY,
            offsetX: this.offsetX, offsetY: this.offsetY,
        };
        this.container.style.cursor = 'grabbing';
        this.container.style.setProperty('--lt-speed', '0.1s');
        document.addEventListener('mousemove', this._onMouseMoveBound);
        document.addEventListener('mouseup', this._onMouseUpBound);
    }

    _onMouseMove(e) {
        if (!this._dragging) return;
        const dx = e.clientX - this._dragStart.x;
        const dy = e.clientY - this._dragStart.y;
        this.offsetX = this._dragStart.offsetX + dx;
        this.offsetY = this._dragStart.offsetY + dy;
        this._userTransformed = true;
        this.updateLayout();
    }

    _onMouseUp(e) {
        if (!this._dragging) return;
        this._dragging = false;
        this.container.style.removeProperty('--lt-speed');
        this.container.style.cursor = this.zoomEnabled ? 'grab' : '';
        document.removeEventListener('mousemove', this._onMouseMoveBound);
        document.removeEventListener('mouseup', this._onMouseUpBound);
        this._onSettingsChanged();
        this.updateLayout();
    }

    _onTouchStart(e) {
        if (!this.zoomEnabled) return;
        if (e.touches.length === 1) {
            e.preventDefault();
            const t = e.touches[0];
            this._dragging = true;
            this._dragStart = {
                x: t.clientX, y: t.clientY,
                offsetX: this.offsetX, offsetY: this.offsetY,
            };
            this._touchMoved = false;
            this.container.style.setProperty('--lt-speed', '0.0s');
        } else if (e.touches.length === 2) {
            e.preventDefault();
            this._dragging = false;
            // Pinch — не тап.
            this._touchMoved = true;
            const t1 = e.touches[0], t2 = e.touches[1];
            const rect = this.container.getBoundingClientRect();
            this._pinch = {
                startDist: Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY),
                startSize: this.settings.elementSize,
                startOffsetX: this.offsetX,
                startOffsetY: this.offsetY,
                mx: (t1.clientX + t2.clientX) / 2 - rect.left,
                my: (t1.clientY + t2.clientY) / 2 - rect.top,
            };
            this.container.style.setProperty('--lt-speed', '0.0s');
        }
    }

    _onTouchMove(e) {
        if (!this.zoomEnabled) return;
        if (this._pinch && e.touches.length === 2) {
            e.preventDefault();
            const t1 = e.touches[0], t2 = e.touches[1];
            const dist = Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);
            const ratio = dist / this._pinch.startDist;

            const oldSize = this._pinch.startSize;
            const oldScale = oldSize / this.baseElementSize;
            const wx = (this._pinch.mx - this._pinch.startOffsetX - oldSize / 2) / oldScale;
            const wy = (this._pinch.my - this._pinch.startOffsetY - oldSize / 2) / oldScale;

            let newSize = oldSize * ratio;
            newSize = Math.max(15, Math.min(250, newSize));

            this.settings.elementSize = newSize;
            this._userTransformed = true;

            const newScale = newSize / this.baseElementSize;
            this.offsetX = this._pinch.mx - newSize / 2 - wx * newScale;
            this.offsetY = this._pinch.my - newSize / 2 - wy * newScale;

            this._onSettingsChanged();
            this.updateLayout();

            if (this.onSizeChanged) this.onSizeChanged(newSize);
        } else if (this._dragging && e.touches.length === 1) {
            e.preventDefault();
            const t = e.touches[0];
            const dx = t.clientX - this._dragStart.x;
            const dy = t.clientY - this._dragStart.y;
            // Отмечаем "двигался" только при реальном сдвиге,
            // чтобы тап не считался drag-ом.
            if (Math.hypot(dx, dy) > 5) this._touchMoved = true;
            this.offsetX = this._dragStart.offsetX + dx;
            this.offsetY = this._dragStart.offsetY + dy;
            this._userTransformed = true;
            this.updateLayout();
        }
    }

    _onTouchEnd(e) {
        if (e.touches.length === 0) {
            // Детектор двойного тапа: если это не drag и не pinch
            // и два тапа подряд в пределах 300ms — центрируем сцену.
            if (!this._touchMoved && !this._pinch) {
                const now = Date.now();
                if (this._lastTapTime && now - this._lastTapTime < 300) {
                    this._onDblClick({ preventDefault: () => {} });
                    this._lastTapTime = 0;
                } else {
                    this._lastTapTime = now;
                }
            }
            this._pinch = null;
            this._dragging = false;
            this._dragStart = null;
            this._touchMoved = false;
            this.container.style.removeProperty('--lt-speed');
        } else if (e.touches.length === 1) {
            // Один палец остался после pinch — переходим в pan.
            this._pinch = null;
            this._dragging = true;
            this._touchMoved = true;  // не считаем завершение pinch тапом
            const t = e.touches[0];
            this._dragStart = {
                x: t.clientX, y: t.clientY,
                offsetX: this.offsetX, offsetY: this.offsetY,
            };
        }
    }

    _onDblClick(e) {
        if (!this.zoomEnabled) return;
        e.preventDefault();
        this._userTransformed = false;
        this.localZoom = 1.0;
        this.updateLayout();
    }

    setZoomEnabled(enabled) {
        this.zoomEnabled = !!enabled;
        if (enabled) {
            this.container.style.cursor = 'grab';
            this.container.style.touchAction = 'none';
        } else {
            this.container.style.cursor = '';
            this.container.style.touchAction = '';
        }
    }
}
