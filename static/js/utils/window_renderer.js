export class WindowRenderer {
    constructor(windowId, title) {
        this.windowId = windowId;
        this.title = title || windowId;
        this.visible = true;
        this._contentHeight = null;
        this._structureHosts = new Map();  // structureName → div-контейнер

        this.element = document.createElement('div');
        this.element.className = 'scene-window';
        this.element.dataset.windowId = windowId;

        this.header = document.createElement('div');
        this.header.className = 'scene-window-header';
        this.header.textContent = this.title;
        this.element.appendChild(this.header);

        this.content = document.createElement('div');
        this.content.className = 'scene-window-content';
        this.element.appendChild(this.content);
    }

    setTitle(title) {
        this.title = title || this.windowId;
        this.header.textContent = this.title;
    }

    setVisible(visible) {
        this.visible = !!visible;
        this.element.style.display = this.visible ? '' : 'none';
    }

    appendTo(parent) {
        parent.appendChild(this.element);
    }

    remove() {
        this.element.remove();
    }

    // Возвращает (или создаёт) контейнер для конкретной структуры
    ensureStructureHost(name) {
        if (this._structureHosts.has(name)) return this._structureHosts.get(name);
        const host = document.createElement('div');
        host.className = 'scene-window-structure';
        host.dataset.structureName = name;
        this.content.appendChild(host);
        this._structureHosts.set(name, host);
        return host;
    }

    setStructureHeight(name, contentHeight, marginBottom = 0) {
        const host = this._structureHosts.get(name);
        if (!host) return;
        const total = Math.max(0, Math.ceil(contentHeight || 0));
        const mbPx = Math.max(0, Math.round(marginBottom || 0));
        const curH = parseInt(host.style.height, 10) || 0;
        const curM = parseInt(host.style.marginBottom, 10) || 0;
        if (curH === total && curM === mbPx) return;
        host.style.height = total + 'px';
        host.style.marginBottom = mbPx + 'px';
    }

    setContentHeightDirect(totalPx) {
        // Ставит итоговую высоту content без пересчёта padding — уже посчитано снаружи.
        if (this._contentHeight === totalPx) return;
        this._contentHeight = totalPx;
        this.content.style.height = totalPx + 'px';
    }

    clearStructureHeights() {
        for (const host of this._structureHosts.values()) {
            host.style.height = '';
            host.style.marginBottom = '';
        }
    }

    removeStructureHost(name) {
        const host = this._structureHosts.get(name);
        if (host) {
            host.remove();
            this._structureHosts.delete(name);
        }
    }

    computeContentHeight(contentHeight) {
        const style = getComputedStyle(this.content);
        const padTop = parseFloat(style.paddingTop) || 0;
        const padBottom = parseFloat(style.paddingBottom) || 0;
        return Math.max(0, Math.ceil((contentHeight || 0) + padTop + padBottom));
    }

    clearContentHeight() {
        if (this._contentHeight === null) return;
        this._contentHeight = null;
        this.content.style.height = '';
    }
}
