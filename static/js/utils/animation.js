import { SquareLine, AnimationManager } from "/static/js/utils/CanvasSquares.js";

class MergeSortAnimationController {
  constructor() {
    // === НАСТРОЙКИ ===
    this.DEBUG_MODE = true;
    this.ANIMATION_ENABLED = true;
    this.INITIAL_DELAY = 3000;
    this.SHOW_VISUAL_DEBUG = false;
    this.FIREWORKS_ENABLED = true;
    this.FIREWORKS_DURATION_MULTIPLIER = 4; // Множитель длительности фейерверков
    this.FIREWORKS_HEIGHT_MULTIPLIER = 3; // Множитель высоты фейерверков
    // ================

    this.canvas = document.getElementById("algorithmCanvas");
    if (!this.canvas) {
      console.error("Canvas element not found!");
      return;
    }

    this.ctx = this.canvas.getContext("2d");
    this.setupCanvas();

    this.config = {
      BASE_SIZE: 50,
      ANIMATION_SPEED: 20,
      HIGHLIGHT_COLOR: "#8888ff",
      FINAL_COLOR: "#32CD32",
      FILL_COLOR: "#ccccff",
      STROKE_COLOR: "#000000",
      TEXT_COLOR: "#000000",
      FIREWORK_COLORS: [
        "#ff0000",
        "#00ff00",
        "#0000ff",
        "#ffff00",
        "#ff00ff",
        "#00ffff",
        "#ff7700",
        "#ff0088",
        "#8800ff",
        "#00ff88",
      ],
    };

    this.state = {
      activeLines: [],
      splitSteps: [],
      mergeQueue: [],
      isAnimating: false,
      fireworks: [],
      finalLine: null,
      animationId: null,
      isPaused: false,
    };

    this.sizes = {};
    this.currentScale = 1;
    this.SPEED_MULTIPLIER = 1;

    this.init();
  }

