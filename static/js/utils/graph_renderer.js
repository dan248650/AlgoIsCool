import { BaseRenderer } from './base_renderer.js';

export class GraphRenderer extends BaseRenderer {
    constructor(containerId) {
        super(containerId);
        this.edges = new Map();
        this.canvas = null;
        this.ctx = null;
        this.initCanvas();
        window.addEventListener('resize', () => this.updateLayout());
    }

    initCanvas() {
        this.canvas = document.createElement('canvas');
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.pointerEvents = 'none';
        this.container.style.position = 'relative';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
    }

    resizeCanvas() {
        const rect = this.container.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
        this.redrawEdges();
        setTimeout(() => this.redrawEdges(), 200);
        setTimeout(() => this.redrawEdges(), 400);
    }

    updateLayout() {
        super.updateLayout();                       // расставляет узлы (меняет left/top)
        // Принудительно заставляем браузер пересчитать позиции узлов СИНХРОННО
        void this.container.offsetHeight;
        // Теперь узлы имеют новые координаты, можно перерисовывать рёбра
        this.resizeCanvas();                       // обновит размер canvas и вызовет redrawEdges
    }

    redrawEdges() {
        if (!this.ctx) return;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        const containerRect = this.container.getBoundingClientRect();
        for (const [key, edge] of this.edges.entries()) {
            const fromNode = this.elements.get(`node_${edge.from}`);
            const toNode = this.elements.get(`node_${edge.to}`);
            if (fromNode && toNode) {
                const fromRect = fromNode.getBoundingClientRect();
                const toRect = toNode.getBoundingClientRect();
                // Координаты относительно контейнера
                const x1 = fromRect.left + fromRect.width/2 - containerRect.left;
                const y1 = fromRect.top + fromRect.height/2 - containerRect.top;
                const x2 = toRect.left + toRect.width/2 - containerRect.left;
                const y2 = toRect.top + toRect.height/2 - containerRect.top;
                this.ctx.beginPath();
                this.ctx.moveTo(x1, y1);
                this.ctx.lineTo(x2, y2);
                this.ctx.strokeStyle = edge.color || '#87A3B9';
                this.ctx.lineWidth = 4;
                this.ctx.stroke();
            }
        }
    }

    // --- Вспомогательный метод для нормализации ключа ---
    _edgeKey(from, to) {
        if (this.directed) {
            return `${from}-${to}`;
        } else {
            const a = Math.min(from, to);
            const b = Math.max(from, to);
            return `${a}-${b}`;
        }
    }

    async _handleSpecificCommand(command, skipAnimation) {
        switch (command.component) {
            case 'create_graph':
                this._handleCreateGraph(command.params);
                break;
            case 'highlight_node':
                await this._handleHighlightNode(command.params, skipAnimation);
                break;
            case 'unhighlight_node':
                this._handleUnhighlightNode(command.params, skipAnimation);
                break;
            case 'highlight_edge':
                await this._handleHighlightEdge(command.params, skipAnimation);
                break;
            case 'unhighlight_edge':
                this._handleUnhighlightEdge(command.params, skipAnimation);
                break;
            case 'set_node_label':
                this._handleSetNodeLabel(command.params);
                break;
            default:
                console.warn('GraphRenderer: unknown command', command.component);
        }
    }

    _handleCreateGraph(params) {
        this.clear();
        const { nodes, edges, directed } = params;
        this.directed = directed;

        for (const node of nodes) {
            const element = this._createNodeElement(node);
            this.container.appendChild(element);
            this.elements.set(`node_${node.id}`, element);
        }

        this.edges.clear();
        for (const edge of edges) {
            const key = this._edgeKey(edge.from, edge.to);
            this.edges.set(key, {
                from: edge.from,
                to: edge.to,
                color: edge.color || null,
                label: edge.label || null,
                element: null,
                directed: this.directed
            });
        }
        this.updateLayout();
    }

    clear() {
        // Удаляем только узлы (div-элементы), оставляем canvas
        for (let el of this.elements.values()) {
            if (el && el.parentNode) el.remove();
        }
        this.elements.clear();
        // Очищаем canvas (не удаляем его)
        if (this.ctx) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
        this.edges.clear();
    }

