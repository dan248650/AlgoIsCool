export class WindowRenderer {
    constructor(windowId, title) {
        this.windowId = windowId;
        this.title = title || windowId;
        this.visible = true;

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
}
