import { BaseRenderer } from './base_renderer.js';

export class ArrayRenderer extends BaseRenderer {
    // --- Специфические методы для массивов ---
    async _handleSpecificCommand(command, skipAnimation) {
        switch (command.component) {
            case 'create_element':
                await this.createElement(command.params, skipAnimation);
                break;
            case 'create_elements':
                this.createElements(command.params.array);
                break;
            case 'move_straight':
                await this.moveStraight(command.params, skipAnimation);
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
    applySnapshot(snapshot) {
        this.clear();
        if (!snapshot || !snapshot.elements) return;
        for (const elem of snapshot.elements) {
            const element = this._createDomElement(elem, elem.x, elem.y);
            this.container.appendChild(element);
            this.elements.set(elem.id, element);
        }
        this.updateLayout();
    }

    _createDomElement(elemData, baseX, baseY) {
        const element = document.createElement('div');
        element.id = elemData.id;
        element.className = 'visualization-element';
        element.style.position = 'absolute';
        element.style.width = `${this.settings.elementSize}px`;
        element.style.height = `${this.settings.elementSize}px`;
        element.style.borderRadius = '8px';
        element.style.backgroundColor = elemData.color && elemData.color !== 'None'
            ? elemData.color
            : 'rgba(224, 224, 224, 0.5)';
        element.style.display = 'flex';
        element.style.flexDirection = 'column';
        element.style.alignItems = 'center';
        element.style.justifyContent = 'center';
        element.style.fontSize = `${Math.max(12, this.settings.elementSize / 3)}px`;
        element.style.fontWeight = 'bold';
        element.style.color = '#333';
        element.style.transition = 'none';
        element.dataset.defaultBg = 'rgba(224, 224, 224, 0.5)';
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
    async createElement(params, skipAnimation = false) {
        const { id, value, x, y } = params;
        const element = document.createElement('div');
        element.id = id;
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
        element.style.transition = 'all 0.3s ease-in-out';
        element.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        element.style.cursor = 'pointer';
        element.dataset.defaultBg = 'rgba(224, 224, 224, 0.5)';
        element.dataset.baseX = x;
        element.dataset.baseY = y;
        element.innerHTML = `
            <div class="value">${value}</div>
            ${this.settings.showIndices ? `<div class="index" style="font-size: 10px; color: #888;">${id.split('_')[1]}</div>` : ''}
        `;
        this.container.appendChild(element);
        this.elements.set(id, element);

        const indexDiv = element.querySelector('.index');
        if (indexDiv) indexDiv.style.fontSize = `${Math.max(10, this.settings.elementSize / 4)}px`;

        if (!skipAnimation) {
            element.style.transform = 'scale(0)';
            await this.sleep(50);
            element.style.transform = 'scale(1)';
            element.style.transition = '';
        } else {
            element.style.transform = 'scale(1)';
        }
        this.updateLayout();
    }

    createElements(array) {
        this.clear();
        array.forEach((value, index) => {
            const element = document.createElement('div');
            element.id = `elem_${index}`;
            element.className = 'visualization-element';
            element.style.position = 'absolute';
            element.style.width = `${this.settings.elementSize}px`;
            element.style.height = `${this.settings.elementSize}px`;
            element.style.borderRadius = '4px';
            element.style.backgroundColor = 'rgba(224, 224, 224, 0.5)';
            element.style.display = 'flex';
            element.style.alignItems = 'center';
            element.style.justifyContent = 'center';
            element.style.fontSize = `${Math.max(12, this.settings.elementSize / 3)}px`;
            element.style.color = '#333';
            element.style.fontWeight = 'bold';
            element.style.transition = 'all 0.3s ease-in-out';
            element.dataset.defaultBg = 'rgba(224, 224, 224, 0.5)';
            element.dataset.baseX = index * (this.baseElementSize + this.settings.spacing);
            element.dataset.baseY = 50;
            element.innerHTML = `
                <div class="value">${value}</div>
                ${this.settings.showIndices ? `<div class="index">${index}</div>` : ''}
            `;
            this.container.appendChild(element);
            const indexDiv = element.querySelector('.index');
            if (indexDiv) indexDiv.style.fontSize = `${Math.max(10, this.settings.elementSize / 4)}px`;
            const valueDiv = element.querySelector('.value');
            if (valueDiv) valueDiv.style.fontSize = `${Math.max(12, this.settings.elementSize / 3)}px`;
            this.elements.set(`elem_${index}`, element);
        });
        this.updateLayout();
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
        for (const id of element_ids) {
            const element = this.elements.get(id);
            if (element) {
                element.style.backgroundColor = color;
                element.style.opacity = opacity;
                element.style.boxShadow = `0 0 8px ${color}`;
            }
        }
        if (!skipAnimation) {
            await this.sleep(duration / this.settings.speedFactor);
        }
    }

    async unhighlight(params, skipAnimation = false) {
        const { element_ids, duration = 400 } = params;
        const actualDuration = duration / this.settings.speedFactor;
        for (const id of element_ids) {
            const element = this.elements.get(id);
            if (!element) continue;
            element.style.transition = `all ${actualDuration}ms ease`;
            const defaultBg = element.dataset.defaultBg || '';
            element.style.backgroundColor = defaultBg;
            element.style.opacity = 1;
            element.style.boxShadow = '';
        }
        if (!skipAnimation) {
            await this.sleep(actualDuration);
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
    }
}