    _createNodeElement(node) {
        const element = document.createElement('div');
        element.id = `node_${node.id}`;
        element.className = 'visualization-element';
        element.style.position = 'absolute';
        element.style.width = `${this.settings.elementSize}px`;
        element.style.height = `${this.settings.elementSize}px`;
        element.style.borderRadius = '50%';
        element.style.backgroundColor = node.color || 'rgba(224, 224, 224, 0.8)';
        element.style.display = 'flex';
        element.style.alignItems = 'center';
        element.style.justifyContent = 'center';
        element.style.fontSize = `${Math.max(12, this.settings.elementSize / 3)}px`;
        element.style.fontWeight = 'bold';
        element.style.color = '#333';
        element.style.transition = 'all 0.3s ease-in-out';
        element.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        element.style.cursor = 'pointer';
        element.dataset.defaultBg = 'rgba(224, 224, 224, 0.8)';
        element.dataset.baseX = node.x;
        element.dataset.baseY = node.y;
        element.style.zIndex = '5';
        element.innerHTML = `<div class="value">${node.label}</div>`;
        return element;
    }

    async _handleHighlightNode(params, skipAnimation) {
        const { node_id, color, duration = 600 } = params;
        const element = this.elements.get(`node_${node_id}`);
        if (element) {
            element.style.backgroundColor = color;
            element.style.boxShadow = `0 0 8px ${color}`;
        }
        if (!skipAnimation && duration) {
            await this.sleep(duration / this.settings.speedFactor);
        }
    }

    async _handleUnhighlightNode(params, skipAnimation) {
        const { node_id } = params;
        const element = this.elements.get(`node_${node_id}`);
        if (element) {
            const defaultBg = element.dataset.defaultBg || 'rgba(224, 224, 224, 0.8)';
            element.style.backgroundColor = defaultBg;
            element.style.boxShadow = '';
        }
    }

    async _handleHighlightEdge(params, skipAnimation) {
        const { from, to, color, duration = 500 } = params;
        const key = this._edgeKey(from, to);
        const edge = this.edges.get(key);
        if (edge) {
            edge.color = color;
            this.redrawEdges();
        }
        if (!skipAnimation && duration) {
            await this.sleep(duration / this.settings.speedFactor);
        }
    }

    async _handleUnhighlightEdge(params, skipAnimation) {
        const { from, to } = params;
        const key = this._edgeKey(from, to);
        const edge = this.edges.get(key);
        if (edge) {
            edge.color = null;
            this.redrawEdges();
        }
    }

    _handleSetNodeLabel(params) {
        const { node_id, label } = params;
        const element = this.elements.get(`node_${node_id}`);
        if (element) {
            const valueDiv = element.querySelector('.value');
            if (valueDiv) valueDiv.textContent = label;
        }
    }

    applySnapshot(snapshot) {
        if (!snapshot || snapshot.type !== 'graph') return;
        this.clear();
        const { nodes, edges, directed } = snapshot;
        this.directed = directed !== undefined ? directed : false;

        for (const node of nodes) {
            const element = this._createNodeElement(node);
            this.container.appendChild(element);
            this.elements.set(`node_${node.id}`, element);
        }

        this.edges.clear();
        for (const edge of edges) {
            const key = this._edgeKey(edge.from, edge.to);
            this.edges.set(key, {
                from: edge.from,
                to: edge.to,
                color: edge.color || null,
                label: edge.label || null,
                element: null,
                directed: this.directed
            });
        }
        this.updateLayout();
    }

    _onSettingsChanged() {
        for (const element of this.elements.values()) {
            element.style.width = `${this.settings.elementSize}px`;
            element.style.height = `${this.settings.elementSize}px`;
            element.style.fontSize = `${Math.max(12, this.settings.elementSize / 3)}px`;
            const valueDiv = element.querySelector('.value');
            if (valueDiv) valueDiv.style.fontSize = `${Math.max(12, this.settings.elementSize / 3)}px`;
        }
        this.redrawEdges();
    }

    async _onSetVariable(params) {}
}
