import { BaseRenderer } from './base_renderer.js';

export class TableRenderer extends BaseRenderer {
    async _handleSpecificCommand(command, skipAnimation) {
        switch (command.component) {
            case 'create_table':
                this.createTable(command.params);
                break;
            case 'update_cell':
                await this.updateCell(command.params, skipAnimation);
                break;
            case 'highlight_cell':
            case 'unhighlight_cell':
            case 'highlight_row':
            case 'unhighlight_row':
            case 'highlight_col':
            case 'unhighlight_col':
                // Fire-and-forget: команда возвращается сразу после
                // применения стилей. Duration обеспечивает transition.
                // Паузы — через явный wait() в DSL. Иначе await sleep
                // внутри создаёт task-границу → style recalc → прерывание
                // соседней подсветки (row «вползает» по одной клетке).
                this[this._methodByComponent(command.component)](
                    command.params, skipAnimation
                );
                break;
            default:
                throw new Error(`Unknown table component: ${command.component}`);
        }
    }

    _methodByComponent(component) {
        return {
            'highlight_cell': 'highlightCell',
            'unhighlight_cell': 'unhighlightCell',
            'highlight_row': 'highlightRow',
            'unhighlight_row': 'unhighlightRow',
            'highlight_col': 'highlightCol',
            'unhighlight_col': 'unhighlightCol',
        }[component];
    }

    clear() {
        super.clear();
        this.rows = 0;
        this.cols = 0;
    }

    _onSettingsChanged() {
        const size = this._getEffectiveSize();
        for (const el of this.elements.values()) {
            el.style.width = `${size}px`;
            el.style.height = `${size}px`;
            el.style.fontSize = `${Math.max(10, size / 3)}px`;
            const valueDiv = el.querySelector('.value');
            if (valueDiv) valueDiv.style.fontSize = `${Math.max(10, size / 3)}px`;
        }
    }

    // ---------- Создание клетки ----------

    _createCellElement(id, value) {
        const size = this._getEffectiveSize();
        const el = document.createElement('div');
        el.id = id;
        el.className = 'visualization-element table-cell';
        el.style.position = 'absolute';
        el.style.width = `${size}px`;
        el.style.height = `${size}px`;
        el.style.borderRadius = '6px';
        el.style.backgroundColor = 'rgba(224, 224, 224, 0.5)';
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        el.style.fontSize = `${Math.max(10, size / 3)}px`;
        el.style.fontWeight = 'bold';
        el.style.color = '#333';
        el.style.transition = 'none';
        el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        el.dataset.defaultBg = 'rgba(224, 224, 224, 0.5)';
        el.dataset.defaultBs = '0 2px 4px rgba(0,0,0,0.1)';
        el.innerHTML = `<div class="value">${value}</div>`;
        return el;
    }

    // ---------- create_table ----------

