import { BaseRenderer } from './base_renderer.js';

export class GraphRenderer extends BaseRenderer {
    constructor(containerId) {
        super(containerId);
        this.edges = new Map();
        this.canvas = null;
        this.ctx = null;

        this._lastCanvasLeft = null;
        this._lastCanvasTop = null;
        this._lastCanvasW = null;
        this._lastCanvasH = null;
        this._canvasOriginX = 0;
        this._canvasOriginY = 0;

        this.initCanvas();
        window.addEventListener('resize', () => this.updateLayout());
    }

    initCanvas() {
        this.canvas = document.createElement('canvas');
        this.canvas.style.position = 'absolute';
        this.canvas.style.left = '0px';
        this.canvas.style.top = '0px';
        this.canvas.style.width = '0px';
        this.canvas.style.height = '0px';
        this.canvas.style.pointerEvents = 'none';
        if (!this.container.style.position) {
            this.container.style.position = 'relative';
        }
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
    }

    _computeCanvasBounds() {
        // bbox элементов в системе координат structure (container).
        // el.style.left/top — это позиции в coordinate space, в которой
        // их расставил BaseRenderer.updateLayout.
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        for (const el of this.elements.values()) {
            const x = parseFloat(el.style.left) || 0;
            const y = parseFloat(el.style.top) || 0;
            const w = el.offsetWidth;
            const h = el.offsetHeight;
            if (x < minX) minX = x;
            if (y < minY) minY = y;
            if (x + w > maxX) maxX = x + w;
            if (y + h > maxY) maxY = y + h;
        }
        if (minX === Infinity) {
            const cw = this.container.clientWidth;
            const ch = this.container.clientHeight;
            return { left: 0, top: 0, width: cw, height: ch };
        }

        // Расширяем минимум до bbox structure (0..clientW/H),
        // чтобы canvas всегда покрывал всю structure.
        const structW = this.container.clientWidth;
        const structH = this.container.clientHeight;
        minX = Math.min(minX, 0);
        minY = Math.min(minY, 0);
        maxX = Math.max(maxX, structW);
        maxY = Math.max(maxY, structH);

        // Запас на рёбра (толщина линии, свечение) и небольшую погрешность.
        const pad = 20;
        return {
            left: minX - pad,
            top: minY - pad,
            width: (maxX - minX) + pad * 2,
            height: (maxY - minY) + pad * 2,
        };
    }

