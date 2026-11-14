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
                let dep = spec.depends_on || null;
                if (typeof dep === 'string') {
                    dep = { field: dep, mode: null };
                }
                out[field] = {
                    type: spec.type || 'text',
                    constraints: spec.constraints || {},
                    depends_on: dep,
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
            } else if (type === 'string') {
                input = document.createElement('input');
                input.type = 'text';
                input.placeholder = 'строка (например, abacaba)';
                if (c.min_length !== undefined) input.minLength = c.min_length;
                if (c.max_length !== undefined) input.maxLength = c.max_length;
            } else if (type === 'table') {
                input = document.createElement('input');
                input.type = 'text';
                input.placeholder = 'строки через ; , столбцы через , — например: 1,2,3;4,5,6;7,8,9';
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

    static TYPE_LABELS = {
        'array': 'Массив',
        'number': 'Число',
        'string': 'Строка',
        'boolean': 'Флаг',
        'table': 'Таблица',
        'graph_nodes': 'Узлы',
        'graph_edges': 'Рёбра',
    };

    static FIELD_LABELS = {
        'start_node': 'Стартовая вершина (индекс)',
        'directed': 'Ориентированный граф',
        'target': 'Целевое значение',
        'matrix': 'Матрица',
    };

    getLabel(field) {
        const spec = this.schema[field];
        if (spec?.constraints?.label) return spec.constraints.label;
        if (InputFormHandler.FIELD_LABELS[field]) return InputFormHandler.FIELD_LABELS[field];
        if (spec?.type && InputFormHandler.TYPE_LABELS[spec.type]) {
            return InputFormHandler.TYPE_LABELS[spec.type];
        }
        return field;
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
        if (type === 'string') {
            return input.value;
        }
        if (type === 'table') {
            const str = input.value.trim();
            if (str === '') return [];
            const rows = str.split(';').map(s => s.trim()).filter(s => s !== '');
            return rows.map(row =>
                row.split(',').map(cell => {
                    const n = Number(cell.trim());
                    return isNaN(n) ? cell.trim() : n;
                })
            );
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

    _validateNumber(value, c, dependsValue, depSpec) {
        if (typeof value !== 'number' || isNaN(value)) return 'должно быть числом';
        if (c.integer !== false && c.real !== true && !Number.isInteger(value)) return 'должно быть целым';
        if (c.positive && !(value > 0)) return 'должно быть положительным';
        if (c.negative && !(value < 0)) return 'должно быть отрицательным';
        if (c.nonnegative && !(value >= 0)) return 'должно быть неотрицательным';
        if (c.nonpositive && !(value <= 0)) return 'должно быть неположительным';
        if (c.min !== undefined && value < c.min) return `должно быть >= ${c.min}`;
        if (c.max !== undefined && value > c.max) return `должно быть <= ${c.max}`;

        // --- Динамические ограничения от depends_on ---
        if (depSpec && Array.isArray(dependsValue) && dependsValue.length > 0) {
            // max_of: value <= max(dependsValue)
            if (depSpec.mode === 'max_of'
                && typeof dependsValue[0] === 'number') {
                const mx = Math.max(...dependsValue);
                if (value > mx) {
                    return `должно быть <= max(${depSpec.field}) = ${mx}`;
                }
            }
            // sum_scaled: value <= sum(dependsValue).
            // Ratio — только для генерации (`_generateNumber` даёт
            // ratio·sum для «интересного» случая). Валидация — без
            // ratio: автор вручную может ввести любую вместимость
            // до суммы весов включительно (тривиальный случай «всё
            // влезает» — его ответственность, но больше суммы —
            // заведомо избыточно).
            if (depSpec.mode === 'sum_scaled'
                && typeof dependsValue[0] === 'number') {
                const sum = dependsValue.reduce((s, v) => s + (Number(v) || 0), 0);
                if (value > sum) {
                    return `должно быть <= sum(${depSpec.field}) = ${sum}`;
                }
            }
        }

        if (depSpec && depSpec.mode === null && Array.isArray(dependsValue)
            && dependsValue.length > 0
            && typeof dependsValue[0] === 'object' && 'id' in dependsValue[0]) {
            if (value < 0 || value >= dependsValue.length) {
                return `должно быть в диапазоне [0, ${dependsValue.length - 1}]`;
            }
        }
        return null;
    }

    _validateArray(value, c, dependsValue, depSpec) {
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

        if (depSpec && Array.isArray(dependsValue)) {
            if (depSpec.mode === 'same_length' && value.length !== dependsValue.length) {
                return `длина должна совпадать с «${depSpec.field}» (${dependsValue.length})`;
            }
            if (depSpec.mode === 'subset') {
                const srcSet = new Set(dependsValue);
                for (const v of value) {
                    if (!srcSet.has(v)) {
                        return `элемент ${v} отсутствует в «${depSpec.field}»`;
                    }
                }
            }
        }

        return null;
    }

    _validateString(value, c) {
        if (typeof value !== 'string') return 'должно быть строкой';
        if (c.min_length !== undefined && value.length < c.min_length) return `длина должна быть >= ${c.min_length}`;
        if (c.max_length !== undefined && value.length > c.max_length) return `длина должна быть <= ${c.max_length}`;
        if (c.alphabet && value.split('').some(ch => c.alphabet.indexOf(ch) < 0)) {
            return `символы должны быть из множества "${c.alphabet}"`;
        }
        return null;
    }

    _validateTable(value, c) {
        if (!Array.isArray(value)) return 'должно быть списком строк';
        if (value.length === 0) return null;
        if (c.min_rows !== undefined && value.length < c.min_rows) return `минимум ${c.min_rows} строк`;
        if (c.max_rows !== undefined && value.length > c.max_rows) return `максимум ${c.max_rows} строк`;
        const width = Array.isArray(value[0]) ? value[0].length : 0;
        if (c.min_cols !== undefined && width < c.min_cols) return `минимум ${c.min_cols} столбцов`;
        if (c.max_cols !== undefined && width > c.max_cols) return `максимум ${c.max_cols} столбцов`;
        for (let i = 0; i < value.length; i++) {
            if (!Array.isArray(value[i])) return `строка ${i} не является списком`;
            if (value[i].length !== width) return `строка ${i} имеет разную длину с первой`;
            if (c.integer !== false) {
                for (const cell of value[i]) {
                    if (typeof cell !== 'number' || !Number.isInteger(cell)) {
                        return `строка ${i}: все ячейки должны быть целыми`;
                    }
                }
            }
            if (c.min_value !== undefined && value[i].some(v => v < c.min_value)) {
                return `строка ${i}: значения должны быть >= ${c.min_value}`;
            }
            if (c.max_value !== undefined && value[i].some(v => v > c.max_value)) {
                return `строка ${i}: значения должны быть <= ${c.max_value}`;
            }
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

    _validateField(field, value, spec, allData) {
        const type = spec.type;
        const c = spec.constraints || {};
        const depSpec = spec.depends_on;
        const depField = depSpec ? depSpec.field : null;
        const dependsValue = depField ? allData[depField] : undefined;

        if (type === 'number') return this._validateNumber(value, c, dependsValue, depSpec);
        if (type === 'array') return this._validateArray(value, c, dependsValue, depSpec);
        if (type === 'string') return this._validateString(value, c);
        if (type === 'graph_nodes') return this._validateGraphNodes(value, c);
        if (type === 'graph_edges') return this._validateGraphEdges(value, c, dependsValue);
        if (type === 'table') return this._validateTable(value, c);
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
            } else if (type === 'string') {
                input.value = (value === undefined || value === null) ? '' : String(value);
            } else if (type === 'table') {
                if (Array.isArray(value) && value.length > 0) {
                    input.value = value.map(row => row.join(',')).join(';');
                } else {
                    input.value = '';
                }
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

    _generateNumber(field, c, dependsValue, depSpec) {
        if (depSpec && Array.isArray(dependsValue) && dependsValue.length > 0) {
            if (depSpec.mode === 'max_of') {
                const mx = Math.max(...dependsValue.map(Number).filter(v => !isNaN(v)));
                let lo = (c.min !== undefined) ? c.min : 1;
                let hi = (c.max !== undefined) ? Math.min(c.max, mx) : mx;
                if (lo > hi) lo = hi;
                return Math.floor(Math.random() * (hi - lo + 1)) + lo;
            }
            if (depSpec.mode === 'sum_scaled') {
                const sum = dependsValue.reduce((s, v) => s + (Number(v) || 0), 0);
                const ratio = depSpec.ratio ?? 0.7;
                let target = Math.round(sum * ratio);
                if (c.min !== undefined) target = Math.max(target, c.min);
                if (c.max !== undefined) target = Math.min(target, c.max);
                return target;
            }
        }

        let lo = (c.min !== undefined) ? c.min : null;
        let hi = (c.max !== undefined) ? c.max : null;

        if (dependsValue !== undefined && dependsValue !== null && Array.isArray(dependsValue)
            && dependsValue.length > 0
            && typeof dependsValue[0] === 'object' && 'id' in dependsValue[0]) {
            const n = dependsValue.length;
            if (lo === null) lo = 0;
            if (hi === null) hi = Math.max(0, n - 1);
        }

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

    _generateArray(c, dependsValue, depSpec) {
        const minLen = c.min_length ?? 5;
        const maxLen = c.max_length ?? Math.max(minLen, 12);

        if (depSpec && Array.isArray(dependsValue)) {
            if (depSpec.mode === 'same_length') {
                return this._randomNumbers(dependsValue.length, c);
            }
            if (depSpec.mode === 'subset' && dependsValue.length > 0) {
                const shuffled = [...dependsValue].sort(() => Math.random() - 0.5);
                const take = Math.max(minLen, Math.floor(shuffled.length * 0.7));
                return shuffled.slice(0, Math.min(take, maxLen));
            }
        }

        const size = Math.floor(Math.random() * (maxLen - minLen + 1)) + minLen;
        return this._randomNumbers(size, c);
    }

    _randomNumbers(size, c) {
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

    _generateString(c) {
        const alphabet = c.alphabet || 'abc';
        const minLen = c.min_length ?? 5;
        const maxLen = c.max_length ?? 12;
        const len = Math.floor(Math.random() * (maxLen - minLen + 1)) + minLen;
        let out = '';
        for (let i = 0; i < len; i++) {
            out += alphabet[Math.floor(Math.random() * alphabet.length)];
        }
        return out;
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

        const shuffled = Array.from({ length: count }, (_, i) => i);
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        for (let k = 1; k < count; k++) {
            const parent = shuffled[Math.floor(Math.random() * k)];
            edges.push({ from: parent, to: shuffled[k] });
        }

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

    _generateTable(c) {
        const rows = Math.floor(Math.random() * ((c.max_rows ?? 4) - (c.min_rows ?? 3) + 1)) + (c.min_rows ?? 3);
        const cols = Math.floor(Math.random() * ((c.max_cols ?? 4) - (c.min_cols ?? 3) + 1)) + (c.min_cols ?? 3);
        const minV = c.min_value ?? 0;
        const maxV = c.max_value ?? 9;
        const out = [];
        for (let r = 0; r < rows; r++) {
            const row = [];
            for (let cc = 0; cc < cols; cc++) {
                row.push(Math.floor(Math.random() * (maxV - minV + 1)) + minV);
            }
            out.push(row);
        }
        return out;
    }

    generateRandom() {
        const randomData = {};
        const pending = { ...this.schema };

        let guard = 0;
        while (Object.keys(pending).length > 0 && guard++ < 100) {
            let progressed = false;
            for (const [field, spec] of Object.entries(pending)) {
                const depSpec = spec.depends_on;
                if (depSpec && !(depSpec.field in randomData)) continue;
                const c = spec.constraints || {};
                const dep = depSpec ? randomData[depSpec.field] : undefined;

                if (spec.type === 'graph_nodes') randomData[field] = this._generateNodes(c);
                else if (spec.type === 'graph_edges') randomData[field] = this._generateEdges(c, dep);
                else if (spec.type === 'array') randomData[field] = this._generateArray(c, dep, depSpec);
                else if (spec.type === 'number') randomData[field] = this._generateNumber(field, c, dep, depSpec);
                else if (spec.type === 'boolean') randomData[field] = Math.random() < 0.5;
                else if (spec.type === 'string') randomData[field] = this._generateString(c);
                else if (spec.type === 'table') randomData[field] = this._generateTable(c);

                delete pending[field];
                progressed = true;
            }
            if (!progressed) break;
        }

        this.setData(randomData);
        return randomData;
    }
}
