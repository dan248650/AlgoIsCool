export class InputFormHandler {
    constructor(container, schema, initialData = {}) {
        this.container = container;
        this.schema = schema;
        this.fields = {};
        this.buildForm();
        if (Object.keys(initialData).length) {
            this.setData(initialData);
        }
    }

    buildForm() {
        this.container.innerHTML = '';
        for (const [field, type] of Object.entries(this.schema)) {
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
                input.placeholder = 'числа через запятую (например, 64,34,25)';
            } else if (type === 'number') {
                input = document.createElement('input');
                input.type = 'number';
                input.step = '1';
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

    getData() {
        const data = {};
        for (const [field, type] of Object.entries(this.schema)) {
            const input = this.fields[field];
            if (!input) continue;
            if (type === 'array') {
                const str = input.value.trim();
                data[field] = str ? str.split(',').map(s => parseInt(s.trim(), 10)).filter(v => !isNaN(v)) : [];
            } else if (type === 'number') {
                data[field] = parseInt(input.value, 10);
            } else if (type === 'boolean') {
                data[field] = input.checked;
            } else if (type === 'graph_nodes') {
                const str = input.value.trim();
                if (str === '') data[field] = [];
                else {
                    const labels = str.split(',').map(s => s.trim());
                    data[field] = labels.map((label, idx) => ({ id: idx, label }));
                }
            } else if (type === 'graph_edges') {
                const str = input.value.trim();
                if (str === '') data[field] = [];
                else {
                    const pairs = str.split(',').map(p => p.trim());
                    data[field] = pairs
                        .map(pair => {
                            const parts = pair.split('-');
                            if (parts.length === 2) {
                                const from = Number(parts[0]);
                                const to = Number(parts[1]);
                                if (!isNaN(from) && !isNaN(to)) return { from, to };
                            }
                            return null;
                        })
                        .filter(e => e !== null);
                }
            } else {
                data[field] = input.value;
            }
        }
        // Валидация рёбер (если есть и nodes уже распарсены)
        if (data.edges && data.nodes) {
            const nodeIds = new Set(data.nodes.map(n => n.id));
            const invalidEdges = data.edges.filter(e => !nodeIds.has(e.from) || !nodeIds.has(e.to));
            if (invalidEdges.length) {
                alert(`Ошибка: рёбра ссылаются на несуществующие узлы:\n${invalidEdges.map(e => `${e.from}→${e.to}`).join(', ')}`);
                return null;  // не обновляем данные
            }
        }
        return data;
    }

    setData(data) {
        for (const [field, type] of Object.entries(this.schema)) {
            const input = this.fields[field];
            if (!input || !(field in data)) continue;
            const value = data[field];
            if (type === 'array') {
                input.value = Array.isArray(value) ? value.join(', ') : '';
            } else if (type === 'number') {
                input.value = value;
            } else if (type === 'boolean') {
                input.checked = !!value;
            } else if (type === 'graph_nodes') {
                if (Array.isArray(value)) {
                    const labels = value.map(node => node.label || node).join(',');
                    input.value = labels;
                } else {
                    input.value = '';
                }
            } else if (type === 'graph_edges') {
                if (Array.isArray(value)) {
                    const edgesStr = value.map(edge => `${edge.from}-${edge.to}`).join(',');
                    input.value = edgesStr;
                } else {
                    input.value = '';
                }
            } else {
                input.value = value;
            }
        }
    }

    generateRandom() {
        const randomData = {};
        // Сначала генерируем простые поля и узлы
        for (const [field, type] of Object.entries(this.schema)) {
            if (type === 'graph_nodes') {
                const count = Math.floor(Math.random() * 6) + 3; // 3–8 узлов
                const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
                const labels = [];
                for (let i = 0; i < count; i++) {
                    labels.push({ id: i, label: letters[i % letters.length] });
                }
                randomData[field] = labels;
            } else if (type === 'array') {
                const size = Math.floor(Math.random() * 8) + 5;
                randomData[field] = Array.from({ length: size }, () => Math.floor(Math.random() * 191) - 95);
            } else if (type === 'number') {
                randomData[field] = Math.floor(Math.random() * 90) + 10;
            } else if (type === 'boolean') {
                randomData[field] = Math.random() < 0.5;
            }
        }
        // Генерируем рёбра на основе уже сгенерированных узлов
        for (const [field, type] of Object.entries(this.schema)) {
            if (type === 'graph_edges') {
                const nodes = randomData.nodes || [];
                const count = nodes.length;
                if (count < 2) {
                    randomData[field] = [];
                } else {
                    const edges = [];
                    // связное дерево
                    for (let i = 0; i < count - 1; i++) {
                        edges.push({ from: i, to: i + 1 });
                    }
                    // добавим случайные рёбра для больших графов
                    if (count > 3) {
                        const extra = Math.floor(Math.random() * (count - 2)) + 1;
                        for (let i = 0; i < extra; i++) {
                            let from = Math.floor(Math.random() * count);
                            let to = Math.floor(Math.random() * count);
                            if (from !== to) edges.push({ from, to });
                        }
                    }
                    randomData[field] = edges;
                }
            }
        }
        // Стартовая вершина
        for (const [field, type] of Object.entries(this.schema)) {
            if (field === 'start_node' && type === 'number') {
                const nodes = randomData.nodes || [];
                randomData[field] = nodes.length ? Math.floor(Math.random() * nodes.length) : 0;
            }
        }
        this.setData(randomData);
        return randomData;
    }
}
