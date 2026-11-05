export class WindowRenderer {
    constructor(windowId, title) {
        this.windowId = windowId;
        this.title = title || windowId;
        this.visible = true;
        this._contentHeight = null;

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

    setContentHeight(contentHeight) {
        const style = getComputedStyle(this.content);
        const padTop = parseFloat(style.paddingTop) || 0;
        const padBottom = parseFloat(style.paddingBottom) || 0;
        const total = Math.max(80, Math.ceil(contentHeight + padTop + padBottom));

        if (this._contentHeight === total) return;
        this._contentHeight = total;
        this.content.style.height = total + 'px';
    }

    clearContentHeight() {
        if (this._contentHeight === null) return;
        this._contentHeight = null;
        this.content.style.height = '';
    }
}
