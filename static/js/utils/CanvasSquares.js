class AnimationManager {
  static async animate(updateCallback, duration, easing = "linear") {
    return new Promise((resolve) => {
      const startTime = performance.now();

      function animateFrame(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        let easedProgress = progress;
        switch (easing) {
          case "easeInOut":
            easedProgress =
              progress < 0.5
                ? 2 * progress * progress
                : -1 + (4 - 2 * progress) * progress;
            break;
          case "easeIn":
            easedProgress = progress * progress;
            break;
          case "easeOut":
            easedProgress = progress * (2 - progress);
            break;
          default:
            easedProgress = progress;
        }

        updateCallback(easedProgress);

        if (progress < 1) {
          requestAnimationFrame(animateFrame);
        } else {
          updateCallback(1);
          resolve();
        }
      }

      requestAnimationFrame(animateFrame);
    });
  }

  static lerp(start, end, progress) {
    return start + (end - start) * progress;
  }

  static lerpColor(color1, color2, progress) {
    const parseHex = (hex) => {
      hex = hex.startsWith("#") ? hex.slice(1) : hex;
      return [
        parseInt(hex.substr(0, 2), 16),
        parseInt(hex.substr(2, 2), 16),
        parseInt(hex.substr(4, 2), 16),
      ];
    };

    const toHex = (r, g, b) =>
      `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;

    const [r1, g1, b1] = parseHex(color1);
    const [r2, g2, b2] = parseHex(color2);

    const r = Math.round(AnimationManager.lerp(r1, r2, progress));
    const g = Math.round(AnimationManager.lerp(g1, g2, progress));
    const b = Math.round(AnimationManager.lerp(b1, b2, progress));

    return toHex(r, g, b);
  }
}

class Square {
  constructor(x, y, side, radius, number, fillColor, strokeColor, textColor) {
    this.setProperties(
      x,
      y,
      side,
      radius,
      number,
      fillColor,
      strokeColor,
      textColor
    );
    this.isMoving = false;
    this.alpha = 1;
    this.scale = 1;
  }

  setProperties(x, y, side, radius, number, fillColor, strokeColor, textColor) {
    this.x = x;
    this.y = y;
    this.targetX = x;
    this.targetY = y;
    this.baseSide = side;
    this.baseRadius = radius;
    this.number = number;
    this.originalFillColor = fillColor;
    this.fillColor = fillColor;
    this.strokeColor = strokeColor;
    this.textColor = textColor;
    this.moveSpeed = 0.05;
  }

  async animateProperties(properties, duration = 1000, easing = "easeInOut") {
    const startValues = {};
    const targetValues = {};

    for (const [key, value] of Object.entries(properties)) {
      if (key === "color") {
        startValues[key] = this.fillColor;
        targetValues[key] = value;
      } else if (key === "alpha") {
        startValues[key] = this.alpha;
        targetValues[key] = value;
      } else if (key === "scale") {
        startValues[key] = this.scale;
        targetValues[key] = value;
      } else if (key === "position") {
        startValues[key] = { x: this.x, y: this.y };
        targetValues[key] = value;
      }
    }

    return AnimationManager.animate(
      (progress) => {
        for (const [key, startValue] of Object.entries(startValues)) {
          if (key === "color") {
            this.fillColor = AnimationManager.lerpColor(
              startValue,
              targetValues[key],
              progress
            );
          } else if (key === "alpha") {
            this.alpha = AnimationManager.lerp(
              startValue,
              targetValues[key],
              progress
            );
          } else if (key === "scale") {
            this.scale = AnimationManager.lerp(
              startValue,
              targetValues[key],
              progress
            );
          } else if (key === "position") {
            this.x = AnimationManager.lerp(
              startValue.x,
              targetValues[key].x,
              progress
            );
            this.y = AnimationManager.lerp(
              startValue.y,
              targetValues[key].y,
              progress
            );
          }
        }
      },
      duration,
      easing
    );
  }

  async highlight(color = "#8888ff", duration = 500) {
    const originalColor = this.fillColor;
    await this.animateProperties({ color }, duration / 2, "easeInOut");
    await this.animateProperties(
      { color: originalColor },
      duration / 2,
      "easeInOut"
    );
  }

  async fade(type = "in", duration = 1000) {
    const targetAlpha = type === "in" ? 1 : 0;
    return this.animate({ alpha: targetAlpha }, duration);
  }

  async changeColor(targetColor, duration = 1000) {
    return this.animateProperties({ color: targetColor }, duration);
  }

  async moveTo(targetX, targetY, speed = 0.05) {
    this.targetX = targetX;
    this.targetY = targetY;
    this.moveSpeed = speed;
    this.isMoving = true;

    return new Promise((resolve) => {
      const checkMovement = () => {
        if (!this.isMoving) {
          resolve();
        } else {
          requestAnimationFrame(checkMovement);
        }
      };
      checkMovement();
    });
  }

  update() {
    if (this.isMoving) {
      const dx = this.targetX - this.x;
      const dy = this.targetY - this.y;

      const speedFactor = 0.2;
      this.x += dx * this.moveSpeed * speedFactor;
      this.y += dy * this.moveSpeed * speedFactor;

      if (Math.abs(dx) < 2 && Math.abs(dy) < 2) {
        this.x = this.targetX;
        this.y = this.targetY;
        this.isMoving = false;
      }
    }
  }

  draw(ctx) {
    ctx.save();
    ctx.globalAlpha = this.alpha;

    const side = this.getScaledSide();
    const radius = this.getScaledRadius();

    this.drawRoundedRect(ctx, side, radius);
    this.drawNumber(ctx, side);

    ctx.restore();
  }

  getScaledSide() {
    return this.baseSide * this.scale;
  }

  getScaledRadius() {
    return this.baseRadius * this.scale;
  }

  drawRoundedRect(ctx, side, radius) {
    ctx.beginPath();
    ctx.moveTo(this.x + radius, this.y);
    ctx.lineTo(this.x + side - radius, this.y);
    ctx.arcTo(this.x + side, this.y, this.x + side, this.y + radius, radius);
    ctx.lineTo(this.x + side, this.y + side - radius);
    ctx.arcTo(
      this.x + side,
      this.y + side,
      this.x + side - radius,
      this.y + side,
      radius
    );
    ctx.lineTo(this.x + radius, this.y + side);
    ctx.arcTo(this.x, this.y + side, this.x, this.y + side - radius, radius);
    ctx.lineTo(this.x, this.y + radius);
    ctx.arcTo(this.x, this.y, this.x + radius, this.y, radius);
    ctx.closePath();

    ctx.fillStyle = this.fillColor;
    ctx.fill();
    ctx.strokeStyle = this.strokeColor;
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  drawNumber(ctx, side) {
    const numLength = this.number.toString().length;
    const fontSize = Math.max(
      12 * this.scale,
      (24 - (numLength - 1) * 2) * this.scale
    );

    ctx.font = `bold ${fontSize}px Arial`;
    ctx.fillStyle = this.textColor;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(this.number.toString(), this.x + side / 2, this.y + side / 2);
  }

  setPosition(x, y) {
    this.x = x;
    this.y = y;
    this.targetX = x;
    this.targetY = y;
    this.isMoving = false;
  }

  setScale(scale) {
    this.scale = scale;
  }

  setAlpha(alpha) {
    this.alpha = alpha;
  }

  setColor(color) {
    this.fillColor = color;
    this.originalFillColor = color;
  }

  resetColor() {
    this.fillColor = this.originalFillColor;
  }
}

class SquareLine {
  constructor(
    startX,
    startY,
    side,
    radius,
    numbersArray,
    spacing = 10,
    fillColor,
    strokeColor,
    textColor
  ) {
    this.setBaseProperties(
      startX,
      startY,
      side,
      radius,
      spacing,
      fillColor,
      strokeColor,
      textColor
    );
    this.numbers = numbersArray || [];
    this.squares = [];
    this.scale = 1;
    this.id = this.generateId();
    this.createSquares();
  }

  setBaseProperties(
    startX,
    startY,
    side,
    radius,
    spacing,
    fillColor,
    strokeColor,
    textColor
  ) {
    this.startX = startX;
    this.startY = startY;
    this.x = startX;
    this.y = startY;
    this.baseSide = side;
    this.baseRadius = radius;
    this.baseSpacing = spacing;
    this.fillColor = fillColor;
    this.strokeColor = strokeColor;
    this.textColor = textColor;
  }

  generateId() {
    return `line-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  createSquares() {
    this.squares = [];
    let currentX = this.startX;

    this.numbers.forEach((number) => {
      const square = new Square(
        currentX,
        this.startY,
        this.baseSide,
        this.baseRadius,
        number,
        this.fillColor,
        this.strokeColor,
        this.textColor
      );
      square.setScale(this.scale);
      this.squares.push(square);
      currentX += this.getScaledSide() + this.getScaledSpacing();
    });
  }

  async animateProperties(properties, duration = 1000, easing = "easeInOut") {
    const animations = this.squares.map((square) =>
      square.animateProperties(properties, duration, easing)
    );
    return Promise.all(animations);
  }

  async fade(type = "in", duration = 1000) {
    const targetAlpha = type === "in" ? 1 : 0;
    return this.animateProperties({ alpha: targetAlpha }, duration);
  }

  async fadeIn(duration = 1000) {
    return this.animateProperties({ alpha: 1 }, duration);
  }

  async fadeOut(duration = 1000) {
    return this.animateProperties({ alpha: 0 }, duration);
  }

  async changeColor(targetColor, duration = 1000) {
    return this.animateProperties({ color: targetColor }, duration);
  }

  async highlight(color = "#8888ff", duration = 500) {
    const animations = this.squares.map((square) =>
      square.highlight(color, duration)
    );
    return Promise.all(animations);
  }

  async highlightElements(indices, color = "#8888ff", duration = 500) {
    const animations = indices.map((index) => {
      if (index >= 0 && index < this.squares.length) {
        return this.squares[index].highlight(color, duration);
      }
      return Promise.resolve();
    });
    return Promise.all(animations);
  }

  async moveTo(x, y, speed = 0.05) {
    const deltaX = x - this.startX;
    const deltaY = y - this.startY;

    this.startX = x;
    this.startY = y;
    this.x = x;
    this.y = y;

    const movePromises = this.squares.map((square) => {
      const targetX = square.x + deltaX;
      const targetY = square.y + deltaY;
      return square.moveTo(targetX, targetY, speed);
    });

    return Promise.all(movePromises);
  }

  getScaledSide() {
    return this.baseSide * this.scale;
  }

  getScaledSpacing() {
    return this.baseSpacing * this.scale;
  }

  draw(ctx) {
    this.squares.forEach((square) => square.draw(ctx));
  }

  update() {
    this.squares.forEach((square) => square.update());
  }

  setScale(scale) {
    this.scale = scale;
    this.squares.forEach((square) => square.setScale(scale));
    this.createSquares();
  }

  setAlpha(alpha) {
    this.squares.forEach((square) => square.setAlpha(alpha));
  }

  getSquareAtPosition(index) {
    if (index >= 0 && index < this.squares.length) {
      return this.squares[index];
    }
    return null;
  }

  getTotalWidth() {
    if (this.numbers.length === 0) return 0;
    return (
      this.numbers.length * this.getScaledSide() +
      (this.numbers.length - 1) * this.getScaledSpacing()
    );
  }
}

export { Square, SquareLine, AnimationManager };
