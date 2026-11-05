(() => {
  "use strict";

  const VIRTUAL_W = 1280;
  const VIRTUAL_H = 720;
  const canvas = document.getElementById("gameCanvas");
  const ctx = canvas.getContext("2d");

  // --- Web Audio API SoundFX ---
  class SoundFX {
    constructor() {
      this.ctx = null;
      this.buffers = {};
    }

    ensureContext() {
      if (!this.ctx) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) {
          this.ctx = new AudioCtx();
          this.buildBuffers();
        }
      }
      if (this.ctx && this.ctx.state === "suspended") {
        this.ctx.resume().catch(() => {});
      }
    }

    buildBuffers() {
      if (!this.ctx) return;
      this.buffers["select"] = this.makeTone([660], 0.065, 0.45);
      this.buffers["swap"] = this.makeTone([440, 554], 0.06, 0.45);
      this.buffers["shuffle"] = this.makeTone([330, 440, 554, 660], 0.055, 0.45);
      this.buffers["tick"] = this.makeTone([880], 0.055, 0.38);
      this.buffers["levelup"] = this.makeTone([523, 659, 784, 1046], 0.09, 0.55);
      this.buffers["gameover"] = this.makeTone([659, 587, 523, 392], 0.12, 0.55);
      this.buffers["zap"] = this.makeTone([1320, 988, 1568, 784, 1760], 0.05, 0.55);
      this.buffers["rainbow"] = this.makeTone([523, 659, 784, 988, 1175, 1318, 1568], 0.05, 0.55);
      this.buffers["bomb"] = this.makeBombSound(0.35, 0.65);
      for (let combo = 1; combo <= 7; combo++) {
        const base = 440 * Math.pow(1.12, combo - 1);
        this.buffers[`match_${combo}`] = this.makeTone([base, base * 1.25, base * 1.5], 0.07, 0.52);
      }
    }

    makeTone(freqs, durationPerNote, volume = 0.45) {
      const sr = this.ctx.sampleRate;
      const nPerNote = Math.floor(sr * durationPerNote);
      const total = nPerNote * freqs.length;
      const buffer = this.ctx.createBuffer(1, total, sr);
      const data = buffer.getChannelData(0);
      let idx = 0;
      for (const freq of freqs) {
        for (let i = 0; i < nPerNote; i++) {
          const t = i / sr;
          const env = Math.pow(1.0 - i / Math.max(1, nPerNote), 0.8);
          const wave = 0.75 * Math.sin(2 * Math.PI * freq * t) + 0.25 * Math.sin(4 * Math.PI * freq * t);
          data[idx++] = Math.max(-1, Math.min(1, volume * env * wave));
        }
      }
      return buffer;
    }

    makeBombSound(duration = 0.35, volume = 0.65) {
      const sr = this.ctx.sampleRate;
      const total = Math.floor(sr * duration);
      const buffer = this.ctx.createBuffer(1, total, sr);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < total; i++) {
        const t = i / sr;
        const prog = 1.0 - i / Math.max(1, total);
        const env = Math.pow(prog, 1.4);
        const freq = 150.0 * Math.pow(prog, 0.7) + 38.0;
        const boom = Math.sin(2 * Math.PI * freq * t);
        const noise = (Math.random() * 1.3 - 0.65) * Math.pow(prog, 2.0);
        data[i] = Math.max(-1, Math.min(1, volume * env * (0.72 * boom + 0.28 * noise)));
      }
      return buffer;
    }

    play(name) {
      this.ensureContext();
      if (!this.ctx || !this.buffers[name]) return;
      try {
        const src = this.ctx.createBufferSource();
        src.buffer = this.buffers[name];
        src.connect(this.ctx.destination);
        src.start(0);
      } catch (_) {}
    }

    playMatch(combo) {
      const idx = Math.max(1, Math.min(7, combo));
      this.play(`match_${idx}`);
    }
  }

  // --- HighScoreManager ---
  const HighScoreManager = {
    KEY: "flowers_highscores_v1",
    loadScores() {
      try {
        const raw = localStorage.getItem(this.KEY);
        if (!raw) return [];
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          return parsed
            .map((x) => Math.floor(Number(x)))
            .filter((x) => x > 0)
            .sort((a, b) => b - a)
            .slice(0, 5);
        }
      } catch (_) {}
      return [];
    },
    saveScoresList(scores) {
      const clean = scores
        .map((x) => Math.floor(Number(x)))
        .filter((x) => x > 0)
        .sort((a, b) => b - a)
        .slice(0, 5);
      try {
        localStorage.setItem(this.KEY, JSON.stringify(clean));
      } catch (_) {}
      return clean;
    }
  };

  // --- Helper functions ---
  function rgba(r, g, b, a = 1) {
    return `rgba(${r | 0}, ${g | 0}, ${b | 0}, ${a})`;
  }

  function roundRectPath(c, x, y, w, h, r) {
    const rad = Math.min(r, w * 0.5, h * 0.5);
    c.beginPath();
    c.moveTo(x + rad, y);
    c.arcTo(x + w, y, x + w, y + h, rad);
    c.arcTo(x + w, y + h, x, y + h, rad);
    c.arcTo(x, y + h, x, y, rad);
    c.arcTo(x, y, x + w, y, rad);
    c.closePath();
  }

  function loadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = src;
    });
  }

  function createOffscreen(w, h) {
    const c = document.createElement("canvas");
    c.width = w;
    c.height = h;
    return c;
  }

  function keyWhiteAndScale(img, targetW, targetH, keyWhite) {
    const raw = createOffscreen(img.width, img.height);
    const rctx = raw.getContext("2d");
    rctx.drawImage(img, 0, 0);
    if (keyWhite) {
      const imgData = rctx.getImageData(0, 0, raw.width, raw.height);
      const d = imgData.data;
      for (let i = 0; i < d.length; i += 4) {
        if (255 - d[i] <= 22 && 255 - d[i + 1] <= 22 && 255 - d[i + 2] <= 26) {
          d[i + 3] = 0;
        }
      }
      rctx.putImageData(imgData, 0, 0);
    }
    const scaled = createOffscreen(targetW, targetH);
    const sctx = scaled.getContext("2d");
    sctx.drawImage(raw, 0, 0, targetW, targetH);
    return scaled;
  }

  function muteCanvas(srcCanvas, alphaMul = 1.0) {
    const out = createOffscreen(srcCanvas.width, srcCanvas.height);
    const octx = out.getContext("2d");
    octx.drawImage(srcCanvas, 0, 0);
    const imgData = octx.getImageData(0, 0, out.width, out.height);
    const d = imgData.data;
    for (let i = 0; i < d.length; i += 4) {
      const r = d[i], g = d[i + 1], b = d[i + 2];
      const gray = 0.299 * r + 0.587 * g + 0.114 * b;
      d[i] = Math.min(255, (r * 105 + gray * 88) / 255);
      d[i + 1] = Math.min(255, (g * 105 + gray * 88) / 255);
      d[i + 2] = Math.min(255, (b * 105 + gray * 88) / 255);
      d[i + 3] = Math.floor(d[i + 3] * alphaMul);
    }
    octx.putImageData(imgData, 0, 0);
    return out;
  }

  function extractSheetFlower(sheetImg, rx, ry, rw, rh, targetSize) {
    const sub = createOffscreen(rw, rh);
    const sctx = sub.getContext("2d");
    sctx.drawImage(sheetImg, rx, ry, rw, rh, 0, 0, rw, rh);
    const data = sctx.getImageData(0, 0, rw, rh).data;
    let minX = rw, minY = rh, maxX = -1, maxY = -1;
    for (let y = 0; y < rh; y++) {
      for (let x = 0; x < rw; x++) {
        const a = data[(y * rw + x) * 4 + 3];
        if (a > 8) {
          if (x < minX) minX = x;
          if (x > maxX) maxX = x;
          if (y < minY) minY = y;
          if (y > maxY) maxY = y;
        }
      }
    }
    const out = createOffscreen(targetSize, targetSize);
    const octx = out.getContext("2d");
    if (maxX < minX || maxY < minY) {
      octx.drawImage(sub, 0, 0, targetSize, targetSize);
      return out;
    }
    const bw = maxX - minX + 1;
    const bh = maxY - minY + 1;
    const side = Math.max(bw, bh);
    const sq = createOffscreen(side, side);
    const sqCtx = sq.getContext("2d");
    sqCtx.drawImage(sub, minX, minY, bw, bh, Math.floor((side - bw) / 2), Math.floor((side - bh) / 2), bw, bh);
    octx.drawImage(sq, 0, 0, targetSize, targetSize);
    return out;
  }

  // --- ScreenShader ---
  class ScreenShader {
    constructor() {
      this.width = VIRTUAL_W;
      this.height = VIRTUAL_H;
      const palette = [
        [255, 220, 130],
        [255, 160, 220],
        [160, 220, 255],
        [190, 255, 180]
      ];
      this.particles = Array.from({ length: 45 }, () => ({
        x: Math.random() * VIRTUAL_W,
        y: Math.random() * VIRTUAL_H,
        speed: 0.6 + Math.random() * 1.2,
        radius: 3.0 + Math.random() * 4.0,
        phase: Math.random() * Math.PI * 2,
        color: palette[Math.floor(Math.random() * palette.length)]
      }));
    }

    drawParallaxBackground(ticks, mouseX, mouseY, cloudsList, muted = true) {
      const layers = muted ? assets.parallaxMuted : assets.parallaxVibrant;
      if (!layers.length) return;
      const t = ticks * 0.0012;
      const normX = (mouseX - this.width * 0.5) / (this.width * 0.5);
      const normY = (mouseY - this.height * 0.5) / (this.height * 0.5);
      const driftX = Math.sin(t) * 18.0;
      const driftY = Math.cos(t * 0.8) * 8.0;

      let activeClouds = cloudsList;
      if (!activeClouds && assets.cloudsMuted.length) {
        const sec = ticks * 0.06;
        const specs = [
          [40.0, 22.0, 0.42, 420.0, 0.0],
          [460.0, 135.0, 0.19, 260.0, 2.1],
          [940.0, 72.0, 0.30, 320.0, 4.2]
        ];
        activeClouds = assets.cloudsMuted.map((csurf, idx) => {
          const [bx, by, spd, pad, phase] = specs[Math.min(idx, specs.length - 1)];
          const span = 1380.0 + pad;
          const breeze = Math.sin(t * 0.55 + phase) * 18.0;
          const cx = (((bx + sec * spd + breeze + pad) % span) + span) % span - pad;
          const cy = by + Math.sin(t * 0.85 + phase) * 5.0;
          return [csurf, [cx, cy]];
        });
      }

      const cloudParallax = [[0.38, 0.28], [0.24, 0.18], [0.31, 0.23]];
      const parallaxFactors = [[0.2, 0.15], [0.55, 0.4], [1.0, 0.75]];

      for (let idx = 0; idx < layers.length; idx++) {
        const [fx, fy] = parallaxFactors[Math.min(idx, parallaxFactors.length - 1)];
        const ox = Math.floor(-40 - (normX * 22.0 + driftX) * fx);
        const oy = Math.floor(-22 - (normY * 14.0 + driftY) * fy);
        ctx.drawImage(layers[idx], ox, oy);
        if (idx === 0 && activeClouds) {
          for (let cIdx = 0; cIdx < activeClouds.length; cIdx++) {
            const [cloudSurf, cloudXY] = activeClouds[cIdx];
            const [cfx, cfy] = cloudParallax[Math.min(cIdx, cloudParallax.length - 1)];
            const cox = Math.floor(cloudXY[0] - (normX * 22.0 + driftX) * cfx);
            const coy = Math.floor(cloudXY[1] - (normY * 14.0 + driftY) * cfy);
            ctx.drawImage(cloudSurf, cox, coy);
          }
        }
      }

      if (muted) {
        ctx.fillStyle = rgba(24, 28, 42, 46 / 255);
        ctx.fillRect(0, 0, this.width, this.height);
      }
    }

    drawAtmosphere(ticks) {
      const t = ticks * 0.003;
      for (let i = 0; i < 5; i++) {
        const beamX = 200 + i * 240 + Math.sin(t + i) * 60;
        const beamAlpha = (18 + 12 * Math.sin(t * 1.3 + i)) / 255;
        ctx.fillStyle = rgba(255, 245, 200, Math.max(0.02, beamAlpha));
        ctx.beginPath();
        ctx.moveTo(beamX - 60, 0);
        ctx.lineTo(beamX + 60, 0);
        ctx.lineTo(beamX + 220, this.height);
        ctx.lineTo(beamX - 20, this.height);
        ctx.closePath();
        ctx.fill();
      }

      for (const p of this.particles) {
        p.y -= p.speed;
        p.x += Math.sin(t * 1.2 + p.phase) * 0.8;
        if (p.y < -20) {
          p.y = this.height + 20;
          p.x = Math.random() * this.width;
        }
        const glowAlpha = Math.max(10, Math.min(255, 90 + 80 * Math.sin(t * 2.0 + p.phase)));
        const [r, g, b] = p.color;
        ctx.fillStyle = rgba(r, g, b, (glowAlpha / 3) / 255);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius * 2.4, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = rgba(r, g, b, glowAlpha / 255);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = rgba(255, 255, 255, 210 / 255);
        ctx.beginPath();
        ctx.arc(p.x, p.y, Math.max(1, p.radius * 0.45), 0, Math.PI * 2);
        ctx.fill();
      }
    }

    drawGlowPanel(ticks, x, y, w, h, hovered = false) {
      const t = ticks * 0.003;
      const pulse = (Math.sin(t * 1.5) + 1.0) * 0.5;
      const bgAlpha = (hovered ? 200 : 160) / 255;

      ctx.fillStyle = rgba(35, 20, 80, bgAlpha);
      roundRectPath(ctx, x, y, w, h, 20);
      ctx.fill();

      ctx.lineWidth = 3;
      for (let layer = 4; layer >= 1; layer--) {
        const spread = layer * 3;
        const a = (((hovered ? 45 : 25) * (5 - layer)) / 4) / 255;
        ctx.strokeStyle = rgba(190, 130, 255, a);
        roundRectPath(ctx, x - spread, y - spread, w + spread * 2, h + spread * 2, 20 + spread);
        ctx.stroke();
      }

      ctx.strokeStyle = hovered
        ? rgba(255, 230, 150, 1)
        : rgba(200, 165, 255, (190 + 60 * pulse) / 255);
      roundRectPath(ctx, x, y, w, h, 20);
      ctx.stroke();
    }

    drawGlowText(fontSize, text, x, y, {
      mainColor = [245, 235, 255],
      glowColor = [95, 45, 190],
      offset = 2,
      maxWidth = null,
      centerWidth = null,
      alpha = 1.0
    } = {}) {
      ctx.save();
      let size = fontSize;
      ctx.font = `${size}px "GameFont", sans-serif`;
      ctx.textBaseline = "top";
      let measured = ctx.measureText(text).width;
      if (maxWidth !== null && measured > maxWidth && measured > 0) {
        size = Math.max(8, size * (maxWidth / measured));
        ctx.font = `${size}px "GameFont", sans-serif`;
        measured = ctx.measureText(text).width;
      }
      const drawX = centerWidth !== null ? x + (centerWidth - measured) * 0.5 : x;
      const drawY = y;

      ctx.fillStyle = rgba(glowColor[0], glowColor[1], glowColor[2], alpha);
      const offsets = [
        [-offset, 0], [offset, 0], [0, -offset], [0, offset],
        [-offset + 1, -offset + 1], [offset - 1, -offset + 1],
        [-offset + 1, offset - 1], [offset - 1, offset - 1]
      ];
      for (const [ox, oy] of offsets) {
        ctx.fillText(text, drawX + ox, drawY + oy);
      }
      ctx.fillStyle = rgba(mainColor[0], mainColor[1], mainColor[2], alpha);
      ctx.fillText(text, drawX, drawY);
      ctx.restore();
    }
  }

  // --- Global Assets & State ---
  const sound = new SoundFX();
  const shader = new ScreenShader();
  const assets = {
    ready: false,
    normalFlowers: {},
    bombFlowers: {},
    zapFlowers: {},
    parallaxVibrant: [],
    parallaxMuted: [],
    cloudsVibrant: [],
    cloudsMuted: []
  };

  const COLOR_NAMES = ["red", "blue", "purple", "yellow", "green", "orange"];
  const COLOR_MAP = {
    red: [255, 90, 90],
    blue: [90, 175, 255],
    green: [95, 235, 125],
    purple: [195, 110, 255],
    yellow: [255, 230, 95],
    orange: [255, 155, 70]
  };
  const TITLE_PALETTE = [
    [[245, 235, 255], [95, 45, 190]],
    [[255, 235, 130], [195, 95, 20]],
    [[140, 245, 255], [25, 105, 195]],
    [[255, 155, 220], [175, 30, 120]],
    [[155, 255, 175], [25, 145, 65]],
    [[255, 165, 135], [185, 45, 30]]
  ];
  const BOARD_PULSE_PALETTE = [
    [[165, 95, 255], [38, 18, 72]],
    [[70, 225, 255], [14, 48, 68]],
    [[255, 115, 200], [68, 18, 52]],
    [[105, 250, 170], [16, 58, 38]],
    [[255, 205, 95], [68, 46, 14]],
    [[255, 125, 110], [68, 22, 22]]
  ];

  const BOARD_ROW = 8;
  const BOARD_COL = 10;
  const CELL_SIZE = 75;
  const FLOWER_SIZE = 60;
  const BOARD_START_X = 80;
  const BOARD_START_Y = 60;

  let gameMode = "MainMenu";
  let mouseX = 640;
  let mouseY = 360;

  // Clouds for MainMenu / EndScreen
  let cloud1XY = [40, 22];
  let cloud2XY = [460, 135];
  let cloud3XY = [940, 72];

  // MainMenu state
  let titleColorIndex = 0;
  let titleRect = { x: 440, y: 20, w: 400, h: 105 };
  let titleClickTimes = [];
  let showCreditsModal = false;
  let creditsUrlRect = { x: 420, y: 375, w: 440, h: 48 };
  let highScores = HighScoreManager.loadScores();

  // GameScreen state
  let board = [];
  let flowersSelected = [];
  let dragStartCell = null;
  let animData = null;
  let isFalling = false;
  let userFirstMove = false;
  let userScore = 0;
  let finalScore = 0;
  let bestScore = 0;
  let previousHighScores = [];
  let comboCount = 0;
  let level = 1;
  let levelTarget = 1500;
  let currentTime = 180;
  let lastSecondTick = performance.now();
  let shufflesLeft = 3;
  let showHowToPlay = true;
  let lastActionTime = performance.now();
  let hintPair = null;
  let isTimeOver = false;
  let timeOverStart = 0;
  let screenShake = 0;

  const shuffleBtnRect = { x: 875, y: 515, w: 355, h: 58 };
  const helpBtnRect = { x: 875, y: 595, w: 355, h: 58 };
  const howToPlayCloseRect = { x: 410, y: 580, w: 460, h: 62 };

  let burstParticles = [];
  let floatingTexts = [];
  let specialEffects = [];
  let timeOverFlowers = [];
  let matchesFound = [];

  function ptInRect(px, py, r) {
    return px >= r.x && px <= r.x + r.w && py >= r.y && py <= r.y + r.h;
  }

  function cellToXY(r, c) {
    const pad = (CELL_SIZE - FLOWER_SIZE) * 0.5;
    return [BOARD_START_X + c * CELL_SIZE + pad, BOARD_START_Y + r * CELL_SIZE + pad];
  }

  function getFlowerSurf(name, special = null) {
    if (special === "bomb" && assets.bombFlowers[name]) return assets.bombFlowers[name];
    if ((special === "zap" || special === "line") && assets.zapFlowers[name]) return assets.zapFlowers[name];
    return assets.normalFlowers[name];
  }

  function createFlower(x, y, special = null) {
    const name = COLOR_NAMES[Math.floor(Math.random() * COLOR_NAMES.length)];
    return {
      name,
      x,
      y,
      targetX: x,
      targetY: y,
      surf: getFlowerSurf(name, special),
      special
    };
  }

  function hasMatch() {
    for (let r = 0; r < BOARD_ROW - 2; r++) {
      for (let c = 0; c < BOARD_COL; c++) {
        const n = board[r][c].name;
        if (board[r + 1][c].name === n && board[r + 2][c].name === n) return true;
      }
    }
    for (let c = 0; c < BOARD_COL - 2; c++) {
      for (let r = 0; r < BOARD_ROW; r++) {
        const n = board[r][c].name;
        if (board[r][c + 1].name === n && board[r][c + 2].name === n) return true;
      }
    }
    return false;
  }

  function findHintMove() {
    const dirs = [[0, 1], [1, 0], [1, 1], [1, -1]];
    for (let r = 0; r < BOARD_ROW; r++) {
      for (let c = 0; c < BOARD_COL; c++) {
        for (const [dr, dc] of dirs) {
          const nr = r + dr, nc = c + dc;
          if (nr >= 0 && nr < BOARD_ROW && nc >= 0 && nc < BOARD_COL) {
            const tmp = board[r][c];
            board[r][c] = board[nr][nc];
            board[nr][nc] = tmp;
            const matched = hasMatch();
            board[nr][nc] = board[r][c];
            board[r][c] = tmp;
            if (matched) return [[r, c], [nr, nc]];
          }
        }
      }
    }
    return null;
  }

  function checkBoard() {
    for (let r = 0; r < BOARD_ROW - 2; r++) {
      for (let c = 0; c < BOARD_COL; c++) {
        const n = board[r][c].name;
        if (board[r + 1][c].name === n && board[r + 2][c].name === n) {
          matchesFound.push([[r, c], [r + 1, c], [r + 2, c]]);
        }
      }
    }
    for (let c = 0; c < BOARD_COL - 2; c++) {
      for (let r = 0; r < BOARD_ROW; r++) {
        const n = board[r][c].name;
        if (board[r][c + 1].name === n && board[r][c + 2].name === n) {
          matchesFound.push([[r, c], [r, c + 1], [r, c + 2]]);
        }
      }
    }
  }

  function saveCurrentScore() {
    if (userScore > 0) {
      const updated = HighScoreManager.saveScoresList([...previousHighScores, userScore]);
      if (updated.length) bestScore = Math.max(bestScore, updated[0]);
    }
  }

  function addFloatingText(text, x, y, color = [255, 240, 150]) {
    ctx.save();
    ctx.font = '30px "GameFont", sans-serif';
    const w = ctx.measureText(text).width;
    ctx.restore();
    const h = 34;
    const padX = 14, padY = 6;
    const fx = Math.max(BOARD_START_X, Math.min(x, BOARD_START_X + BOARD_COL * CELL_SIZE - w - 8));
    let fy = y;
    for (let i = 0; i < floatingTexts.length + 2; i++) {
      let collided = false;
      for (const other of floatingTexts) {
        if (
          Math.abs(fx - other.x) < w + padX &&
          Math.abs(fy - other.y) < h + padY
        ) {
          fy = other.y - h - padY;
          collided = true;
          break;
        }
      }
      if (!collided) break;
    }
    if (fy < 16) fy = y;
    floatingTexts.push({ text, x: fx, y: fy, alpha: 380, color });
  }

  function spawnBurst(x, y, colorName) {
    const col = COLOR_MAP[colorName] || [255, 220, 150];
    const cx = x + FLOWER_SIZE * 0.5;
    const cy = y + FLOWER_SIZE * 0.5;
    for (let i = 0; i < 12; i++) {
      const ang = Math.random() * Math.PI * 2;
      const spd = 2.0 + Math.random() * 4.5;
      burstParticles.push({
        x: cx,
        y: cy,
        vx: Math.cos(ang) * spd,
        vy: Math.sin(ang) * spd - 1.5,
        radius: 4.0 + Math.random() * 4.0,
        alpha: 255,
        col
      });
    }
  }

  function spawnZapShader(r, c) {
    sound.play("zap");
    const [fx, fy] = cellToXY(r, c);
    const cx = fx + FLOWER_SIZE * 0.5;
    const cy = fy + FLOWER_SIZE * 0.5;
    specialEffects.push({ type: "zap", r, c, cx, cy, timer: 0, maxTimer: 24 });
    const cols = [[255, 250, 110], [130, 245, 255], [255, 255, 230]];
    for (let i = 0; i < 28; i++) {
      let px, py, vx, vy;
      if (Math.random() < 0.5) {
        px = BOARD_START_X + Math.random() * (BOARD_COL * CELL_SIZE);
        py = cy + (Math.random() * 20 - 10);
        vx = (Math.random() < 0.5 ? -1 : 1) * (3 + Math.random() * 6);
        vy = Math.random() * 4.4 - 2.2;
      } else {
        px = cx + (Math.random() * 20 - 10);
        py = BOARD_START_Y + Math.random() * (BOARD_ROW * CELL_SIZE);
        vx = Math.random() * 4.4 - 2.2;
        vy = (Math.random() < 0.5 ? -1 : 1) * (3 + Math.random() * 6);
      }
      burstParticles.push({
        x: px,
        y: py,
        vx,
        vy,
        radius: 3.5 + Math.random() * 3.0,
        alpha: 255,
        col: cols[Math.floor(Math.random() * cols.length)]
      });
    }
  }

  function spawnRainbowShader(r, c, targetCells) {
    sound.play("rainbow");
    const [fx, fy] = cellToXY(r, c);
    const cx = fx + FLOWER_SIZE * 0.5;
    const cy = fy + FLOWER_SIZE * 0.5;
    const rainbowCols = [
      [255, 95, 120], [255, 175, 85], [255, 240, 100],
      [110, 245, 150], [95, 220, 255], [175, 130, 255], [255, 120, 225]
    ];
    const targets = [];
    for (const [tr, tc] of targetCells) {
      const [tx, ty] = cellToXY(tr, tc);
      const tcx = tx + FLOWER_SIZE * 0.5;
      const tcy = ty + FLOWER_SIZE * 0.5;
      targets.push([tcx, tcy]);
      for (let i = 0; i < 8; i++) {
        const ang = Math.random() * Math.PI * 2;
        const spd = 2.5 + Math.random() * 4.5;
        burstParticles.push({
          x: tcx,
          y: tcy,
          vx: Math.cos(ang) * spd,
          vy: Math.sin(ang) * spd - 1.2,
          radius: 4.5 + Math.random() * 3.5,
          alpha: 255,
          col: rainbowCols[Math.floor(Math.random() * rainbowCols.length)]
        });
      }
    }
    specialEffects.push({ type: "rainbow", cx, cy, targets, timer: 0, maxTimer: 30 });
  }

  function spawnBombShader(r, c, r0, c0) {
    sound.play("bomb");
    const [fx, fy] = cellToXY(r, c);
    const cx = fx + FLOWER_SIZE * 0.5;
    const cy = fy + FLOWER_SIZE * 0.5;
    const bx = BOARD_START_X + c0 * CELL_SIZE;
    const by = BOARD_START_Y + r0 * CELL_SIZE;
    const bw = Math.min(5, BOARD_COL - c0) * CELL_SIZE;
    const bh = Math.min(5, BOARD_ROW - r0) * CELL_SIZE;
    screenShake = Math.max(screenShake, 10.0);
    specialEffects.push({ type: "bomb", cx, cy, rect: [bx, by, bw, bh], timer: 0, maxTimer: 28 });
    const fireCols = [[255, 120, 60], [255, 210, 80], [255, 90, 185], [255, 245, 200]];
    for (let i = 0; i < 42; i++) {
      const ang = Math.random() * Math.PI * 2;
      const spd = 3.0 + Math.random() * 8.5;
      burstParticles.push({
        x: cx + (Math.random() * 36 - 18),
        y: cy + (Math.random() * 36 - 18),
        vx: Math.cos(ang) * spd,
        vy: Math.sin(ang) * spd - 1.5,
        radius: 5.5 + Math.random() * 5.0,
        alpha: 255,
        col: fireCols[Math.floor(Math.random() * fireCols.length)]
      });
    }
  }

  function deleteAndReplaceFlowers(instant = false) {
    if (!matchesFound.length) {
      if (!instant) comboCount = 0;
      return;
    }
    const seen = new Set();
    const orderedPositions = [];
    for (const matchItem of matchesFound) {
      for (const [r, c] of matchItem) {
        const key = `${r},${c}`;
        if (!seen.has(key)) {
          seen.add(key);
          orderedPositions.push([r, c]);
        }
      }
    }
    matchesFound = [];

    const expanded = [...orderedPositions];
    const expandedSet = new Set(orderedPositions.map(([r, c]) => `${r},${c}`));
    const addExpanded = (rr, cc) => {
      const k = `${rr},${cc}`;
      if (!expandedSet.has(k)) {
        expandedSet.add(k);
        expanded.push([rr, cc]);
      }
    };

    for (const [r, c] of orderedPositions) {
      const fl = board[r][c];
      if (!fl) continue;
      if (fl.special === "zap" || fl.special === "line") {
        if (!instant && userFirstMove) spawnZapShader(r, c);
        for (let cc = 0; cc < BOARD_COL; cc++) addExpanded(r, cc);
        for (let rr = 0; rr < BOARD_ROW; rr++) addExpanded(rr, c);
      } else if (fl.special === "bomb") {
        const r0 = Math.max(0, Math.min(BOARD_ROW - 5, r - 2));
        const c0 = Math.max(0, Math.min(BOARD_COL - 5, c - 2));
        if (!instant && userFirstMove) spawnBombShader(r, c, r0, c0);
        for (let rr = r0; rr < Math.min(BOARD_ROW, r0 + 5); rr++) {
          for (let cc = c0; cc < Math.min(BOARD_COL, c0 + 5); cc++) {
            addExpanded(rr, cc);
          }
        }
      } else if (fl.special === "rainbow") {
        const targetColor = fl.name;
        const rainbowTargets = [];
        for (let rr = 0; rr < BOARD_ROW; rr++) {
          for (let cc = 0; cc < BOARD_COL; cc++) {
            if (board[rr][cc].name === targetColor) {
              rainbowTargets.push([rr, cc]);
              addExpanded(rr, cc);
            }
          }
        }
        if (!instant && userFirstMove) spawnRainbowShader(r, c, rainbowTargets);
      }
    }

    if (instant) {
      for (const [r, c] of expanded) {
        const [tx, ty] = cellToXY(r, c);
        board[r][c] = createFlower(tx, ty);
      }
      return;
    }

    const spawnPos = orderedPositions[0];
    const spawnColor = board[spawnPos[0]][spawnPos[1]].name;
    let spawnSpecial = null;
    if (orderedPositions.length >= 6) spawnSpecial = "bomb";
    else if (orderedPositions.length === 5) spawnSpecial = "rainbow";
    else if (orderedPositions.length === 4) spawnSpecial = "zap";

    if (userFirstMove) {
      comboCount += 1;
      sound.playMatch(comboCount);
      const pointsEarned = expanded.length * 100 * comboCount;
      userScore += pointsEarned;
      saveCurrentScore();

      const avgX = expanded.reduce((s, [r, c]) => s + board[r][c].x, 0) / expanded.length;
      const avgY = expanded.reduce((s, [r, c]) => s + board[r][c].y, 0) / expanded.length;
      const label = comboCount === 1 ? `+${pointsEarned}` : `+${pointsEarned} (${comboCount}x COMBO!)`;
      addFloatingText(label, avgX, avgY, [255, 245, 140]);

      const MAX_TIME = 3599;
      if (orderedPositions.length >= 5 && currentTime < MAX_TIME) {
        const addedBonus = Math.min(3, MAX_TIME - currentTime);
        currentTime += addedBonus;
        addFloatingText(`+${addedBonus}s TIME BONUS!`, avgX, avgY - 32, [150, 255, 190]);
      }

      if (userScore >= levelTarget) {
        level += 1;
        levelTarget += level * 1800;
        const addedLvl = Math.max(0, Math.min(15, MAX_TIME - currentTime));
        currentTime += addedLvl;
        shufflesLeft = Math.min(5, shufflesLeft + 1);
        sound.play("levelup");
        const lvlMsg = addedLvl > 0 ? `LEVEL ${level}! +${addedLvl}s` : `LEVEL ${level}!`;
        addFloatingText(lvlMsg, 380, 300, [255, 210, 255]);
      }
    }

    for (const [r, c] of expanded) {
      const fl = board[r][c];
      if (fl && userFirstMove) spawnBurst(fl.x, fl.y, fl.name);
      board[r][c] = null;
    }

    if (userFirstMove && spawnSpecial !== null) {
      const [sr, sc] = spawnPos;
      const [tx, ty] = cellToXY(sr, sc);
      board[sr][sc] = {
        name: spawnColor,
        x: tx,
        y: ty,
        targetX: tx,
        targetY: ty,
        surf: getFlowerSurf(spawnColor, spawnSpecial),
        special: spawnSpecial
      };
    }

    for (let c = 0; c < BOARD_COL; c++) {
      const remaining = [];
      for (let r = BOARD_ROW - 1; r >= 0; r--) {
        if (board[r][c]) remaining.push(board[r][c]);
      }
      const missingCount = BOARD_ROW - remaining.length;
      for (let i = 0; i < remaining.length; i++) {
        const targetR = BOARD_ROW - 1 - i;
        const [tx, ty] = cellToXY(targetR, c);
        remaining[i].targetX = tx;
        remaining[i].targetY = ty;
        board[targetR][c] = remaining[i];
      }
      for (let m = 0; m < missingCount; m++) {
        const targetR = missingCount - 1 - m;
        const [tx, ty] = cellToXY(targetR, c);
        const startY = BOARD_START_Y - (m + 1) * CELL_SIZE;
        const newFl = createFlower(tx, startY);
        newFl.targetX = tx;
        newFl.targetY = ty;
        board[targetR][c] = newFl;
      }
    }

    isFalling = true;
    hintPair = null;
    lastActionTime = performance.now();
  }

  function shuffleBoard() {
    sound.play("shuffle");
    const flat = board.flat();
    for (let attempt = 0; attempt < 20; attempt++) {
      for (let i = flat.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [flat[i], flat[j]] = [flat[j], flat[i]];
      }
      let idx = 0;
      for (let r = 0; r < BOARD_ROW; r++) {
        for (let c = 0; c < BOARD_COL; c++) {
          const f = flat[idx++];
          const [tx, ty] = cellToXY(r, c);
          f.x = tx;
          f.y = ty;
          f.targetX = tx;
          f.targetY = ty;
          board[r][c] = f;
        }
      }
      if (!hasMatch() && findHintMove()) break;
    }
    while (hasMatch()) {
      checkBoard();
      deleteAndReplaceFlowers(true);
    }
    flowersSelected = [];
    hintPair = null;
    lastActionTime = performance.now();
  }

  function resetGameScreen() {
    userScore = 0;
    userFirstMove = false;
    comboCount = 0;
    level = 1;
    levelTarget = 1500;
    currentTime = 180;
    shufflesLeft = 3;
    showHowToPlay = true;
    isTimeOver = false;
    screenShake = 0;
    animData = null;
    isFalling = false;
    flowersSelected = [];
    dragStartCell = null;
    hintPair = null;
    burstParticles = [];
    floatingTexts = [];
    specialEffects = [];
    timeOverFlowers = [];
    previousHighScores = HighScoreManager.loadScores();
    bestScore = previousHighScores.length ? previousHighScores[0] : 0;
    lastActionTime = performance.now();
    lastSecondTick = performance.now();

    board = Array.from({ length: BOARD_ROW }, (_, r) =>
      Array.from({ length: BOARD_COL }, (_, c) => {
        const [x, y] = cellToXY(r, c);
        return createFlower(x, y);
      })
    );
    while (hasMatch()) {
      checkBoard();
      deleteAndReplaceFlowers(true);
    }
  }

  function checkMove(pos1, pos2) {
    const [r1, c1] = pos1;
    const [r2, c2] = pos2;
    if (r1 === r2 && c1 === c2) return null;
    if (Math.max(Math.abs(r1 - r2), Math.abs(c1 - c2)) !== 1) return null;

    const f1 = board[r1][c1];
    const f2 = board[r2][c2];
    const [t1x, t1y] = cellToXY(r2, c2);
    const [t2x, t2y] = cellToXY(r1, c1);

    board[r1][c1] = f2;
    board[r2][c2] = f1;

    userFirstMove = true;
    comboCount = 0;
    hintPair = null;
    lastActionTime = performance.now();
    sound.play("swap");
    return { f1, f2, t1x, t1y, t2x, t2y };
  }

  function getCellAtPos(vx, vy) {
    if (vx < BOARD_START_X || vy < BOARD_START_Y) return null;
    const c = Math.floor((vx - BOARD_START_X) / CELL_SIZE);
    const r = Math.floor((vy - BOARD_START_Y) / CELL_SIZE);
    if (r >= 0 && r < BOARD_ROW && c >= 0 && c < BOARD_COL) return [r, c];
    return null;
  }

  function triggerTimeOver() {
    if (isTimeOver) return;
    currentTime = 0;
    isTimeOver = true;
    timeOverStart = performance.now();
    animData = null;
    isFalling = false;
    flowersSelected = [];
    hintPair = null;
    dragStartCell = null;
    saveCurrentScore();
    sound.play("gameover");

    timeOverFlowers = [];
    for (let r = 0; r < BOARD_ROW; r++) {
      for (let c = 0; c < BOARD_COL; c++) {
        const fl = board[r][c];
        if (!fl) continue;
        const delay = (BOARD_ROW - 1 - r) * 3 + Math.abs(c - 4.5) * 1.5 + Math.random() * 4;
        const vx = Math.random() * 7.2 - 3.6;
        const vy = -(1.5 + Math.random() * 3.7);
        const angVel = (Math.random() < 0.5 ? -1 : 1) * (3.5 + Math.random() * 6.0);
        timeOverFlowers.push({
          surf: fl.surf,
          x: fl.x,
          y: fl.y,
          vx,
          vy,
          angle: 0,
          angVel,
          delay,
          colorName: fl.name,
          launched: false
        });
      }
    }
  }

  function goToEndScreen() {
    saveCurrentScore();
    finalScore = userScore;
    highScores = HighScoreManager.loadScores();
    gameMode = "EndScreen";
  }

  // --- Input Handling ---
  function getCanvasCoords(clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    return [
      ((clientX - rect.left) / rect.width) * VIRTUAL_W,
      ((clientY - rect.top) / rect.height) * VIRTUAL_H
    ];
  }

  function onPointerDown(vx, vy) {
    sound.ensureContext();
    mouseX = vx;
    mouseY = vy;
    if (gameMode !== "GameScreen" || showHowToPlay || isTimeOver) return;
    if (!animData && !isFalling) {
      hintPair = null;
      lastActionTime = performance.now();
      if (ptInRect(vx, vy, shuffleBtnRect) && shufflesLeft > 0) {
        shufflesLeft -= 1;
        shuffleBoard();
      } else if (ptInRect(vx, vy, helpBtnRect)) {
        sound.play("select");
        showHowToPlay = true;
      } else {
        dragStartCell = getCellAtPos(vx, vy);
      }
    }
  }

  function onPointerMove(vx, vy) {
    mouseX = vx;
    mouseY = vy;
    if (gameMode === "GameScreen" && dragStartCell && !animData && !isFalling && !showHowToPlay && !isTimeOver) {
      const cur = getCellAtPos(vx, vy);
      if (cur && (cur[0] !== dragStartCell[0] || cur[1] !== dragStartCell[1])) {
        if (Math.max(Math.abs(cur[0] - dragStartCell[0]), Math.abs(cur[1] - dragStartCell[1])) === 1) {
          animData = checkMove(dragStartCell, cur);
          flowersSelected = [];
          dragStartCell = null;
        }
      }
    }
  }

  function onPointerUp(vx, vy) {
    sound.ensureContext();
    mouseX = vx;
    mouseY = vy;

    if (gameMode === "MainMenu") {
      if (showCreditsModal) {
        sound.play("select");
        if (ptInRect(vx, vy, creditsUrlRect)) {
          window.open("https://knrf.itch.io/", "_blank", "noopener");
        } else {
          showCreditsModal = false;
        }
        return;
      }
      if (ptInRect(vx, vy, titleRect)) {
        titleColorIndex = (titleColorIndex + 1) % TITLE_PALETTE.length;
        const now = performance.now();
        titleClickTimes = titleClickTimes.filter((ts) => now - ts <= 30000);
        titleClickTimes.push(now);
        if (titleClickTimes.length >= 10) {
          showCreditsModal = true;
          titleClickTimes = [];
          sound.play("levelup");
        } else {
          sound.play("select");
        }
      } else {
        sound.play("select");
        resetGameScreen();
        gameMode = "GameScreen";
      }
      return;
    }

    if (gameMode === "EndScreen") {
      sound.play("select");
      highScores = HighScoreManager.loadScores();
      gameMode = "MainMenu";
      return;
    }

    if (gameMode === "GameScreen") {
      if (showHowToPlay) {
        sound.play("select");
        showHowToPlay = false;
        lastActionTime = performance.now();
        lastSecondTick = performance.now();
        return;
      }
      if (isTimeOver) {
        if (performance.now() - timeOverStart > 1200) {
          goToEndScreen();
        }
        return;
      }
      hintPair = null;
      lastActionTime = performance.now();
      if (!animData && !isFalling && dragStartCell) {
        const clicked = getCellAtPos(vx, vy);
        if (clicked) {
          if (
            (clicked[0] !== dragStartCell[0] || clicked[1] !== dragStartCell[1]) &&
            Math.max(Math.abs(clicked[0] - dragStartCell[0]), Math.abs(clicked[1] - dragStartCell[1])) === 1
          ) {
            animData = checkMove(dragStartCell, clicked);
            flowersSelected = [];
          } else if (
            flowersSelected.length === 1 &&
            flowersSelected[0][0] === clicked[0] &&
            flowersSelected[0][1] === clicked[1]
          ) {
            flowersSelected = [];
          } else {
            sound.play("select");
            flowersSelected.push(clicked);
            if (flowersSelected.length === 2) {
              animData = checkMove(flowersSelected[0], flowersSelected[1]);
              if (!animData) {
                flowersSelected = [clicked];
              } else {
                flowersSelected = [];
              }
            }
          }
        }
      }
      dragStartCell = null;
    }
  }

  canvas.addEventListener("mousedown", (e) => {
    if (e.button === 0) onPointerDown(...getCanvasCoords(e.clientX, e.clientY));
  });
  window.addEventListener("mousemove", (e) => {
    onPointerMove(...getCanvasCoords(e.clientX, e.clientY));
  });
  window.addEventListener("mouseup", (e) => {
    if (e.button === 0) onPointerUp(...getCanvasCoords(e.clientX, e.clientY));
  });

  canvas.addEventListener("touchstart", (e) => {
    e.preventDefault();
    const t = e.changedTouches[0];
    onPointerDown(...getCanvasCoords(t.clientX, t.clientY));
  }, { passive: false });
  canvas.addEventListener("touchmove", (e) => {
    e.preventDefault();
    const t = e.changedTouches[0];
    onPointerMove(...getCanvasCoords(t.clientX, t.clientY));
  }, { passive: false });
  canvas.addEventListener("touchend", (e) => {
    e.preventDefault();
    const t = e.changedTouches[0];
    onPointerUp(...getCanvasCoords(t.clientX, t.clientY));
  }, { passive: false });

  window.addEventListener("keydown", (e) => {
    sound.ensureContext();
    if (gameMode === "MainMenu") {
      if (showCreditsModal && (e.code === "Space" || e.code === "Enter" || e.code === "Escape")) {
        sound.play("select");
        showCreditsModal = false;
      } else if (!showCreditsModal && e.code === "Space") {
        sound.play("select");
        resetGameScreen();
        gameMode = "GameScreen";
      }
    } else if (gameMode === "EndScreen") {
      if (e.code === "Space" || e.code === "Enter" || e.code === "Escape") {
        sound.play("select");
        highScores = HighScoreManager.loadScores();
        gameMode = "MainMenu";
      }
    } else if (gameMode === "GameScreen") {
      if (showHowToPlay && (e.code === "Space" || e.code === "Enter" || e.code === "Escape" || e.code === "KeyH")) {
        sound.play("select");
        showHowToPlay = false;
        lastActionTime = performance.now();
        lastSecondTick = performance.now();
      } else if (isTimeOver && performance.now() - timeOverStart > 1200 && (e.code === "Space" || e.code === "Enter" || e.code === "Escape")) {
        goToEndScreen();
      } else if (!showHowToPlay && !isTimeOver && !animData && !isFalling) {
        if (e.code === "KeyR" && shufflesLeft > 0) {
          shufflesLeft -= 1;
          shuffleBoard();
        } else if (e.code === "KeyH") {
          sound.play("select");
          showHowToPlay = true;
        }
      }
    }
  });

  // --- Rendering & Update Loop ---
  function updateClouds(ticks) {
    const t = ticks * 0.0012;
    cloud1XY[0] += 0.42 + Math.sin(t * 0.55) * 0.08;
    if (cloud1XY[0] > 1380) cloud1XY[0] = -420;
    cloud1XY[1] = 22.0 + Math.sin(t * 0.85) * 5.0;

    cloud2XY[0] += 0.19 + Math.sin(t * 0.55 + 2.1) * 0.05;
    if (cloud2XY[0] > 1380) cloud2XY[0] = -260;
    cloud2XY[1] = 135.0 + Math.sin(t * 0.85 + 2.1) * 3.5;

    cloud3XY[0] += 0.30 + Math.sin(t * 0.55 + 4.2) * 0.06;
    if (cloud3XY[0] > 1380) cloud3XY[0] = -320;
    cloud3XY[1] = 72.0 + Math.sin(t * 0.85 + 4.2) * 4.5;
  }

  function getMenuClouds() {
    if (assets.cloudsVibrant.length < 3) return null;
    return [
      [assets.cloudsVibrant[0], cloud1XY],
      [assets.cloudsVibrant[1], cloud2XY],
      [assets.cloudsVibrant[2], cloud3XY]
    ];
  }

  function drawMainMenu(ticks) {
    const t = ticks * 0.003;
    shader.drawParallaxBackground(ticks, mouseX, mouseY, getMenuClouds(), false);
    shader.drawAtmosphere(ticks);

    const [mainCol, glowCol] = TITLE_PALETTE[titleColorIndex];
    const titleStr = "Flowers";
    ctx.save();
    ctx.font = '92px "GameFont", sans-serif';
    const tw = ctx.measureText(titleStr).width;
    ctx.restore();
    const tx = (VIRTUAL_W - tw) * 0.5;
    const ty = 20 + Math.sin(t * 1.6) * 6;
    titleRect = { x: tx - 12, y: ty - 6, w: tw + 24, h: 108 };
    shader.drawGlowText(92, titleStr, tx, ty, { mainColor: mainCol, glowColor: glowCol, offset: 4 });

    const subStr = "Swap blooms in 8 directions, trigger cascading combos & race the clock!";
    const sw = 1040, sh = 52;
    const sx = (VIRTUAL_W - sw) * 0.5;
    const sy = 135 + Math.sin(t * 1.6) * 4;
    shader.drawGlowPanel(ticks, sx, sy, sw, sh);
    shader.drawGlowText(27, subStr, sx, sy + 10, {
      mainColor: [255, 245, 190],
      offset: 2,
      maxWidth: sw - 32,
      centerWidth: sw
    });

    const hsW = 430, hsH = 215;
    const hsX = (VIRTUAL_W - hsW) * 0.5, hsY = 285;
    shader.drawGlowPanel(ticks, hsX, hsY, hsW, hsH);
    shader.drawGlowText(36, "Top 3 High Scores", hsX, hsY + 14, {
      mainColor: [255, 235, 150],
      offset: 2,
      maxWidth: hsW - 32,
      centerWidth: hsW
    });
    const medalColors = [[255, 235, 130], [225, 235, 255], [255, 195, 150]];
    for (let idx = 0; idx < 3; idx++) {
      const scoreTxt = idx < highScores.length ? `${highScores[idx]} pts` : "---";
      shader.drawGlowText(27, `#${idx + 1}    ${scoreTxt}`, hsX, hsY + 72 + idx * 44, {
        mainColor: medalColors[idx],
        offset: 2,
        maxWidth: hsW - 32,
        centerWidth: hsW
      });
    }

    const startStr = "Click or press space to start!";
    const bw = 540, bh = 66;
    const bx = (VIRTUAL_W - bw) * 0.5, by = 615;
    const hovered = ptInRect(mouseX, mouseY, { x: bx, y: by, w: bw, h: bh }) && !showCreditsModal;
    shader.drawGlowPanel(ticks, bx, by, bw, bh, hovered);
    shader.drawGlowText(36, startStr, bx, by + 14, { offset: 2, centerWidth: bw });

    if (showCreditsModal) {
      ctx.fillStyle = rgba(12, 6, 30, 185 / 255);
      ctx.fillRect(0, 0, VIRTUAL_W, VIRTUAL_H);
      const mw = 680, mh = 330;
      const mx = (VIRTUAL_W - mw) * 0.5, my = (VIRTUAL_H - mh) * 0.5;
      shader.drawGlowPanel(ticks, mx, my, mw, mh, true);
      shader.drawGlowText(56, "Made by Frank Mulvie", mx, my + 30, {
        mainColor: [255, 240, 150],
        offset: 3,
        maxWidth: mw - 48,
        centerWidth: mw
      });
      shader.drawGlowText(34, "Version 1.0.0", mx, my + 125, {
        mainColor: [180, 240, 255],
        offset: 2,
        maxWidth: mw - 48,
        centerWidth: mw
      });
      creditsUrlRect = { x: mx + 120, y: my + 180, w: mw - 240, h: 46 };
      const urlHovered = ptInRect(mouseX, mouseY, creditsUrlRect);
      shader.drawGlowText(34, "https://knrf.itch.io/", mx, my + 185, {
        mainColor: urlHovered ? [255, 235, 140] : [255, 185, 245],
        offset: 2,
        maxWidth: mw - 48,
        centerWidth: mw
      });
      shader.drawGlowText(26, "Click anywhere or press Space to close", mx, my + 255, {
        mainColor: [230, 225, 255],
        offset: 2,
        maxWidth: mw - 48,
        centerWidth: mw
      });
    }
  }

  function drawBoardBorderShader(ticks) {
    const boardW = BOARD_COL * CELL_SIZE;
    const boardH = BOARD_ROW * CELL_SIZE;
    const bx = BOARD_START_X, by = BOARD_START_Y;
    const totalPos = ticks / 5500.0;
    const idx = Math.floor(totalPos) % BOARD_PULSE_PALETTE.length;
    const nxt = (idx + 1) % BOARD_PULSE_PALETTE.length;
    const rawT = totalPos - Math.floor(totalPos);
    const blend = rawT * rawT * (3.0 - 2.0 * rawT);

    const [c1, b1] = BOARD_PULSE_PALETTE[idx];
    const [c2, b2] = BOARD_PULSE_PALETTE[nxt];
    const glowR = c1[0] + (c2[0] - c1[0]) * blend;
    const glowG = c1[1] + (c2[1] - c1[1]) * blend;
    const glowB = c1[2] + (c2[2] - c1[2]) * blend;
    const bgR = b1[0] + (b2[0] - b1[0]) * blend;
    const bgG = b1[1] + (b2[1] - b1[1]) * blend;
    const bgB = b1[2] + (b2[2] - b1[2]) * blend;
    const breath = (Math.sin(ticks * 0.0022) + 1.0) * 0.5;

    ctx.fillStyle = rgba(bgR, bgG, bgB, 145 / 255);
    roundRectPath(ctx, bx - 12, by - 12, boardW + 24, boardH + 24, 16);
    ctx.fill();

    ctx.lineWidth = 1;
    ctx.strokeStyle = rgba(glowR, glowG, glowB, 38 / 255);
    for (let r = 0; r < BOARD_ROW; r++) {
      for (let c = 0; c < BOARD_COL; c++) {
        roundRectPath(ctx, bx + c * CELL_SIZE + 3, by + r * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6, 10);
        ctx.stroke();
      }
    }

    ctx.lineWidth = 4;
    for (let layer = 5; layer >= 1; layer--) {
      const spread = layer * 3;
      const alpha = (((42 + 22 * breath) * (6 - layer)) / 5) / 255;
      ctx.strokeStyle = rgba(glowR, glowG, glowB, alpha);
      roundRectPath(ctx, bx - 12 - spread, by - 12 - spread, boardW + 24 + spread * 2, boardH + 24 + spread * 2, 16 + spread);
      ctx.stroke();
    }

    ctx.lineWidth = 3;
    ctx.strokeStyle = rgba(Math.min(255, glowR + 55), Math.min(255, glowG + 55), Math.min(255, glowB + 55), 245 / 255);
    roundRectPath(ctx, bx - 12, by - 12, boardW + 24, boardH + 24, 16);
    ctx.stroke();
  }

  function drawLightningBolt(x1, y1, x2, y2, glowStyle, coreStyle, width = 4, segments = 14, jitter = 11) {
    const dx = (x2 - x1) / segments;
    const dy = (y2 - y1) / segments;
    const plen = Math.hypot(-dy, dx) || 1;
    const px = -dy / plen;
    const py = dx / plen;
    const pts = [[x1, y1]];
    for (let i = 1; i < segments; i++) {
      const off = (Math.random() * 2 - 1) * jitter;
      pts.push([x1 + dx * i + px * off, y1 + dy * i + py * off]);
    }
    pts.push([x2, y2]);

    for (const [style, w] of [[glowStyle, width + 4], [coreStyle, Math.max(2, width)]]) {
      ctx.strokeStyle = style;
      ctx.lineWidth = w;
      ctx.beginPath();
      ctx.moveTo(pts[0][0], pts[0][1]);
      for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
      ctx.stroke();
    }
  }

  function drawEffects() {
    if (specialEffects.length) {
      const boardW = BOARD_COL * CELL_SIZE;
      const boardH = BOARD_ROW * CELL_SIZE;
      const rainbowPalette = [
        [255, 80, 110], [255, 165, 70], [255, 240, 90],
        [95, 245, 145], [85, 215, 255], [170, 120, 255], [255, 110, 220]
      ];
      const aliveFx = [];
      for (const eff of specialEffects) {
        eff.timer += 1;
        if (eff.timer > eff.maxTimer) continue;
        aliveFx.push(eff);
        const prog = eff.timer / eff.maxTimer;
        const fade = 1.0 - prog;

        if (eff.type === "zap") {
          const rowY = BOARD_START_Y + eff.r * CELL_SIZE;
          const colX = BOARD_START_X + eff.c * CELL_SIZE;
          const beamAlpha = Math.pow(fade, 0.8) * 0.68;
          const coreAlpha = fade * 0.96;

          ctx.fillStyle = rgba(255, 225, 70, beamAlpha * 0.5);
          roundRectPath(ctx, BOARD_START_X, rowY + 8, boardW, CELL_SIZE - 16, 12);
          ctx.fill();
          roundRectPath(ctx, colX + 8, BOARD_START_Y, CELL_SIZE - 16, boardH, 12);
          ctx.fill();

          drawLightningBolt(
            BOARD_START_X, eff.cy, BOARD_START_X + boardW, eff.cy,
            rgba(255, 230, 60, beamAlpha), rgba(255, 255, 235, coreAlpha),
            4, 16, 13 * fade + 3
          );
          drawLightningBolt(
            eff.cx, BOARD_START_Y, eff.cx, BOARD_START_Y + boardH,
            rgba(120, 240, 255, beamAlpha), rgba(255, 255, 235, coreAlpha),
            4, 14, 13 * fade + 3
          );

          ctx.fillStyle = rgba(255, 250, 150, beamAlpha);
          ctx.beginPath();
          ctx.arc(eff.cx, eff.cy, 38 * fade + 10, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = rgba(255, 255, 255, coreAlpha);
          ctx.beginPath();
          ctx.arc(eff.cx, eff.cy, 18 * fade + 4, 0, Math.PI * 2);
          ctx.fill();
        } else if (eff.type === "rainbow") {
          const alpha = fade * 0.92;
          const baseRad = 18 + prog * 360;
          ctx.lineWidth = 4;
          for (let i = 0; i < rainbowPalette.length; i++) {
            const [rr, rg, rb] = rainbowPalette[i];
            ctx.strokeStyle = rgba(rr, rg, rb, alpha * 0.75);
            ctx.beginPath();
            ctx.arc(eff.cx, eff.cy, Math.max(4, baseRad - i * 5), 0, Math.PI * 2);
            ctx.stroke();
          }
          for (let i = 0; i < eff.targets.length; i++) {
            const [tx, ty] = eff.targets[i];
            const c1 = rainbowPalette[(i + eff.timer) % rainbowPalette.length];
            const c2 = rainbowPalette[(i + eff.timer + 2) % rainbowPalette.length];
            ctx.strokeStyle = rgba(c1[0], c1[1], c1[2], alpha * 0.7);
            ctx.lineWidth = 7;
            ctx.beginPath();
            ctx.moveTo(eff.cx, eff.cy);
            ctx.lineTo(tx, ty);
            ctx.stroke();

            ctx.strokeStyle = rgba(c2[0], c2[1], c2[2], alpha);
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(eff.cx, eff.cy);
            ctx.lineTo(tx, ty);
            ctx.stroke();

            ctx.strokeStyle = rgba(255, 255, 255, alpha);
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(eff.cx, eff.cy);
            ctx.lineTo(tx, ty);
            ctx.stroke();

            const burstR = 12 + 16 * Math.sin(prog * Math.PI);
            ctx.fillStyle = rgba(c1[0], c1[1], c1[2], alpha * 0.65);
            ctx.beginPath();
            ctx.arc(tx, ty, burstR, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = rgba(255, 255, 255, alpha);
            ctx.beginPath();
            ctx.arc(tx, ty, Math.max(3, burstR * 0.5), 0, Math.PI * 2);
            ctx.fill();
          }
        } else if (eff.type === "bomb") {
          const [bx, by, bw, bh] = eff.rect;
          const alpha = Math.pow(fade, 0.85) * 0.9;
          ctx.fillStyle = rgba(255, 95, 50, fade * 0.47);
          roundRectPath(ctx, bx, by, bw, bh, 18);
          ctx.fill();

          ctx.lineWidth = 4;
          ctx.strokeStyle = rgba(255, 220, 110, alpha);
          roundRectPath(ctx, bx, by, bw, bh, 18);
          ctx.stroke();

          const maxRad = Math.max(bw, bh) * 0.62;
          const shockRad = Math.max(8, prog * maxRad);
          const innerRad = Math.max(4, (1 - prog * 0.5) * maxRad * 0.55);

          ctx.fillStyle = rgba(255, 110, 45, fade * 0.6);
          ctx.beginPath();
          ctx.arc(eff.cx, eff.cy, innerRad, 0, Math.PI * 2);
          ctx.fill();

          ctx.fillStyle = rgba(255, 235, 140, fade * 0.82);
          ctx.beginPath();
          ctx.arc(eff.cx, eff.cy, innerRad * 0.6, 0, Math.PI * 2);
          ctx.fill();

          ctx.lineWidth = 6;
          ctx.strokeStyle = rgba(255, 95, 195, alpha);
          ctx.beginPath();
          ctx.arc(eff.cx, eff.cy, shockRad, 0, Math.PI * 2);
          ctx.stroke();

          ctx.lineWidth = 3;
          ctx.strokeStyle = rgba(255, 245, 170, alpha);
          ctx.beginPath();
          ctx.arc(eff.cx, eff.cy, Math.max(4, shockRad - 10), 0, Math.PI * 2);
          ctx.stroke();
        }
      }
      specialEffects = aliveFx;
    }

    if (burstParticles.length) {
      const aliveP = [];
      for (const p of burstParticles) {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.22;
        p.alpha -= 9;
        if (p.alpha <= 0) continue;
        aliveP.push(p);
        const a = p.alpha / 255;
        const [r, g, b] = p.col;
        ctx.fillStyle = rgba(r, g, b, a * 0.5);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius * 1.8, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = rgba(r, g, b, a);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = rgba(255, 255, 255, a);
        ctx.beginPath();
        ctx.arc(p.x, p.y, Math.max(1, p.radius * 0.4), 0, Math.PI * 2);
        ctx.fill();
      }
      burstParticles = aliveP;
    }

    if (floatingTexts.length) {
      const aliveT = [];
      for (const ft of floatingTexts) {
        ft.y -= 0.75;
        ft.alpha -= 2.4;
        if (ft.alpha <= 0) continue;
        aliveT.push(ft);
        shader.drawGlowText(30, ft.text, ft.x, ft.y, {
          mainColor: ft.color,
          glowColor: [60, 20, 120],
          offset: 2,
          alpha: Math.min(1, ft.alpha / 255)
        });
      }
      floatingTexts = aliveT;
    }
  }

  function drawTimeOverShader(ticks) {
    const elapsed = ticks - timeOverStart;
    const t = elapsed * 0.004;
    const boardW = BOARD_COL * CELL_SIZE;
    const boardH = BOARD_ROW * CELL_SIZE;
    const cx = BOARD_START_X + boardW * 0.5;
    const cy = BOARD_START_Y + boardH * 0.5;

    const aliveTf = [];
    for (const tf of timeOverFlowers) {
      if (tf.delay > 0) {
        tf.delay -= 1;
        const jx = tf.x + Math.sin(elapsed * 0.05 + tf.y) * 2.5;
        ctx.drawImage(tf.surf, jx, tf.y);
        aliveTf.push(tf);
      } else {
        if (!tf.launched) {
          tf.launched = true;
          if (Math.random() < 0.35) spawnBurst(tf.x, tf.y, tf.colorName);
        }
        tf.x += tf.vx;
        tf.y += tf.vy;
        tf.vy += 0.58;
        tf.angle = (tf.angle + tf.angVel) % 360;
        if (tf.y < 790) {
          ctx.save();
          ctx.translate(tf.x + FLOWER_SIZE * 0.5, tf.y + FLOWER_SIZE * 0.5);
          ctx.rotate((tf.angle * Math.PI) / 180);
          ctx.drawImage(tf.surf, -FLOWER_SIZE * 0.5, -FLOWER_SIZE * 0.5);
          ctx.restore();
          aliveTf.push(tf);
        }
      }
    }
    timeOverFlowers = aliveTf;

    const washAlpha = Math.min(135, elapsed * 0.08) / 255;
    ctx.fillStyle = rgba(28, 10, 52, washAlpha);
    roundRectPath(ctx, BOARD_START_X - 12, BOARD_START_Y - 12, boardW + 24, boardH + 24, 16);
    ctx.fill();

    ctx.lineWidth = 4;
    for (let i = 0; i < 3; i++) {
      const ringProg = (elapsed - i * 260) * 0.42;
      if (ringProg > 0 && ringProg < 520) {
        const ra = Math.max(0, 1 - ringProg / 520) * 0.75;
        ctx.strokeStyle = i % 2 === 0 ? rgba(255, 120, 210, ra) : rgba(120, 230, 255, ra);
        ctx.beginPath();
        ctx.arc(cx, cy, ringProg, 0, Math.PI * 2);
        ctx.stroke();
      }
    }

    const bannerW = 520, bannerH = 155;
    const bx = cx - bannerW * 0.5;
    const by = cy - bannerH * 0.5 + Math.sin(t * 2.0) * 6;
    shader.drawGlowPanel(ticks, bx, by, bannerW, bannerH, true);

    const pulse = (Math.sin(t * 3.0) + 1.0) * 0.5;
    shader.drawGlowText(84, "TIME OVER!", bx, by + 26, {
      mainColor: [255, Math.floor(215 + 35 * pulse), Math.floor(140 + 60 * pulse)],
      glowColor: [210, 35, 115],
      offset: 4,
      maxWidth: bannerW - 40,
      centerWidth: bannerW
    });
  }

  function drawHowToPlayModal(ticks) {
    ctx.fillStyle = rgba(12, 6, 30, 185 / 255);
    ctx.fillRect(0, 0, VIRTUAL_W, VIRTUAL_H);

    const mx = 180, my = 55, mw = 920, mh = 610;
    shader.drawGlowPanel(ticks, mx, my, mw, mh);
    shader.drawGlowText(56, "How to Play Flowers", mx, my + 22, {
      mainColor: [255, 240, 160],
      offset: 3,
      maxWidth: mw - 48,
      centerWidth: mw
    });

    const lines = [
      ["Goal:", "Match 3 or more flowers of the same color in a row or column!", [180, 245, 255]],
      ["8-Way Swap:", "Click 2 neighbors OR click & drag horizontally, vertically, or diagonally.", [245, 235, 255]],
      ["Match 4 (Zap):", "Spawns a zap flower that clears its full row & column!", [255, 235, 140]],
      ["Match 5 (Rainbow):", "Spawns a rainbow-ring flower that clears all flowers of its color (+3s)!", [255, 195, 245]],
      ["Match 6+ (Bomb):", "Spawns a bomb flower that blasts a 5x5 area around it (+3s)!", [160, 255, 210]],
      ["Combos & Levels:", "Chain cascades boost your multiplier (2x, 3x...). Level up for +15s!", [245, 235, 255]],
      ["Hints & Shuffle:", "Wait 6s for an auto-hint wiggle, or press [R] / Shuffle when stuck.", [220, 215, 255]]
    ];

    let yCursor = my + 110;
    for (const [heading, desc, col] of lines) {
      shader.drawGlowText(30, heading, mx + 38, yCursor, {
        mainColor: col,
        offset: 2,
        maxWidth: 275
      });
      shader.drawGlowText(21, desc, mx + 320, yCursor + 6, {
        mainColor: [245, 240, 255],
        offset: 1,
        maxWidth: mw - 350
      });
      yCursor += 58;
    }

    const hovered = ptInRect(mouseX, mouseY, howToPlayCloseRect);
    shader.drawGlowPanel(ticks, howToPlayCloseRect.x, howToPlayCloseRect.y, howToPlayCloseRect.w, howToPlayCloseRect.h, hovered);
    shader.drawGlowText(30, "Got It - Let's Play! (Click / Space)", howToPlayCloseRect.x, howToPlayCloseRect.y + 13, {
      mainColor: hovered ? [255, 245, 190] : [245, 235, 255],
      offset: 2,
      maxWidth: howToPlayCloseRect.w - 28,
      centerWidth: howToPlayCloseRect.w
    });
  }

  function updateGameScreen(ticks) {
    if (!showHowToPlay && !isTimeOver) {
      if (ticks - lastSecondTick >= 1000) {
        lastSecondTick += 1000;
        currentTime -= 1;
        if (currentTime > 0 && currentTime <= 10) sound.play("tick");
        if (currentTime <= 0) {
          triggerTimeOver();
          return;
        }
      }
    } else {
      lastSecondTick = ticks;
    }

    if (isTimeOver) {
      if (ticks - timeOverStart >= 3200) goToEndScreen();
      return;
    }

    if (animData) {
      const speed = 5.0;
      for (const [fl, tx, ty] of [[animData.f1, animData.t1x, animData.t1y], [animData.f2, animData.t2x, animData.t2y]]) {
        if (Math.abs(fl.x - tx) <= speed) fl.x = tx;
        else fl.x += fl.x < tx ? speed : -speed;

        if (Math.abs(fl.y - ty) <= speed) fl.y = ty;
        else fl.y += fl.y < ty ? speed : -speed;
      }
      lastActionTime = ticks;
      if (
        Math.abs(animData.f1.x - animData.t1x) < 0.5 &&
        Math.abs(animData.f1.y - animData.t1y) < 0.5 &&
        Math.abs(animData.f2.x - animData.t2x) < 0.5 &&
        Math.abs(animData.f2.y - animData.t2y) < 0.5
      ) {
        animData = null;
      }
    } else if (isFalling) {
      let stillFalling = false;
      const fallSpeed = 9.0;
      for (const row of board) {
        for (const fl of row) {
          if (Math.abs(fl.y - fl.targetY) > 0.5) {
            stillFalling = true;
            fl.y = fl.y < fl.targetY
              ? Math.min(fl.targetY, fl.y + fallSpeed)
              : Math.max(fl.targetY, fl.y - fallSpeed);
          } else {
            fl.y = fl.targetY;
          }
        }
      }
      isFalling = stillFalling;
      lastActionTime = ticks;
    } else {
      checkBoard();
      if (matchesFound.length) {
        deleteAndReplaceFlowers(false);
      } else if (!showHowToPlay && !hintPair && ticks - lastActionTime > 6000) {
        const move = findHintMove();
        if (move) hintPair = move;
        else shuffleBoard();
      }
    }
  }

  function drawGameScreen(ticks) {
    shader.drawParallaxBackground(ticks, mouseX, mouseY, null, true);
    shader.drawAtmosphere(ticks);

    const hudX = 875, hudY = 60, hudW = 355, hudH = 435;
    const padX = hudX + 22, innerW = hudW - 44;

    shader.drawGlowPanel(ticks, hudX, hudY, hudW, hudH);
    shader.drawGlowText(30, `Level ${level}`, padX, 70, { mainColor: [180, 240, 255], offset: 2, maxWidth: innerW });
    shader.drawGlowText(30, `Score: ${userScore}`, padX, 112, { mainColor: [255, 240, 170], offset: 2, maxWidth: innerW });
    shader.drawGlowText(21, `High Score: ${Math.max(bestScore, userScore)}`, padX, 154, { mainColor: [210, 255, 195], offset: 1, maxWidth: innerW });

    const prevTarget = level > 1 ? (level - 1) * 1500 : 0;
    const span = Math.max(1, levelTarget - prevTarget);
    const prog = Math.max(0, Math.min(1, (userScore - prevTarget) / span));
    const barX = padX, barY = 196, barW = innerW, barH = 18;
    ctx.fillStyle = rgba(25, 15, 55, 1);
    roundRectPath(ctx, barX, barY, barW, barH, 9);
    ctx.fill();
    if (prog > 0) {
      ctx.fillStyle = rgba(140, 235, 255, 1);
      roundRectPath(ctx, barX, barY, barW * prog, barH, 9);
      ctx.fill();
    }
    ctx.lineWidth = 2;
    ctx.strokeStyle = rgba(210, 180, 255, 1);
    roundRectPath(ctx, barX, barY, barW, barH, 9);
    ctx.stroke();

    shader.drawGlowText(21, `Next Level: ${levelTarget}`, padX, 222, { offset: 1, maxWidth: innerW });

    const timeCol = currentTime <= 10 ? [255, 110, 110] : [245, 235, 255];
    const mins = Math.floor(Math.max(0, currentTime) / 60);
    const secs = Math.floor(Math.max(0, currentTime) % 60);
    const timeStr = `Time: ${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    shader.drawGlowText(30, timeStr, padX, 258, { mainColor: timeCol, offset: 2, maxWidth: innerW });
    if (comboCount > 1) {
      shader.drawGlowText(30, `Combo: ${comboCount}x!`, padX, 300, { mainColor: [255, 220, 120], offset: 2, maxWidth: innerW });
    }

    shader.drawGlowText(21, "8-Way & Drag Swap Enabled", padX, 344, { mainColor: [210, 210, 255], offset: 1, maxWidth: innerW });
    shader.drawGlowText(21, "Match 4: Zap (Clears Row & Col)", padX, 378, { mainColor: [255, 235, 140], offset: 1, maxWidth: innerW });
    shader.drawGlowText(21, "Match 5: Rainbow (Clears Color)", padX, 410, { mainColor: [255, 195, 245], offset: 1, maxWidth: innerW });
    shader.drawGlowText(21, "Match 6+: Bomb (5x5 Blast)", padX, 442, { mainColor: [160, 255, 210], offset: 1, maxWidth: innerW });

    const hovShuffle = ptInRect(mouseX, mouseY, shuffleBtnRect) && shufflesLeft > 0 && !showHowToPlay;
    shader.drawGlowPanel(ticks, shuffleBtnRect.x, shuffleBtnRect.y, shuffleBtnRect.w, shuffleBtnRect.h, hovShuffle);
    shader.drawGlowText(30, `Shuffle (${shufflesLeft}) [R]`, shuffleBtnRect.x, shuffleBtnRect.y + 12, {
      offset: 2,
      maxWidth: shuffleBtnRect.w - 28,
      centerWidth: shuffleBtnRect.w
    });

    const hovHelp = ptInRect(mouseX, mouseY, helpBtnRect) && !showHowToPlay;
    shader.drawGlowPanel(ticks, helpBtnRect.x, helpBtnRect.y, helpBtnRect.w, helpBtnRect.h, hovHelp);
    shader.drawGlowText(30, "How to Play [H]", helpBtnRect.x, helpBtnRect.y + 12, {
      offset: 2,
      maxWidth: helpBtnRect.w - 28,
      centerWidth: helpBtnRect.w
    });

    drawBoardBorderShader(ticks);
    if (isTimeOver) {
      drawTimeOverShader(ticks);
      drawEffects();
    } else {
      const selectedSet = new Set(flowersSelected.map(([r, c]) => `${r},${c}`));
      const hintSet = hintPair ? new Set([`${hintPair[0][0]},${hintPair[0][1]}`, `${hintPair[1][0]},${hintPair[1][1]}`]) : new Set();
      const t = ticks * 0.015;
      let shakeX = 0, shakeY = 0;
      if (screenShake > 0.2) {
        shakeX = (Math.random() * 2 - 1) * screenShake;
        shakeY = (Math.random() * 2 - 1) * screenShake;
        screenShake *= 0.84;
      } else {
        screenShake = 0;
      }

      for (let r = 0; r < BOARD_ROW; r++) {
        for (let c = 0; c < BOARD_COL; c++) {
          const fl = board[r][c];
          if (!fl) continue;
          let drawX = fl.x + shakeX;
          const drawY = fl.y + shakeY;
          const key = `${r},${c}`;

          if (hintSet.has(key)) {
            drawX += Math.sin(t) * 3.5;
            ctx.strokeStyle = rgba(120, 255, 240, 180 / 255);
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.arc(drawX + FLOWER_SIZE * 0.5, drawY + FLOWER_SIZE * 0.5, FLOWER_SIZE * 0.5 + 4, 0, Math.PI * 2);
            ctx.stroke();
          }

          if (selectedSet.has(key)) {
            const pulse = (Math.sin(ticks * 0.008) + 1.0) * 0.5;
            ctx.fillStyle = rgba(255, 235, 130, (85 + 75 * pulse) / 255);
            ctx.beginPath();
            ctx.arc(drawX + FLOWER_SIZE * 0.5, drawY + FLOWER_SIZE * 0.5, FLOWER_SIZE * 0.55, 0, Math.PI * 2);
            ctx.fill();
          }

          ctx.drawImage(fl.surf, drawX, drawY);
          if (fl.special === "rainbow") {
            const rt = ticks * 0.008;
            const cr = Math.floor(127 + 127 * Math.sin(rt));
            const cg = Math.floor(127 + 127 * Math.sin(rt + 2.1));
            const cb = Math.floor(127 + 127 * Math.sin(rt + 4.2));
            ctx.fillStyle = rgba(cr, cg, cb, 1);
            ctx.beginPath();
            ctx.arc(drawX + FLOWER_SIZE * 0.5, drawY + FLOWER_SIZE * 0.5, 7, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      }
      drawEffects();
    }

    if (showHowToPlay) {
      drawHowToPlayModal(ticks);
    }
  }

  function drawEndScreen(ticks) {
    const t = ticks * 0.003;
    shader.drawParallaxBackground(ticks, mouseX, mouseY, getMenuClouds(), false);
    shader.drawAtmosphere(ticks);

    const msg1Str = `Your Score: ${finalScore}`;
    const msg2Str = "Click or press Space to play again";
    ctx.save();
    ctx.font = '72px "GameFont", sans-serif';
    const pw = Math.max(460, ctx.measureText(msg1Str).width + 64);
    ctx.restore();
    const px = (VIRTUAL_W - pw) * 0.5;
    const ty = 50 + Math.sin(t * 1.6) * 6;
    shader.drawGlowPanel(ticks, px, ty - 16, pw, 108);
    shader.drawGlowText(72, msg1Str, px, ty, { offset: 3, maxWidth: pw - 32, centerWidth: pw });

    const hsW = 460, hsH = 290;
    const hsX = (VIRTUAL_W - hsW) * 0.5, hsY = 225;
    shader.drawGlowPanel(ticks, hsX, hsY, hsW, hsH);
    shader.drawGlowText(34, "Top High Scores", hsX, hsY + 18, {
      mainColor: [255, 235, 150],
      offset: 2,
      centerWidth: hsW
    });
    for (let idx = 0; idx < Math.min(5, highScores.length); idx++) {
      const hs = highScores[idx];
      const col = hs === finalScore && finalScore > 0 ? [255, 240, 140] : [240, 230, 255];
      shader.drawGlowText(26, `#${idx + 1}    ${hs} pts`, hsX, hsY + 80 + idx * 40, {
        mainColor: col,
        offset: 2,
        centerWidth: hsW
      });
    }

    const bw = 660, bh = 66;
    const bx = (VIRTUAL_W - bw) * 0.5, by = 590;
    const hovered = ptInRect(mouseX, mouseY, { x: bx, y: by, w: bw, h: bh });
    shader.drawGlowPanel(ticks, bx, by, bw, bh, hovered);
    shader.drawGlowText(34, msg2Str, bx, by + 14, { offset: 2, maxWidth: bw - 32, centerWidth: bw });
  }

  function extractSheetSet(sheetImg, dest) {
    dest["blue"] = extractSheetFlower(sheetImg, 0, 0, 341, 350, FLOWER_SIZE);
    dest["green"] = extractSheetFlower(sheetImg, 341, 0, 341, 350, FLOWER_SIZE);
    dest["purple"] = extractSheetFlower(sheetImg, 682, 0, 342, 350, FLOWER_SIZE);
    dest["red"] = extractSheetFlower(sheetImg, 0, 350, 341, 350, FLOWER_SIZE);
    dest["yellow"] = extractSheetFlower(sheetImg, 341, 350, 341, 350, FLOWER_SIZE);
    dest["orange"] = extractSheetFlower(sheetImg, 682, 350, 342, 350, FLOWER_SIZE);
  }

  async function initAssets() {
    try {
      if (document.fonts && document.fonts.load) {
        await document.fonts.load('36px "GameFont"');
      }
    } catch (_) {}

    const [
      sheetNormal,
      sheetBomb,
      sheetZap,
      bg1,
      bg2,
      bg3,
      c1,
      c2,
      c3
    ] = await Promise.all([
      loadImage("imgs/flower-sheet.png"),
      loadImage("imgs/flower-bombs.png"),
      loadImage("imgs/flower-zap.png"),
      loadImage("imgs/bg-layer1.jpeg"),
      loadImage("imgs/bg-layer2.jpeg"),
      loadImage("imgs/bg-layer3.jpeg"),
      loadImage("imgs/N-Cloud-1.png"),
      loadImage("imgs/N-Cloud-2.png"),
      loadImage("imgs/N-Cloud-3.png")
    ]);

    extractSheetSet(sheetNormal, assets.normalFlowers);
    extractSheetSet(sheetBomb, assets.bombFlowers);
    extractSheetSet(sheetZap, assets.zapFlowers);

    const l1 = keyWhiteAndScale(bg1, 1360, 765, false);
    const l2 = keyWhiteAndScale(bg2, 1360, 765, true);
    const l3 = keyWhiteAndScale(bg3, 1360, 765, true);
    assets.parallaxVibrant = [l1, l2, l3];
    assets.parallaxMuted = [muteCanvas(l1), muteCanvas(l2), muteCanvas(l3)];

    for (const [cImg, alpha] of [[c1, 232 / 255], [c2, 222 / 255], [c3, 228 / 255]]) {
      const cw = Math.max(1, Math.floor(cImg.width * 0.6));
      const ch = Math.max(1, Math.floor(cImg.height * 0.6));
      const scaled = keyWhiteAndScale(cImg, cw, ch, false);
      assets.cloudsVibrant.push(scaled);
      assets.cloudsMuted.push(muteCanvas(scaled, alpha));
    }

    resetGameScreen();
    assets.ready = true;
  }

  function frame(ticks) {
    ctx.clearRect(0, 0, VIRTUAL_W, VIRTUAL_H);
    if (!assets.ready) {
      ctx.fillStyle = "#160a2e";
      ctx.fillRect(0, 0, VIRTUAL_W, VIRTUAL_H);
      shader.drawGlowText(48, "Loading Flowers...", 0, 320, { centerWidth: VIRTUAL_W });
    } else if (gameMode === "MainMenu") {
      updateClouds(ticks);
      drawMainMenu(ticks);
    } else if (gameMode === "GameScreen") {
      updateGameScreen(ticks);
      drawGameScreen(ticks);
    } else if (gameMode === "EndScreen") {
      updateClouds(ticks);
      drawEndScreen(ticks);
    }
    requestAnimationFrame(frame);
  }

  initAssets().catch((err) => console.error("Failed to load assets:", err));
  requestAnimationFrame(frame);
})();