    resizeCanvas() {
        const bounds = this._computeCanvasBounds();

        // CSS-позиция и размер (в системе structure).
        const newLeft = Math.floor(bounds.left);
        const newTop = Math.floor(bounds.top);
        const newW = Math.ceil(bounds.width);
        const newH = Math.ceil(bounds.height);

        // Обновляем CSS, только если реально изменилось —
        // иначе браузер будет считать layout каждый кадр.
        if (this._lastCanvasLeft !== newLeft) {
            this.canvas.style.left = `${newLeft}px`;
            this._lastCanvasLeft = newLeft;
        }
        if (this._lastCanvasTop !== newTop) {
            this.canvas.style.top = `${newTop}px`;
            this._lastCanvasTop = newTop;
        }
        if (this._lastCanvasW !== newW) {
            this.canvas.style.width = `${newW}px`;
            this._lastCanvasW = newW;
        }
        if (this._lastCanvasH !== newH) {
            this.canvas.style.height = `${newH}px`;
            this._lastCanvasH = newH;
        }

        // Пиксельный размер — обязательно с DPR, иначе на retina мыло.
        // ВАЖНО: canvas.width = X стирает буфер. Делаем только при
        // реальном изменении размера (иначе рёбра мигают на каждом pan).
        const dpr = window.devicePixelRatio || 1;
        const targetPxW = Math.ceil(newW * dpr);
        const targetPxH = Math.ceil(newH * dpr);
        if (this.canvas.width !== targetPxW || this.canvas.height !== targetPxH) {
            this.canvas.width = targetPxW;
            this.canvas.height = targetPxH;
            this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        }

        // Запоминаем origin — для redrawEdges.
        this._canvasOriginX = newLeft;
        this._canvasOriginY = newTop;

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
        // clearRect в CSS-координатах (ctx scaled на dpr, поэтому
        // используем CSS-размеры, а не canvas.width/height).
        const cssW = this.canvas.width / (window.devicePixelRatio || 1);
        const cssH = this.canvas.height / (window.devicePixelRatio || 1);
        this.ctx.clearRect(0, 0, cssW, cssH);

        const originX = this._canvasOriginX || 0;
        const originY = this._canvasOriginY || 0;
        // Ориентир — structure (container). Позиция элемента в structure
        // = el.style.left (то, что записал updateLayout). Позиция в canvas
        // = (el.style.left − originX).
        for (const [key, edge] of this.edges.entries()) {
            const fromNode = this.elements.get(`node_${edge.from}`);
            const toNode = this.elements.get(`node_${edge.to}`);
            if (fromNode && toNode) {
                const fx = (parseFloat(fromNode.style.left) || 0) + fromNode.offsetWidth / 2;
                const fy = (parseFloat(fromNode.style.top) || 0) + fromNode.offsetHeight / 2;
                const tx = (parseFloat(toNode.style.left) || 0) + toNode.offsetWidth / 2;
                const ty = (parseFloat(toNode.style.top) || 0) + toNode.offsetHeight / 2;
                const x1 = fx - originX;
                const y1 = fy - originY;
                const x2 = tx - originX;
                const y2 = ty - originY;
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
                if (command.params) this._handleCreateGraph(command.params);
                break;
            case 'replace_graph':
                if (command.params) this._handleReplaceGraph(command.params);
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
        if (!params || !Array.isArray(params.nodes)) return;
        this.clear();
        const { nodes, edges, directed } = params;
        this.directed = directed;

        for (const node of nodes) {
            const element = this._createNodeElement(node);
            this.container.appendChild(element);
            this.elements.set(`node_${node.id}`, element);
        }

        this.edges.clear();
        for (const edge of (Array.isArray(edges) ? edges : [])) {
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

    _handleReplaceGraph(params) {
        if (!params || !Array.isArray(params.nodes)) return;
        const { nodes, edges, directed } = params;
        this.directed = directed;

        // Добавляем/обновляем узлы
        const newNodeIds = new Set();
        for (const node of nodes) {
            newNodeIds.add(node.id);
            const key = `node_${node.id}`;
            let el = this.elements.get(key);
            if (el) {
                // Обновляем позицию и цвет
                el.dataset.baseX = node.x;
                el.dataset.baseY = node.y;
                if (node.color) {
                    el.style.boxShadow = `0 0 14px 6px ${node.color}, 0 0 28px 12px ${node.color}`;
                } else {
                    el.style.boxShadow = el.dataset.defaultBs || '0 2px 8px rgba(0,0,0,0.1)';
                }
                const valueDiv = el.querySelector('.value');
                if (valueDiv) valueDiv.textContent = node.label;
            } else {
                el = this._createNodeElement(node);
                this.container.appendChild(el);
                this.elements.set(key, el);
            }
        }

        // Удаляем узлы, которых больше нет
        for (const [key, el] of Array.from(this.elements.entries())) {
            const id = parseInt(key.replace('node_', ''), 10);
            if (!newNodeIds.has(id)) {
                el.remove();
                this.elements.delete(key);
            }
        }

        // Обновляем рёбра
        this.edges.clear();
        for (const edge of (Array.isArray(edges) ? edges : [])) {
            const key = this._edgeKey(edge.from, edge.to);
            this.edges.set(key, {
                from: edge.from,
                to: edge.to,
                color: edge.color || null,
                label: edge.label || null,
                element: null,
                directed: this.directed,
            });
        }

        this.updateLayout();
        setTimeout(() => this.redrawEdges(), 400);
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
        const size = this._getEffectiveSize();
        element.id = `node_${node.id}`;
        element.className = 'visualization-element';
        element.style.position = 'absolute';
        element.style.width = `${size}px`;
        element.style.height = `${size}px`;
        element.style.borderRadius = '50%';
        element.style.backgroundColor = 'rgba(224, 224, 224, 0.8)';
        element.style.display = 'flex';
        element.style.alignItems = 'center';
        element.style.justifyContent = 'center';
        element.style.fontSize = `${Math.max(12, size / 3)}px`;
        element.style.fontWeight = 'bold';
        element.style.color = '#333';
        this._setTransition(element, 'all 0.3s ease-in-out');
        if (node.color) element.style.boxShadow = `0 0 14px 6px ${node.color}, 0 0 28px 12px ${node.color}`;
        else element.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        element.style.cursor = 'pointer';
        element.dataset.defaultBg = 'rgba(224, 224, 224, 0.8)';
        element.dataset.defaultBs = '0 2px 8px rgba(0,0,0,0.1)';
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
            element.style.boxShadow = `0 0 14px 6px ${color}, 0 0 28px 12px ${color}`;
        }
        if (!skipAnimation && duration) {
            await this.sleep(duration / this.settings.speedFactor);
        }
    }

    async _handleUnhighlightNode(params, skipAnimation) {
        const { node_id } = params;
        const element = this.elements.get(`node_${node_id}`);
        if (element) {
            const defaultBs = element.dataset.defaultBs || '0 2px 8px rgba(0,0,0,0.1)';
            element.style.boxShadow = defaultBs;
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
        if (!snapshot || (snapshot.type !== 'graph' && snapshot.type !== 'tree')) return;
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
        const size = this._getEffectiveSize();
        for (const element of this.elements.values()) {
            element.style.width = `${size}px`;
            element.style.height = `${size}px`;
            element.style.fontSize = `${Math.max(12, size / 3)}px`;
            const valueDiv = element.querySelector('.value');
            if (valueDiv) valueDiv.style.fontSize = `${Math.max(12, size / 3)}px`;
        }
        this.redrawEdges();
    }
}