    createTable(params) {
        this.clear();
        const { rows, cols, cells } = params;
        this.rows = rows;
        this.cols = cols;
        // baseElementSize, не effectiveSize: updateLayout умножит
        // baseX/baseY на scale = effectiveSize / 40 — gap будет
        // пропорционален zoom.
        const step = this.baseElementSize + this.settings.table_spacing;

        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const id = `cell_${r}_${c}`;
                const el = this._createCellElement(id, cells[r][c]);
                el.dataset.baseX = c * step;
                el.dataset.baseY = r * step;
                this.container.appendChild(el);
                this.elements.set(id, el);
            }
        }
        this.updateLayout();
    }

    // ---------- applySnapshot ----------

    applySnapshot(snapshot) {
        if (!snapshot || snapshot.type !== 'table') return;
        this.clear();
        this.rows = snapshot.rows;
        this.cols = snapshot.cols;
        const step = this.baseElementSize + this.settings.table_spacing;

        for (const cell of snapshot.cells) {
            const id = `cell_${cell.r}_${cell.c}`;
            const el = this._createCellElement(id, cell.value);
            el.dataset.baseX = cell.c * step;
            el.dataset.baseY = cell.r * step;
            if (cell.color) {
                el.style.backgroundColor = cell.color;
                el.style.boxShadow = `0 0 8px 2px ${cell.color}`;
            }
            this.container.appendChild(el);
            this.elements.set(id, el);
        }
        this.updateLayout();
    }

    // ---------- update_cell (изменение значения) ----------
    // Здесь await нужен: значение меняется, вспышка фона, потом
    // возвращаемся. Это не конфликтует с подсветкой — update_cell
    // обычно идёт отдельной командой между wait.

    async updateCell(params, skipAnimation = false) {
        const { row, col, value } = params;
        const el = this.elements.get(`cell_${row}_${col}`);
        if (!el) return;
        const valueDiv = el.querySelector('.value');
        if (valueDiv) valueDiv.textContent = value;
        if (skipAnimation) return;

        const actualDuration = 300 / this.settings.speedFactor;
        valueDiv.style.transition = `background-color ${actualDuration}ms ease`;
        valueDiv.style.backgroundColor = 'rgba(255, 255, 255, 0.7)';
        await this.sleep(actualDuration);
        valueDiv.style.backgroundColor = '';
        valueDiv.style.transition = '';
    }

    // ---------- highlight_cell / unhighlight_cell ----------
    // Синхронные fire-and-forget. Transition проигрывается CSS.

    highlightCell(params, skipAnimation = false) {
        const { row, col, color, duration = 400 } = params;
        const el = this.elements.get(`cell_${row}_${col}`);
        if (!el) return;
        if (skipAnimation) {
            el.style.transition = 'none';
            el.style.backgroundColor = color;
            el.style.boxShadow = `0 0 8px 2px ${color}`;
            return;
        }
        const actualDuration = duration / this.settings.speedFactor;
        el.style.transition =
            `background-color ${actualDuration}ms ease, box-shadow ${actualDuration}ms ease`;
        el.style.backgroundColor = color;
        el.style.boxShadow = `0 0 8px 2px ${color}`;
    }

    unhighlightCell(params, skipAnimation = false) {
        const { row, col, duration = 400 } = params;
        const el = this.elements.get(`cell_${row}_${col}`);
        if (!el) return;
        if (skipAnimation) {
            el.style.transition = 'none';
            el.style.backgroundColor = el.dataset.defaultBg;
            el.style.boxShadow = el.dataset.defaultBs;
            return;
        }
        const actualDuration = duration / this.settings.speedFactor;
        el.style.transition =
            `background-color ${actualDuration}ms ease, box-shadow ${actualDuration}ms ease`;
        el.style.backgroundColor = el.dataset.defaultBg;
        el.style.boxShadow = el.dataset.defaultBs;
    }

    // ---------- highlight_row / unhighlight_row ----------
    // Простой цикл: все transition + все цвета в одном таске —
    // применяются одним style recalc, transition стартует
    // одновременно у всех клеток.

    highlightRow(params, skipAnimation = false) {
        const { row, color, duration = 400 } = params;
        const actualDuration = duration / this.settings.speedFactor;

        for (const [id, el] of this.elements) {
            if (parseInt(id.split('_')[1], 10) === row) {
                if (skipAnimation) {
                    el.style.transition = 'none';
                    el.style.backgroundColor = color;
                    el.style.boxShadow = `0 0 8px 2px ${color}`;
                } else {
                    el.style.transition =
                        `background-color ${actualDuration}ms ease, box-shadow ${actualDuration}ms ease`;
                    el.style.backgroundColor = color;
                    el.style.boxShadow = `0 0 8px 2px ${color}`;
                }
            }
        }
    }

    unhighlightRow(params, skipAnimation = false) {
        const { row, duration = 400 } = params;
        const actualDuration = duration / this.settings.speedFactor;

        for (const [id, el] of this.elements) {
            if (parseInt(id.split('_')[1], 10) === row) {
                if (skipAnimation) {
                    el.style.transition = 'none';
                    el.style.backgroundColor = el.dataset.defaultBg;
                    el.style.boxShadow = el.dataset.defaultBs;
                } else {
                    el.style.transition =
                        `background-color ${actualDuration}ms ease, box-shadow ${actualDuration}ms ease`;
                    el.style.backgroundColor = el.dataset.defaultBg;
                    el.style.boxShadow = el.dataset.defaultBs;
                }
            }
        }
    }

    // ---------- highlight_col / unhighlight_col ----------

    highlightCol(params, skipAnimation = false) {
        const { col, color, duration = 400 } = params;
        const actualDuration = duration / this.settings.speedFactor;

        for (const [id, el] of this.elements) {
            if (parseInt(id.split('_')[2], 10) === col) {
                if (skipAnimation) {
                    el.style.transition = 'none';
                    el.style.backgroundColor = color;
                    el.style.boxShadow = `0 0 8px 2px ${color}`;
                } else {
                    el.style.transition =
                        `background-color ${actualDuration}ms ease, box-shadow ${actualDuration}ms ease`;
                    el.style.backgroundColor = color;
                    el.style.boxShadow = `0 0 8px 2px ${color}`;
                }
            }
        }
    }

    unhighlightCol(params, skipAnimation = false) {
        const { col, duration = 400 } = params;
        const actualDuration = duration / this.settings.speedFactor;

        for (const [id, el] of this.elements) {
            if (parseInt(id.split('_')[2], 10) === col) {
                if (skipAnimation) {
                    el.style.transition = 'none';
                    el.style.backgroundColor = el.dataset.defaultBg;
                    el.style.boxShadow = el.dataset.defaultBs;
                } else {
                    el.style.transition =
                        `background-color ${actualDuration}ms ease, box-shadow ${actualDuration}ms ease`;
                    el.style.backgroundColor = el.dataset.defaultBg;
                    el.style.boxShadow = el.dataset.defaultBs;
                }
            }
        }
    }
}
