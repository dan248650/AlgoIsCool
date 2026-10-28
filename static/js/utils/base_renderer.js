export class BaseRenderer {
    constructor(container) {
        this.container = (typeof container === 'string') ? document.getElementById(container) : container;
        this.elements = new Map();                 // id → DOM element (для массивов)
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
            showIndices: true
        };
        this.baseElementSize = 40;   // все координаты от сервера рассчитаны для этого размера
        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;

        this.initContainer();

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
        const targetSize = this.settings.elementSize;
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
        this.offsetX = (containerRect.width - groupWidth) / 2 - minX;
        this.offsetY = (containerRect.height - groupHeight) / 2 - minY;

        for (const { el, screenX, screenY } of items) {
            el.style.left = `${screenX + this.offsetX}px`;
            el.style.top = `${screenY + this.offsetY}px`;
        }
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
        if ('elementSize' in newSettings) {
            this.settings.elementSize = newSettings.elementSize;
            this.updateLayout();
            this._onSettingsChanged();
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
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async showConditionResult(params, result) {
        const { condition } = params;
        const notification = document.createElement('div');
        notification.className = 'condition-notification';
        notification.textContent = result ? `False ${condition}` : `True ${condition}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${result ? '#4CAF50' : '#f44336'};
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 14px;
            font-family: monospace;
            z-index: 1000;
            animation: slideIn 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        `;
        document.body.appendChild(notification);
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300 / this.settings.speedFactor);
        }, 1500 / this.settings.speedFactor);
        return Promise.resolve();
    }

    async showVariableSet(params) {
        const { variable, value } = params;
        const notification = document.createElement('div');
        notification.className = 'variable-notification';
        notification.textContent = `${variable} = ${value}`;
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #2196F3;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 14px;
            font-family: monospace;
            z-index: 1000;
            animation: slideIn 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        `;
        document.body.appendChild(notification);
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300 / this.settings.speedFactor);
        }, 1500 / this.settings.speedFactor);
        return Promise.resolve();
    }

    // === Диспетчер команд ===
    async executeCommand(command, skipAnimation = false, commandIndex = null) {
        console.log('Executing command:', command.component, command.params);
        switch (command.component) {
            case 'wait':
                await this.sleep(command.params.duration / this.settings.speedFactor);
                break;
            case 'condition_true':
                await this.showConditionResult(command.params, true);
                break;
            case 'condition_false':
                await this.showConditionResult(command.params, false);
                break;
            case 'set_variable':
                await this.showVariableSet(command.params);
                await this._onSetVariable(command.params);
                break;
            case 'update_settings':
                this.updateSettings(command.params);
                break;
            default:
                await this._handleSpecificCommand(command, skipAnimation);
        }
    }

    async _onSetVariable(params) {
        // может быть переопределён в наследниках
    }

    async onBecameVisible(skipAnimation = false) {
        // Переопределяется в наследниках, которым нужна реакция
        // на первое появление структуры в видимом контейнере.
    }

    cancelPendingReveal() {
        // Переопределяется в наследниках, у которых есть отложенное
        // раскрытие. По умолчанию — ничего.
    }

    async _handleSpecificCommand(command, skipAnimation) {
        throw new Error(`Unhandled command: ${command.component}`);
    }

    // Абстрактные методы, которые должны быть переопределены
    applySnapshot(snapshot) {
        throw new Error('applySnapshot must be implemented in subclass');
    }
}
