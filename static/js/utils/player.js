export class VisualizationPlayer {
    constructor(renderEngine) {
        this.renderEngine = renderEngine;
        this.commands = [];
        this.isPlaying = false;
        this.currentIndex = 0;
    }

    setCommands(commands) {
        this.commands = commands || [];
        this.currentIndex = 0;
    }

    set onStep(callback) {
        this._onStep = callback;
    }

    async play() {
        if (this.isPlaying) return;
        if (!this.commands || this.commands.length === 0) {
            console.warn('No commands to play. Use setCommands() first.');
            return;
        }
        this.isPlaying = true;
        for (let i = this.currentIndex; i < this.commands.length && this.isPlaying; i++) {
            const command = this.commands[i];
            if (command) {
                await this.renderEngine.executeCommand(command);
                this.currentIndex = i + 1;
                if (this._onStep) this._onStep(this.currentIndex);
            }
        }
        this.isPlaying = false;
    }

    pause() {
        this.isPlaying = false;
    }

    stop() {
        this.isPlaying = false;
        this.currentIndex = 0;
    }

    reset() {
        this.stop();
        this.renderEngine.clear();
        // Перезапуск с первой команды
        if (this.commands && this.commands.length > 0) {
            this.currentIndex = 0;
            this.renderEngine.executeCommand(this.commands[0]);
        }
    }

    next() {
        if (!this.isPlaying && this.currentIndex < this.commands.length) {
            const command = this.commands[this.currentIndex];
            if (command) {
                this.renderEngine.executeCommand(command);
            }
            this.currentIndex++;
        }
    }
}