  destroyAnimation() {
    console.log('🧹 Destroying animation...');
    
    // Останавливаем рендеринг
    this.stopRendering();
    
    // Останавливаем анимацию
    this.state.isAnimating = false;
    
    // Очищаем canvas
    if (this.ctx) {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    // Очищаем все массивы
    this.state.activeLines = [];
    this.state.splitSteps = [];
    this.state.mergeQueue = [];
    this.state.fireworks = [];
    this.state.finalLine = null;
    
    // Сбрасываем глобальный флаг
    window.animationInitialized = false;
    
    console.log('Animation destroyed');
  }

  /**
   * Уничтожает анимацию (alias для destroyAnimation)
   */
  destroy() {
    this.destroyAnimation();
  }

  debugLog(...args) {
    if (this.DEBUG_MODE) {
      console.log("[DEBUG]", ...args);
    }
  }

  setupCanvas() {
    this.canvas.width = this.canvas.offsetWidth;
    this.canvas.height = this.canvas.offsetHeight;
    this.debugLog(
      "Canvas размеры:",
      this.canvas.width,
      "x",
      this.canvas.height
    );
  }

  init() {
    if (window.animationInitialized) return;
    window.animationInitialized = true;

    this.updateSizes(0.9);
    this.SPEED_MULTIPLIER = 5 / this.config.ANIMATION_SPEED;

    if (this.ANIMATION_ENABLED) {
      this.startAnimationSequence();
    }
  }

  calculateSizes(scale = 1) {
    this.currentScale = scale;
    const baseSize = this.config.BASE_SIZE * scale;

    return {
      SIZE: baseSize,
      RADIUS: 0.16 * baseSize,
      SQUARE_SIZE: baseSize,
      SQUARE_SPACING: 0.16 * baseSize,
      SQUARE_WIDTH: baseSize + 0.16 * baseSize,
      VERTICAL_SPACING: 2 * baseSize,
      BASE_HORIZONTAL_SPACING: 7 * baseSize,
    };
  }

  updateSizes(scale) {
    this.sizes = this.calculateSizes(scale);
  }

  async startAnimationSequence() {
    this.debugLog("Начало анимационной последовательности");

    // 3 секунды задержки перед началом
    await this.delay(this.INITIAL_DELAY);

    // Бесконечный цикл анимации
    while (true) {
      if (!this.ANIMATION_ENABLED) break;

      await this.runFullAnimationCycle();

      // Пауза перед перезапуском
      await this.delay(2000);
    }
  }

  async runFullAnimationCycle() {
    try {
      this.debugLog("=== НАЧАЛО НОВОГО ЦИКЛА АНИМАЦИИ ===");

      const initialArray = this.generateRandomArray(8, 10, 99);
      const startX = this.canvas.width / 2;

      this.resetAnimation();
      this.state.isAnimating = true;

      const initialLineWidth =
        initialArray.length * this.sizes.SQUARE_SIZE +
        (initialArray.length - 1) * this.sizes.SQUARE_SPACING;

      const initialLine = new SquareLine(
        startX - initialLineWidth / 2,
        50,
        this.sizes.SQUARE_SIZE,
        this.sizes.RADIUS,
        initialArray,
        this.sizes.SQUARE_SPACING,
        this.config.FILL_COLOR,
        this.config.STROKE_COLOR,
        this.config.TEXT_COLOR
      );

      // Начальная прозрачность 0 для плавного появления
      initialLine.setAlpha(0);

      this.state.activeLines.push(initialLine);
      this.state.mergeQueue.push(initialLine);

      // Запускаем рендеринг
      this.startRendering();

      // 1. Плавное появление начального массива
      this.debugLog("Плавное появление начального массива");
      await initialLine.fade("in", 1500);

      // 2. Подготовка и выполнение шагов разделения
      this.prepareSplitSteps(initialArray, startX, 50, 0);
      this.debugLog("Шагов разделения:", this.state.splitSteps.length);

      for (const step of this.state.splitSteps) {
        if (!this.state.isAnimating) break;
        await this.executeSplitStep(step);
        await this.delay(500 * this.SPEED_MULTIPLIER);
      }

      // 3. Процесс слияния
      if (this.state.isAnimating && this.state.mergeQueue.length > 1) {
        await this.delay(500 * this.SPEED_MULTIPLIER);
        await this.startMergeProcess();
      }

      // 4. Если есть финальная линия - завершающие анимации
      if (this.state.finalLine && this.state.isAnimating) {
        // Превращение в зеленый
        this.debugLog("Изменение цвета на зеленый");
        await this.state.finalLine.changeColor(this.config.FINAL_COLOR, 2000);

        // Пауза перед исчезновением
        await this.delay(1000);

        // Плавное исчезновение
        this.debugLog("Плавное исчезновение");
        await this.state.finalLine.fade("out", 1500);

        // Фейерверк (если включены)
        if (this.FIREWORKS_ENABLED) {
          this.debugLog("Запуск фейерверка");
          await this.createFireworksWithPromise();
        }

        // Очистка после фейерверка
        this.state.finalLine = null;
      }
    } catch (error) {
      console.error("Ошибка в цикле анимации:", error);
    } finally {
      this.stopRendering();
    }
  }

  prepareSplitSteps(arr, startX, startY, depth = 0, parentId = null) {
    if (arr.length <= 1) return;

    const stepId = `split-${depth}-${Date.now()}-${Math.random()
      .toString(36)
      .substr(2, 9)}`;

    this.state.splitSteps.push({
      id: stepId,
      type: "split",
      array: arr,
      startX: startX,
      startY: startY,
      depth: depth,
      parentId: parentId,
    });

    const mid = Math.floor(arr.length / 2);
    const left = arr.slice(0, mid);
    const right = arr.slice(mid);

    const leftWidth =
      left.length * this.sizes.SQUARE_WIDTH - this.sizes.SQUARE_SPACING;
    const rightWidth =
      right.length * this.sizes.SQUARE_WIDTH - this.sizes.SQUARE_SPACING;

    const desiredSeparation =
      this.sizes.BASE_HORIZONTAL_SPACING * Math.pow(0.4, depth);
    const minSeparation =
      leftWidth / 2 + rightWidth / 2 + this.sizes.SQUARE_SPACING * 1.5;
    const separation = Math.max(desiredSeparation, minSeparation);

    const leftCenterX = startX - separation / 2;
    const rightCenterX = startX + separation / 2;

    if (left.length > 1) {
      this.prepareSplitSteps(
        left,
        leftCenterX,
        startY + this.sizes.VERTICAL_SPACING,
        depth + 1,
        stepId
      );
    }

    if (right.length > 1) {
      this.prepareSplitSteps(
        right,
        rightCenterX,
        startY + this.sizes.VERTICAL_SPACING,
        depth + 1,
        stepId
      );
    }
  }

  async executeSplitStep(step) {
    if (!this.state.isAnimating) return;

    const mid = Math.floor(step.array.length / 2);
    const left = step.array.slice(0, mid);
    const right = step.array.slice(mid);

    const leftWidth =
      left.length * this.sizes.SQUARE_WIDTH - this.sizes.SQUARE_SPACING;
    const rightWidth =
      right.length * this.sizes.SQUARE_WIDTH - this.sizes.SQUARE_SPACING;

    const desiredSeparation =
      this.sizes.BASE_HORIZONTAL_SPACING * Math.pow(0.4, step.depth);
    const minSeparation =
      leftWidth / 2 + rightWidth / 2 + this.sizes.SQUARE_SPACING * 1.5;
    const separation = Math.max(desiredSeparation, minSeparation);

    const leftX = step.startX - separation / 2 - leftWidth / 2;
    const rightX = step.startX + separation / 2 - rightWidth / 2;
    const targetY = step.startY + this.sizes.VERTICAL_SPACING;
    console.log("1");
    const leftLine = new SquareLine(
      step.startX - leftWidth - this.sizes.SQUARE_SPACING / 2,
      step.startY,
      this.sizes.SQUARE_SIZE,
      this.sizes.RADIUS,
      left,
      this.sizes.SQUARE_SPACING,
      this.config.FILL_COLOR,
      this.config.STROKE_COLOR,
      this.config.TEXT_COLOR
    );

    const rightLine = new SquareLine(
      step.startX + this.sizes.SQUARE_SPACING / 2,
      step.startY,
      this.sizes.SQUARE_SIZE,
      this.sizes.RADIUS,
      right,
      this.sizes.SQUARE_SPACING,
      this.config.FILL_COLOR,
      this.config.STROKE_COLOR,
      this.config.TEXT_COLOR
    );
    const parentLine = this.state.activeLines.find(
      (line) => line.numbers && this.arraysEqual(line.numbers, step.array)
    );

    if (parentLine) {
      leftLine.parentId = parentLine.id;
      rightLine.parentId = parentLine.id;

      this.state.activeLines = this.state.activeLines.filter(
        (line) => line.id !== parentLine.id
      );

      const parentIndex = this.state.mergeQueue.findIndex(
        (line) => line === parentLine
      );
      if (parentIndex !== -1) {
        this.state.mergeQueue.splice(parentIndex, 1);
      }
    }

    this.state.activeLines.push(leftLine, rightLine);
    this.state.mergeQueue.push(leftLine, rightLine);

    await leftLine.moveTo(leftX, targetY, this.config.ANIMATION_SPEED / 50);
    await rightLine.moveTo(rightX, targetY, this.config.ANIMATION_SPEED / 50);
    console.log("2");
    this.drawFrame();
  }

  async startMergeProcess() {
    this.debugLog("Начинаем процесс слияния...");

    if (!this.state.isAnimating || this.state.mergeQueue.length <= 1) {
      this.debugLog("Условия для слияния не выполнены");
      return;
    }

    // Сортируем очередь слияния по уровню (глубине)
    this.state.mergeQueue.sort((a, b) => {
      const aDepth = this.getLineDepth(a);
      const bDepth = this.getLineDepth(b);
      return bDepth - aDepth;
    });

    let currentLevel = [...this.state.mergeQueue];
    let nextLevel = [];

    while (currentLevel.length > 1 && this.state.isAnimating) {
      this.debugLog(`Уровень слияния: ${currentLevel.length} линий`);

      for (let i = 0; i < currentLevel.length; i += 2) {
        if (!this.state.isAnimating) break;

        if (i + 1 < currentLevel.length) {
          const leftLine = currentLevel[i];
          const rightLine = currentLevel[i + 1];

          this.debugLog(`Слияние: ${leftLine.numbers} + ${rightLine.numbers}`);

          try {
            const mergedLine = await this.mergeTwoLines(leftLine, rightLine);
            if (mergedLine) {
              nextLevel.push(mergedLine);
            }
          } catch (error) {
            console.error("Ошибка при слиянии:", error);
          }

          await this.delay(500 * this.SPEED_MULTIPLIER);
        } else {
          nextLevel.push(currentLevel[i]);
        }
      }

      currentLevel = nextLevel;
      nextLevel = [];

      if (currentLevel.length > 1) {
        await this.delay(300 * this.SPEED_MULTIPLIER);
      }
    }

    if (currentLevel.length === 1 && this.state.isAnimating) {
      this.state.finalLine = currentLevel[0];
      this.debugLog(
        "Финальное слияние завершено:",
        this.state.finalLine.numbers
      );
    }
  }

  getLineDepth(line) {
    return line.numbers.length;
  }

  async mergeTwoLines(leftLine, rightLine) {
    if (!this.state.isAnimating) return null;

    const mergedArray = [];
    let leftIndex = 0;
    let rightIndex = 0;

    const targetX =
      (rightLine.startX -
        leftLine.startX -
        leftLine.getTotalWidth() -
        this.sizes.SQUARE_SPACING) /
        2 +
      leftLine.startX;
    const targetY =
      Math.min(leftLine.startY, rightLine.startY) - this.sizes.VERTICAL_SPACING;

    const resultLine = new SquareLine(
      targetX,
      targetY,
      this.sizes.SQUARE_SIZE,
      this.sizes.RADIUS,
      [],
      this.sizes.SQUARE_SPACING,
      this.config.FILL_COLOR,
      this.config.STROKE_COLOR,
      this.config.TEXT_COLOR
    );

    // Подсветка и сравнение элементов
    while (
      leftIndex < leftLine.squares.length &&
      rightIndex < rightLine.squares.length &&
      this.state.isAnimating
    ) {
      // Подсветка текущих элементов
      await leftLine.squares[leftIndex].highlight(
        this.config.HIGHLIGHT_COLOR,
        300
      );
      await rightLine.squares[rightIndex].highlight(
        this.config.HIGHLIGHT_COLOR,
        300
      );

      await this.delay(200 * this.SPEED_MULTIPLIER);

      const leftValue = leftLine.squares[leftIndex].number;
      const rightValue = rightLine.squares[rightIndex].number;

      if (leftValue <= rightValue) {
        await this.moveSquareToNewLine(
          leftLine.squares[leftIndex],
          resultLine,
          mergedArray.length,
          targetX,
          targetY
        );
        mergedArray.push(leftValue);
        leftIndex++;
      } else {
        await this.moveSquareToNewLine(
          rightLine.squares[rightIndex],
          resultLine,
          mergedArray.length,
          targetX,
          targetY
        );
        mergedArray.push(rightValue);
        rightIndex++;
      }
    }

    // Добавление оставшихся элементов
    while (leftIndex < leftLine.squares.length) {
      await this.moveSquareToNewLine(
        leftLine.squares[leftIndex],
        resultLine,
        mergedArray.length,
        targetX,
        targetY
      );
      mergedArray.push(leftLine.squares[leftIndex].number);
      leftIndex++;
    }

    while (rightIndex < rightLine.squares.length) {
      await this.moveSquareToNewLine(
        rightLine.squares[rightIndex],
        resultLine,
        mergedArray.length,
        targetX,
        targetY
      );
      mergedArray.push(rightLine.squares[rightIndex].number);
      rightIndex++;
    }

    // Обновление состояния
    resultLine.numbers = mergedArray;

    this.state.activeLines = this.state.activeLines.filter(
      (line) => line !== leftLine && line !== rightLine
    );

    this.state.mergeQueue = this.state.mergeQueue.filter(
      (line) => line !== leftLine && line !== rightLine
    );

    this.state.activeLines.push(resultLine);
    this.state.mergeQueue.push(resultLine);

    this.debugLog("Слияние завершено:", mergedArray);
    return resultLine;
  }

  async moveSquareToNewLine(square, resultLine, position, targetX, targetY) {
    const targetSquareX =
      targetX + position * (this.sizes.SQUARE_SIZE + this.sizes.SQUARE_SPACING);
    const targetSquareY = targetY;

    await square.moveTo(
      targetSquareX,
      targetSquareY,
      this.config.ANIMATION_SPEED / 30
    );

    if (!resultLine.squares.includes(square)) {
      resultLine.squares.push(square);
    }
  }

  async createFireworksWithPromise() {
    return new Promise((resolve) => {
      this.state.fireworks = [];
      const colors = this.config.FIREWORK_COLORS;
      const fireworksCount = 8;

      for (let i = 0; i < fireworksCount; i++) {
        const startX = Math.random() * this.canvas.width;
        const startY = this.canvas.height + 100; // Стартуем значительно ниже
        const targetY =
          this.canvas.height * 0.05 + Math.random() * this.canvas.height * 0.1;
        const targetX = startX + (Math.random() - 0.5) * 200; // Больший разброс по горизонтали

        const dx = targetX - startX;
        const dy = targetY - startY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const speed = 6 + Math.random() * 4; // Увеличиваем скорость для высокого полета

        this.state.fireworks.push({
          x: startX,
          y: startY,
          vx: (dx / distance) * speed,
          vy: (dy / distance) * speed,
          targetX,
          targetY,
          color: colors[Math.floor(Math.random() * colors.length)],
          size: 4 + Math.random() * 4, // Увеличиваем размер снарядов
          particles: [],
          exploded: false,
          explosionDelay:
            (1500 + Math.random() * 1000) * this.SPEED_MULTIPLIER * 5,
          timer: 0,
          trail: [],
          trailLength: 10,
        });
      }

      const animateFireworks = () => {
        if (this.state.fireworks.length === 0) {
          resolve();
          return;
        }

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Отрисовка активных линий (если есть)
        this.state.activeLines.forEach((line) => line.draw(this.ctx));

        for (let i = this.state.fireworks.length - 1; i >= 0; i--) {
          const fw = this.state.fireworks[i];

          if (!fw.exploded) {
            // Сохраняем позицию для следа
            fw.trail.push({ x: fw.x, y: fw.y });
            if (fw.trail.length > fw.trailLength) {
              fw.trail.shift();
            }

            // Движение снаряда
            fw.x += fw.vx;
            fw.y += fw.vy;
            fw.timer += 16;

            // Отрисовка следа (более длинного и красивого)
            this.ctx.save();
            for (let j = 0; j < fw.trail.length; j++) {
              const point = fw.trail[j];
              const alpha = (j / fw.trail.length) * 0.8;
              const size = fw.size * 0.6 * (j / fw.trail.length);

              this.ctx.globalAlpha = alpha;
              this.ctx.fillStyle = fw.color;
              this.ctx.beginPath();
              this.ctx.arc(point.x, point.y, size, 0, Math.PI * 2);
              this.ctx.fill();
            }
            this.ctx.restore();

            // Отрисовка снаряда с свечением
            this.ctx.save();
            this.ctx.shadowBlur = 20;
            this.ctx.shadowColor = fw.color;
            this.ctx.fillStyle = fw.color;
            this.ctx.beginPath();
            this.ctx.arc(fw.x, fw.y, fw.size, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.restore();

            // Проверка условий взрыва - взлетаем намного выше
            const shouldExplode =
              fw.y <= fw.targetY || fw.timer >= fw.explosionDelay || fw.y < 30; // Минимальная высота (очень высоко)

            if (shouldExplode) {
              fw.exploded = true;
              const particlesCount = 60 + Math.random() * 30;

              for (let j = 0; j < particlesCount; j++) {
                const angle = Math.random() * Math.PI * 2;
                const speed = 3 + Math.random() * 4; // Большая скорость разлета
                const size = 2 + Math.random() * 3; // Больший размер частиц

                fw.particles.push({
                  x: fw.x,
                  y: fw.y,
                  vx: Math.cos(angle) * speed,
                  vy: Math.sin(angle) * speed,
                  color: fw.color,
                  size,
                  life: (200 + Math.random() * 100) * this.SPEED_MULTIPLIER * 5, // В 5 раз дольше живут
                  alpha: 1,
                  gravity: 0.01 + Math.random() * 0.02, // Меньшая гравитация для медленного падения
                  fadeSpeed: 0.5 + Math.random() * 0.3, // Скорость затухания
                });
              }
            }
          } else {
            let hasActiveParticles = false;

            for (let j = fw.particles.length - 1; j >= 0; j--) {
              const p = fw.particles[j];

              // Движение частиц с гравитацией
              p.x += p.vx;
              p.y += p.vy;
              p.vy += p.gravity;
              p.life--;
              p.alpha = Math.max(0, p.life / 200); // Медленнее затухание

              // Отрисовка частиц с свечением
              this.ctx.save();
              this.ctx.globalAlpha = p.alpha;
              this.ctx.shadowBlur = 15;
              this.ctx.shadowColor = p.color;
              this.ctx.fillStyle = p.color;
              this.ctx.beginPath();

              // Разные формы частиц для разнообразия
              if (Math.random() > 0.7) {
                // Круглые частицы
                this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
              } else {
                // Звездообразные частицы
                this.ctx.moveTo(p.x + p.size, p.y);
                for (let k = 0; k < 5; k++) {
                  this.ctx.lineTo(
                    p.x + p.size * 0.5 * Math.cos((k * 2 * Math.PI) / 5),
                    p.y + p.size * 0.5 * Math.sin((k * 2 * Math.PI) / 5)
                  );
                  this.ctx.lineTo(
                    p.x + p.size * Math.cos(((k * 2 + 1) * Math.PI) / 5),
                    p.y + p.size * Math.sin(((k * 2 + 1) * Math.PI) / 5)
                  );
                }
                this.ctx.closePath();
              }

              this.ctx.fill();
              this.ctx.restore();

              if (p.life <= 0) {
                fw.particles.splice(j, 1);
              } else {
                hasActiveParticles = true;
              }
            }

            if (!hasActiveParticles) {
              this.state.fireworks.splice(i, 1);
            }
          }
        }

        requestAnimationFrame(animateFireworks);
      };

      animateFireworks();
    });
  }

  startRendering() {
    this.stopRendering();

    const render = () => {
      if (this.state.isAnimating && !this.state.isPaused) {
        this.drawFrame();
        this.state.activeLines.forEach((line) => line.update());
        this.state.animationId = requestAnimationFrame(render);
      }
    };

    render();
  }

  stopRendering() {
    if (this.state.animationId) {
      cancelAnimationFrame(this.state.animationId);
      this.state.animationId = null;
    }
  }

  drawFrame() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.state.activeLines.forEach((line) => line.draw(this.ctx));
  }

  delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  resetAnimation() {
    this.stopRendering();
    this.state.activeLines = [];
    this.state.splitSteps = [];
    this.state.mergeQueue = [];
    this.state.fireworks = [];
    this.state.finalLine = null;
    this.state.isAnimating = true;
    this.state.isPaused = false;
  }

  generateRandomArray(length, min, max) {
    return Array.from(
      { length },
      () => Math.floor(Math.random() * (max - min + 1)) + min
    );
  }

  arraysEqual(arr1, arr2) {
    if (!arr1 || !arr2 || arr1.length !== arr2.length) return false;
    return arr1.every((value, index) => value === arr2[index]);
  }
}

// Обновленная функция initAnimation
function initAnimation() {
  // Если уже есть активная анимация, сначала уничтожаем её
  if (window.animationController) {
    window.animationController.destroyAnimation();
  }
  
  window.animationController = new MergeSortAnimationController();
  return window.animationController;
}

// Экспортируем функцию destroyAnimation для внешнего использования
function destroyAnimation() {
  if (window.animationController) {
    window.animationController.destroyAnimation();
    window.animationController = null;
  }
}

export { initAnimation, destroyAnimation };
