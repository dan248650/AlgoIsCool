export class InputFormHandler {
    constructor(container, schema, initialData = {}) {
        this.container = container;
        this.schema = this._normalizeSchema(schema);
        this.fields = {};
        this.buildForm();
        if (Object.keys(initialData).length) {
            this.setData(initialData);
        }
    }

    _normalizeSchema(raw) {
        const out = {};
        for (const [field, spec] of Object.entries(raw || {})) {
            if (typeof spec === 'string') {
                out[field] = { type: spec, constraints: {}, depends_on: null };
            } else if (spec && typeof spec === 'object') {
                out[field] = {
                    type: spec.type || 'text',
                    constraints: spec.constraints || {},
                    depends_on: spec.depends_on || null,
                };
            } else {
                out[field] = { type: 'text', constraints: {}, depends_on: null };
            }
        }
        return out;
    }

    _hasInt(c, key) {
        return Number.isInteger(c[key]);
    }

    buildForm() {
        this.container.innerHTML = '';
        for (const [field, spec] of Object.entries(this.schema)) {
            const type = spec.type;
            const c = spec.constraints || {};
            const wrapper = document.createElement('div');
            wrapper.className = 'input-field';
            const label = document.createElement('label');
            label.textContent = this.getLabel(field) + ': ';
            label.htmlFor = field;
            wrapper.appendChild(label);

            let input;
            if (type === 'array') {
                input = document.createElement('input');
                input.type = 'text';
                const hints = [];
                if (c.sorted === 'ascending') hints.push('↑');
                if (c.sorted === 'descending') hints.push('↓');
                if (c.has_negatives === true) hints.push('с отрицательными');
                if (c.has_negatives === false) hints.push('без отрицательных');
                input.placeholder = 'числа через запятую'
                    + (hints.length ? ` (${hints.join(', ')})` : '');
            } else if (type === 'number') {
                input = document.createElement('input');
                input.type = 'number';
                input.step = (c.integer === false || c.real === true) ? 'any' : '1';
                if (c.min !== undefined) input.min = c.min;
                if (c.max !== undefined) input.max = c.max;
                if (c.positive) input.placeholder = 'положительное';
                else if (c.negative) input.placeholder = 'отрицательное';
                else if (c.nonnegative) input.placeholder = 'неотрицательное';
                else if (c.nonpositive) input.placeholder = 'неположительное';
            } else if (type === 'boolean') {
                input = document.createElement('input');
                input.type = 'checkbox';
            } else if (type === 'graph_nodes') {
                input = document.createElement('input');
                input.type = 'text';
                input.placeholder = 'метки узлов через запятую (A,B,C)';
            } else if (type === 'graph_edges') {
                input = document.createElement('input');
                input.type = 'text';
                input.placeholder = 'рёбра: 0-1,1-2,2-0';
            } else {
                input = document.createElement('input');
                input.type = 'text';
            }
            input.id = field;
            wrapper.appendChild(input);
            this.container.appendChild(wrapper);
            this.fields[field] = input;
        }
    }

    getLabel(field) {
        const labels = {
            input_array: 'Массив',
            target: 'Целевое значение',
            nodes: 'Узлы (метки)',
            edges: 'Рёбра',
            directed: 'Ориентированный граф',
            start_node: 'Стартовая вершина (индекс)'
        };
        return labels[field] || field;
    }

    _parseField(input, spec) {
        const type = spec.type;
        if (type === 'array') {
            const str = input.value.trim();
            return str ? str.split(',').map(s => parseInt(s.trim(), 10)).filter(v => !isNaN(v)) : [];
        }
        if (type === 'number') {
            const raw = input.value.trim();
            if (raw === '') return NaN;
            const isFloat = (spec.constraints?.integer === false) || (spec.constraints?.real === true);
            return isFloat ? parseFloat(raw) : parseInt(raw, 10);
        }
        if (type === 'boolean') {
            return input.checked;
        }
        if (type === 'graph_nodes') {
            const str = input.value.trim();
            if (str === '') return [];
            return str.split(',').map(s => s.trim()).map((label, idx) => ({ id: idx, label }));
        }
        if (type === 'graph_edges') {
            const str = input.value.trim();
            if (str === '') return [];
            return str.split(',').map(p => p.trim()).map(pair => {
                const parts = pair.split('-');
                if (parts.length === 2) {
                    const from = Number(parts[0]);
                    const to = Number(parts[1]);
                    if (!isNaN(from) && !isNaN(to)) return { from, to };
                }
                return null;
            }).filter(e => e !== null);
        }
        return input.value;
    }

    // ---- Валидация ----
    _validateNumber(value, c, dependsValue) {
        if (typeof value !== 'number' || isNaN(value)) return 'должно быть числом';
        if (c.integer !== false && c.real !== true && !Number.isInteger(value)) return 'должно быть целым';
        if (c.positive && !(value > 0)) return 'должно быть положительным';
        if (c.negative && !(value < 0)) return 'должно быть отрицательным';
        if (c.nonnegative && !(value >= 0)) return 'должно быть неотрицательным';
        if (c.nonpositive && !(value <= 0)) return 'должно быть неположительным';
        if (c.min !== undefined && value < c.min) return `должно быть >= ${c.min}`;
        if (c.max !== undefined && value > c.max) return `должно быть <= ${c.max}`;

        // Зависимость от nodes: 0 <= value < len(nodes)
        if (dependsValue !== undefined && dependsValue !== null) {
            if (Array.isArray(dependsValue) && dependsValue.length > 0
                && (typeof dependsValue[0] === 'object') && ('id' in dependsValue[0])) {
                if (value < 0 || value >= dependsValue.length) {
                    return `должно быть в диапазоне [0, ${dependsValue.length - 1}] (узлов: ${dependsValue.length})`;
                }
            }
        }
        return null;
    }

    _validateArray(value, c) {
        if (!Array.isArray(value)) return 'должно быть массивом';
        if (c.min_length !== undefined && value.length < c.min_length) return `длина должна быть >= ${c.min_length}`;
        if (c.max_length !== undefined && value.length > c.max_length) return `длина должна быть <= ${c.max_length}`;
        if (value.length === 0) return null;
        if (c.has_negatives === true && !value.some(v => v < 0)) return 'должен содержать хотя бы одно отрицательное';
        if (c.has_negatives === false && value.some(v => v < 0)) return 'не должен содержать отрицательных';
        if (c.min_value !== undefined && value.some(v => v < c.min_value)) return `все значения должны быть >= ${c.min_value}`;
        if (c.max_value !== undefined && value.some(v => v > c.max_value)) return `все значения должны быть <= ${c.max_value}`;
        if (c.sorted === 'ascending') {
            for (let i = 1; i < value.length; i++) if (value[i] < value[i - 1]) return 'должен быть по возрастанию';
        }
        if (c.sorted === 'descending') {
            for (let i = 1; i < value.length; i++) if (value[i] > value[i - 1]) return 'должен быть по убыванию';
        }
        return null;
    }

    _validateGraphNodes(value, c) {
        if (!Array.isArray(value)) return 'должно быть списком узлов';
        if (c.min_count !== undefined && value.length < c.min_count) return `минимум ${c.min_count} узлов`;
        if (c.max_count !== undefined && value.length > c.max_count) return `максимум ${c.max_count} узлов`;
        return null;
    }

    _validateGraphEdges(value, c, dependsValue) {
        if (!Array.isArray(value)) return 'должно быть списком рёбер';

        let nodeCount;
        if (dependsValue !== undefined && dependsValue !== null && Array.isArray(dependsValue)) {
            nodeCount = dependsValue.length;
        } else {
            let maxId = -1;
            for (const e of value) {
                if (typeof e.from === 'number' && e.from > maxId) maxId = e.from;
                if (typeof e.to === 'number' && e.to > maxId) maxId = e.to;
            }
            nodeCount = maxId + 1;
        }

        for (const e of value) {
            if (typeof e.from !== 'number' || typeof e.to !== 'number') continue;
            if (e.from < 0 || e.to < 0) return `ребро ${e.from}→${e.to}: отрицательный id`;
            if (e.from >= nodeCount || e.to >= nodeCount) {
                return `ребро ${e.from}→${e.to} ссылается на узел вне диапазона [0, ${nodeCount - 1}]`;
            }
        }
        if (this._hasInt(c, 'exact_count') && value.length !== c.exact_count) {
            return `должно быть ровно ${c.exact_count} рёбер, сейчас ${value.length}`;
        }
        if (c.no_cycles && nodeCount > 0 && this._hasCycle(nodeCount, value)) {
            return 'граф не должен содержать циклов';
        }
        if (c.connected && nodeCount > 0 && !this._isConnected(nodeCount, value)) {
            return 'граф должен быть связным';
        }
        return null;
    }

    _hasCycle(nodeCount, edges) {
        const adj = Array.from({ length: nodeCount }, () => []);
        for (const e of edges) { adj[e.from].push(e.to); adj[e.to].push(e.from); }
        const visited = new Array(nodeCount).fill(false);
        const dfs = (u, parent) => {
            visited[u] = true;
            for (const v of adj[u]) {
                if (!visited[v]) { if (dfs(v, u)) return true; }
                else if (v !== parent) return true;
            }
            return false;
        };
        for (let i = 0; i < nodeCount; i++) {
            if (!visited[i] && dfs(i, -1)) return true;
        }
        return false;
    }

    _isConnected(nodeCount, edges) {
        if (nodeCount === 0) return true;
        const adj = Array.from({ length: nodeCount }, () => []);
        for (const e of edges) { adj[e.from].push(e.to); adj[e.to].push(e.from); }
        const visited = new Array(nodeCount).fill(false);
        const stack = [0];
        visited[0] = true;
        let count = 0;
        while (stack.length) {
            const u = stack.pop();
            count++;
            for (const v of adj[u]) {
                if (!visited[v]) { visited[v] = true; stack.push(v); }
            }
        }
        return count === nodeCount;
    }

    _validateField(field, value, spec, data) {
        const type = spec.type;
        const c = spec.constraints || {};
        const dependsValue = spec.depends_on ? data[spec.depends_on] : undefined;
        if (type === 'number') return this._validateNumber(value, c, dependsValue);
        if (type === 'array') return this._validateArray(value, c);
        if (type === 'graph_nodes') return this._validateGraphNodes(value, c);
        if (type === 'graph_edges') return this._validateGraphEdges(value, c, dependsValue);
        return null;
    }

    getData() {
        const data = {};
        for (const [field, spec] of Object.entries(this.schema)) {
            const input = this.fields[field];
            if (!input) continue;
            data[field] = this._parseField(input, spec);
        }
        for (const [field, spec] of Object.entries(this.schema)) {
            const err = this._validateField(field, data[field], spec, data);
            if (err) {
                alert(`Ошибка в поле «${this.getLabel(field)}»: ${err}`);
                return null;
            }
        }
        return data;
    }

    setData(data) {
        for (const [field, spec] of Object.entries(this.schema)) {
            const input = this.fields[field];
            if (!input || !(field in data)) continue;
            const type = spec.type;
            const value = data[field];
            if (type === 'array') {
                input.value = Array.isArray(value) ? value.join(', ') : '';
            } else if (type === 'number') {
                input.value = (value === undefined || value === null || Number.isNaN(value)) ? '' : value;
            } else if (type === 'boolean') {
                input.checked = !!value;
            } else if (type === 'graph_nodes') {
                input.value = Array.isArray(value) ? value.map(n => n.label || n).join(',') : '';
            } else if (type === 'graph_edges') {
                input.value = Array.isArray(value) ? value.map(e => `${e.from}-${e.to}`).join(',') : '';
            } else {
                input.value = (value === undefined || value === null) ? '' : value;
            }
        }
    }

    // ---- Генерация ----
    _generateNumber(field, c, dependsValue) {
        let lo = (c.min !== undefined) ? c.min : null;
        let hi = (c.max !== undefined) ? c.max : null;

        // Зависимость от nodes: [0, len(nodes)-1]
        if (dependsValue !== undefined && dependsValue !== null && Array.isArray(dependsValue)
            && dependsValue.length > 0
            && typeof dependsValue[0] === 'object' && 'id' in dependsValue[0]) {
            const n = dependsValue.length;
            if (lo === null) lo = 0;
            if (hi === null) hi = Math.max(0, n - 1);
        }

        // Зависимость от array: [min, max]
        if (dependsValue !== undefined && dependsValue !== null && Array.isArray(dependsValue)
            && dependsValue.length > 0 && typeof dependsValue[0] === 'number') {
            if (lo === null) lo = Math.min(...dependsValue);
            if (hi === null) hi = Math.max(...dependsValue);
        }

        if (lo === null && hi === null) {
            if (field === 'start_node') { lo = 0; hi = 10; }
            else { lo = -100; hi = 100; }
        } else if (lo === null) lo = hi - 200;
        else if (hi === null) hi = lo + 200;

        if (c.positive) lo = Math.max(lo, 1);
        if (c.nonnegative) lo = Math.max(lo, 0);
        if (c.negative) hi = Math.min(hi, -1);
        if (c.nonpositive) hi = Math.min(hi, 0);
        if (lo > hi) lo = hi;
        return Math.floor(Math.random() * (hi - lo + 1)) + lo;
    }

    _generateArray(c) {
        const minLen = c.min_length ?? 5;
        const maxLen = c.max_length ?? Math.max(minLen, 12);
        const size = Math.floor(Math.random() * (maxLen - minLen + 1)) + minLen;
        const vmin = c.min_value ?? -95;
        const vmax = c.max_value ?? 95;
        let arr = Array.from({ length: size }, () =>
            Math.floor(Math.random() * (vmax - vmin + 1)) + vmin
        );
        if (c.has_negatives === true) {
            if (!arr.some(v => v < 0)) arr[0] = Math.max(vmin, -Math.abs(arr[0]) - 1);
        } else if (c.has_negatives === false) {
            arr = arr.map(v => Math.abs(v));
        }
        if (c.sorted === 'ascending') arr.sort((a, b) => a - b);
        else if (c.sorted === 'descending') arr.sort((a, b) => b - a);
        return arr;
    }

    _generateNodes(c) {
        const minCount = c.min_count ?? 3;
        const maxCount = c.max_count ?? 8;
        const count = Math.floor(Math.random() * (maxCount - minCount + 1)) + minCount;
        const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        return Array.from({ length: count }, (_, i) => ({ id: i, label: letters[i % letters.length] }));
    }

    _generateEdges(c, dependsValue) {
        let count;
        if (dependsValue !== undefined && dependsValue !== null && Array.isArray(dependsValue)) {
            count = dependsValue.length;
        } else {
            count = c.node_count ?? 5;
        }

        const wantAcyclic = c.no_cycles === true;
        const edges = [];

        // Случайное остовное дерево: перемешиваем узлы, каждый новый
        // подключаем к случайному уже подключённому. Гарантирует
        // связность и отсутствие циклов, но форма случайная —
        // возможны ветвления, а не только «бамбук» 0-1-2-3-...
        const shuffled = Array.from({ length: count }, (_, i) => i);
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        for (let k = 1; k < count; k++) {
            const parent = shuffled[Math.floor(Math.random() * k)];
            edges.push({ from: parent, to: shuffled[k] });
        }

        // Доп. рёбра — только если разрешены циклы
        if (!wantAcyclic) {
            let extra;
            if (this._hasInt(c, 'exact_count')) extra = Math.max(0, c.exact_count - (count - 1));
            else if (count > 3) extra = Math.floor(Math.random() * (count - 2)) + 1;
            else extra = 0;
            for (let i = 0; i < extra; i++) {
                const from = Math.floor(Math.random() * count);
                const to = Math.floor(Math.random() * count);
                if (from === to) continue;
                if (edges.some(e => (e.from === from && e.to === to) || (e.from === to && e.to === from))) continue;
                edges.push({ from, to });
            }
        }
        if (this._hasInt(c, 'exact_count') && edges.length > c.exact_count) edges.length = c.exact_count;
        return edges;
    }

    generateRandom() {
        const randomData = {};
        const pending = { ...this.schema };

        // Топологическая генерация: сначала поля без depends_on
        // (или с уже сгенерированной зависимостью).
        let guard = 0;
        while (Object.keys(pending).length > 0 && guard++ < 100) {
            let progressed = false;
            for (const [field, spec] of Object.entries(pending)) {
                if (spec.depends_on && !(spec.depends_on in randomData)) continue;
                const c = spec.constraints || {};
                const dep = spec.depends_on ? randomData[spec.depends_on] : undefined;

                if (spec.type === 'graph_nodes') randomData[field] = this._generateNodes(c);
                else if (spec.type === 'graph_edges') randomData[field] = this._generateEdges(c, dep);
                else if (spec.type === 'array') randomData[field] = this._generateArray(c);
                else if (spec.type === 'number') randomData[field] = this._generateNumber(field, c, dep);
                else if (spec.type === 'boolean') randomData[field] = Math.random() < 0.5;

                delete pending[field];
                progressed = true;
            }
            if (!progressed) break;  // Циклическая зависимость — выходим
        }

        this.setData(randomData);
        return randomData;
    }
}
