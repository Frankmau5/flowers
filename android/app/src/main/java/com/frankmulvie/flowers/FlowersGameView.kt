package com.frankmulvie.flowers

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.PorterDuff
import android.graphics.PorterDuffColorFilter
import android.graphics.Rect
import android.graphics.RectF
import android.graphics.Typeface
import android.net.Uri
import android.os.SystemClock
import android.view.MotionEvent
import android.view.View
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow
import kotlin.math.sin
import kotlin.random.Random

class FlowersGameView(context: Context) : View(context) {

    enum class GameMode { MAIN_MENU, GAME_SCREEN, END_SCREEN }

    data class Flower(
        var name: String,
        var x: Float,
        var y: Float,
        var targetX: Float,
        var targetY: Float,
        var surf: Bitmap,
        var special: String? = null
    )

    data class BurstParticle(
        var x: Float,
        var y: Float,
        var vx: Float,
        var vy: Float,
        val radius: Float,
        var alpha: Float,
        val r: Int,
        val g: Int,
        val b: Int
    )

    data class FloatingText(
        val text: String,
        val x: Float,
        var y: Float,
        var alpha: Float,
        val color: Int
    )

    data class SpecialEffect(
        val type: String,
        val r: Int = 0,
        val c: Int = 0,
        val cx: Float,
        val cy: Float,
        val targets: List<Pair<Float, Float>> = emptyList(),
        val rect: RectF = RectF(),
        var timer: Int = 0,
        val maxTimer: Int = 24
    )

    data class TimeOverFlower(
        val surf: Bitmap,
        var x: Float,
        var y: Float,
        val vx: Float,
        var vy: Float,
        var angle: Float,
        val angVel: Float,
        var delay: Float,
        val colorName: String,
        var launched: Boolean = false
    )

    data class SwapAnim(
        val f1: Flower,
        val f2: Flower,
        val t1x: Float,
        val t1y: Float,
        val t2x: Float,
        val t2y: Float,
        val r1: Int,
        val c1: Int,
        val r2: Int,
        val c2: Int,
        val revertSwap: Boolean = false
    )

    private val virtualW = 1280f
    private val virtualH = 720f
    private var viewScale = 1f
    private var viewOffsetX = 0f
    private var viewOffsetY = 0f

    private val sound = SoundFX()
    private val shader = ScreenShader(context, 1280, 720)
    private val typeface: Typeface = try {
        Typeface.createFromAsset(context.assets, "fonts/GameFont.ttf")
    } catch (_: Exception) {
        Typeface.DEFAULT_BOLD
    }

    private val paint = Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG)
    private val textMeasurePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        this.typeface = this@FlowersGameView.typeface
    }
    private val rectF = RectF()
    private val startTimeMs = SystemClock.uptimeMillis()

    private var mode = GameMode.MAIN_MENU
    private var isPaused = false
    private var lastTouchX = 640f
    private var lastTouchY = 360f

    // Cloud state for MainMenu & EndScreen
    private var cloud1Bmp: Bitmap? = null
    private var cloud2Bmp: Bitmap? = null
    private var cloud3Bmp: Bitmap? = null
    private var cloud1XY = 40f to 22f
    private var cloud2XY = 460f to 135f
    private var cloud3XY = 940f to 72f

    // MainMenu state
    private val titlePalette = arrayOf(
        Color.rgb(245, 235, 255) to Color.rgb(95, 45, 190),
        Color.rgb(255, 235, 130) to Color.rgb(195, 95, 20),
        Color.rgb(140, 245, 255) to Color.rgb(25, 105, 195),
        Color.rgb(255, 155, 220) to Color.rgb(175, 30, 120),
        Color.rgb(155, 255, 175) to Color.rgb(25, 145, 65),
        Color.rgb(255, 165, 135) to Color.rgb(185, 45, 30)
    )
    private var titleColorIndex = 0
    private val titleRect = RectF(440f, 20f, 840f, 125f)
    private val titleClickTimes = mutableListOf<Long>()
    private var showCreditsModal = false
    private val creditsUrlRect = RectF(420f, 375f, 860f, 425f)
    private var highScores: List<Int> = HighScoreManager.loadScores(context)

    // Board & GameScreen state
    private val boardRow = 8
    private val boardCol = 10
    private val cellSize = 75f
    private val flowerSize = 60
    private val boardStartX = 80f
    private val boardStartY = 60f

    private val normalFlowers = mutableMapOf<String, Bitmap>()
    private val bombFlowers = mutableMapOf<String, Bitmap>()
    private val zapFlowers = mutableMapOf<String, Bitmap>()
    private val colorNames = arrayOf("red", "blue", "purple", "yellow", "green", "orange")
    private val colorMap = mapOf(
        "red" to Triple(255, 90, 90),
        "blue" to Triple(90, 175, 255),
        "green" to Triple(95, 235, 125),
        "purple" to Triple(195, 110, 255),
        "yellow" to Triple(255, 230, 95),
        "orange" to Triple(255, 155, 70)
    )
    private val boardPulsePalette = arrayOf(
        Triple(165, 95, 255) to Triple(38, 18, 72),
        Triple(70, 225, 255) to Triple(14, 48, 68),
        Triple(255, 115, 200) to Triple(68, 18, 52),
        Triple(105, 250, 170) to Triple(16, 58, 38),
        Triple(255, 205, 95) to Triple(68, 46, 14),
        Triple(255, 125, 110) to Triple(68, 22, 22)
    )

    private var board: Array<Array<Flower?>> = Array(boardRow) { arrayOfNulls(boardCol) }
    private val flowersSelected = mutableListOf<Pair<Int, Int>>()
    private var dragStartCell: Pair<Int, Int>? = null
    private var animData: SwapAnim? = null
    private var isFalling = false
    private val flowerMatchSpeedAnim = 5.0f
    private val fallSpeed = 9.0f

    private var userFirstMove = false
    private var userScore = 0
    private var finalScore = 0
    private var bestScore = 0
    private var previousHighScores: List<Int> = emptyList()
    private var comboCount = 0
    private var level = 1
    private var levelTarget = 1500
    private var currentTime = 180
    private var lastSecondTickMs = 0L
    private var shufflesLeft = 3
    private var showHowToPlay = true
    private var lastActionTimeMs = 0L
    private var hintPair: Pair<Pair<Int, Int>, Pair<Int, Int>>? = null
    private var isTimeOver = false
    private var timeOverStartMs = 0L
    private var screenShake = 0f

    private val shuffleBtnRect = RectF(875f, 515f, 875f + 355f, 515f + 58f)
    private val helpBtnRect = RectF(875f, 595f, 875f + 355f, 595f + 58f)
    private val howToPlayCloseRect = RectF(410f, 580f, 410f + 460f, 580f + 62f)

    private val burstParticles = mutableListOf<BurstParticle>()
    private val floatingTexts = mutableListOf<FloatingText>()
    private val specialEffects = mutableListOf<SpecialEffect>()
    private val timeOverFlowers = mutableListOf<TimeOverFlower>()
    private val matchesFound = mutableListOf<List<Pair<Int, Int>>>()

    init {
        loadAssets()
        resetGameScreen()
    }

    private fun ticksMs(): Long = SystemClock.uptimeMillis() - startTimeMs

    private fun extractSheetFlower(sheet: Bitmap, rx: Int, ry: Int, rw: Int, rh: Int, targetSize: Int): Bitmap {
        val safeW = min(rw, sheet.width - rx)
        val safeH = min(rh, sheet.height - ry)
        val sub = Bitmap.createBitmap(sheet, rx, ry, safeW, safeH)
        val pixels = IntArray(safeW * safeH)
        sub.getPixels(pixels, 0, safeW, 0, 0, safeW, safeH)
        var minX = safeW
        var minY = safeH
        var maxX = -1
        var maxY = -1
        for (y in 0 until safeH) {
            val rowOff = y * safeW
            for (x in 0 until safeW) {
                if (Color.alpha(pixels[rowOff + x]) > 8) {
                    if (x < minX) minX = x
                    if (x > maxX) maxX = x
                    if (y < minY) minY = y
                    if (y > maxY) maxY = y
                }
            }
        }
        if (maxX < minX || maxY < minY) {
            return Bitmap.createScaledBitmap(sub, targetSize, targetSize, true)
        }
        val bw = maxX - minX + 1
        val bh = maxY - minY + 1
        val cropped = Bitmap.createBitmap(sub, minX, minY, bw, bh)
        val side = max(bw, bh)
        val square = Bitmap.createBitmap(side, side, Bitmap.Config.ARGB_8888)
        val c = Canvas(square)
        c.drawBitmap(cropped, ((side - bw) / 2).toFloat(), ((side - bh) / 2).toFloat(), null)
        return Bitmap.createScaledBitmap(square, targetSize, targetSize, true)
    }

    private fun loadSheetIntoMap(assetPath: String, dest: MutableMap<String, Bitmap>) {
        try {
            context.assets.open(assetPath).use { stream ->
                val sheet = BitmapFactory.decodeStream(stream) ?: return
                dest["blue"] = extractSheetFlower(sheet, 0, 0, 341, 350, flowerSize)
                dest["green"] = extractSheetFlower(sheet, 341, 0, 341, 350, flowerSize)
                dest["purple"] = extractSheetFlower(sheet, 682, 0, 342, 350, flowerSize)
                dest["red"] = extractSheetFlower(sheet, 0, 350, 341, 350, flowerSize)
                dest["yellow"] = extractSheetFlower(sheet, 341, 350, 341, 350, flowerSize)
                dest["orange"] = extractSheetFlower(sheet, 682, 350, 342, 350, flowerSize)
            }
        } catch (_: Exception) {
        }
    }

    private fun loadAssets() {
        loadSheetIntoMap("imgs/flower-sheet.png", normalFlowers)
        loadSheetIntoMap("imgs/flower-bombs.png", bombFlowers)
        loadSheetIntoMap("imgs/flower-zap.png", zapFlowers)
        try {
            context.assets.open("imgs/N-Cloud-1.png").use {
                cloud1Bmp = ScreenShader.scaleCloud(BitmapFactory.decodeStream(it), 0.6f)
            }
            context.assets.open("imgs/N-Cloud-2.png").use {
                cloud2Bmp = ScreenShader.scaleCloud(BitmapFactory.decodeStream(it), 0.6f)
            }
            context.assets.open("imgs/N-Cloud-3.png").use {
                cloud3Bmp = ScreenShader.scaleCloud(BitmapFactory.decodeStream(it), 0.6f)
            }
        } catch (_: Exception) {
        }
    }

    private fun getFlowerSurf(name: String, special: String? = null): Bitmap {
        if (special == "bomb") {
            bombFlowers[name]?.let { return it }
        }
        if (special == "zap" || special == "line") {
            zapFlowers[name]?.let { return it }
        }
        return normalFlowers[name]
            ?: Bitmap.createBitmap(flowerSize, flowerSize, Bitmap.Config.ARGB_8888)
    }

    private fun cellToXY(r: Int, c: Int): Pair<Float, Float> {
        val pad = (cellSize - flowerSize) * 0.5f
        val x = boardStartX + c * cellSize + pad
        val y = boardStartY + r * cellSize + pad
        return x to y
    }

    private fun createFlower(x: Float, y: Float, special: String? = null): Flower {
        val color = colorNames[Random.nextInt(colorNames.size)]
        return Flower(
            name = color,
            x = x,
            y = y,
            targetX = x,
            targetY = y,
            surf = getFlowerSurf(color, special),
            special = special
        )
    }

    private fun resetGameScreen() {
        userScore = 0
        userFirstMove = false
        comboCount = 0
        level = 1
        levelTarget = 1500
        currentTime = 180
        shufflesLeft = 3
        showHowToPlay = true
        isTimeOver = false
        screenShake = 0f
        animData = null
        isFalling = false
        flowersSelected.clear()
        dragStartCell = null
        hintPair = null
        burstParticles.clear()
        floatingTexts.clear()
        specialEffects.clear()
        timeOverFlowers.clear()
        previousHighScores = HighScoreManager.loadScores(context)
        bestScore = previousHighScores.firstOrNull() ?: 0
        lastActionTimeMs = ticksMs()
        lastSecondTickMs = ticksMs()

        board = Array(boardRow) { r ->
            Array(boardCol) { c ->
                val (x, y) = cellToXY(r, c)
                createFlower(x, y)
            }
        }
        while (hasMatch()) {
            checkBoard()
            deleteAndReplaceFlowers(instant = true)
        }
    }

    private fun saveCurrentScore() {
        if (userScore > 0) {
            val combined = previousHighScores.toMutableList()
            combined.add(userScore)
            val updated = HighScoreManager.saveScoresList(context, combined)
            if (updated.isNotEmpty()) {
                bestScore = max(bestScore, updated[0])
            }
        }
    }

    private fun hasMatch(): Boolean {
        for (r in 0 until boardRow - 2) {
            for (c in 0 until boardCol) {
                val n = board[r][c]?.name ?: continue
                if (board[r + 1][c]?.name == n && board[r + 2][c]?.name == n) return true
            }
        }
        for (c in 0 until boardCol - 2) {
            for (r in 0 until boardRow) {
                val n = board[r][c]?.name ?: continue
                if (board[r][c + 1]?.name == n && board[r][c + 2]?.name == n) return true
            }
        }
        return false
    }

    private fun findHintMove(): Pair<Pair<Int, Int>, Pair<Int, Int>>? {
        val dirs = arrayOf(0 to 1, 1 to 0, 1 to 1, 1 to -1)
        for (r in 0 until boardRow) {
            for (c in 0 until boardCol) {
                for ((dr, dc) in dirs) {
                    val nr = r + dr
                    val nc = c + dc
                    if (nr in 0 until boardRow && nc in 0 until boardCol) {
                        val tmp = board[r][c]
                        board[r][c] = board[nr][nc]
                        board[nr][nc] = tmp
                        val matched = hasMatch()
                        board[nr][nc] = board[r][c]
                        board[r][c] = tmp
                        if (matched) return (r to c) to (nr to nc)
                    }
                }
            }
        }
        return null
    }

    private fun shuffleBoard() {
        sound.play("shuffle")
        val flat = mutableListOf<Flower>()
        for (r in 0 until boardRow) {
            for (c in 0 until boardCol) {
                board[r][c]?.let { flat.add(it) }
            }
        }
        for (attempt in 0 until 20) {
            flat.shuffle()
            var idx = 0
            for (r in 0 until boardRow) {
                for (c in 0 until boardCol) {
                    val f = flat[idx++]
                    val (tx, ty) = cellToXY(r, c)
                    f.x = tx
                    f.y = ty
                    f.targetX = tx
                    f.targetY = ty
                    board[r][c] = f
                }
            }
            if (!hasMatch() && findHintMove() != null) break
        }
        while (hasMatch()) {
            checkBoard()
            deleteAndReplaceFlowers(instant = true)
        }
        flowersSelected.clear()
        hintPair = null
        lastActionTimeMs = ticksMs()
    }

    private fun addFloatingText(text: String, x: Float, y: Float, color: Int = Color.rgb(255, 240, 150)) {
        textMeasurePaint.textSize = 30f
        val w = textMeasurePaint.measureText(text)
        val h = 34f
        val padX = 14f
        val padY = 6f
        val fx = x.coerceIn(boardStartX, boardStartX + boardCol * cellSize - w - 8f)
        var fy = y

        for (iter in 0 until floatingTexts.size + 2) {
            val myRect = RectF(fx - padX * 0.5f, fy - padY * 0.5f, fx + w + padX * 0.5f, fy + h + padY * 0.5f)
            var collided = false
            for (other in floatingTexts) {
                val ow = textMeasurePaint.measureText(other.text)
                val oRect = RectF(
                    other.x - padX * 0.5f,
                    other.y - padY * 0.5f,
                    other.x + ow + padX * 0.5f,
                    other.y + h + padY * 0.5f
                )
                if (RectF.intersects(myRect, oRect)) {
                    fy = oRect.top - h - padY
                    collided = true
                    break
                }
            }
            if (!collided) break
        }
        if (fy < 16f) fy = y
        floatingTexts.add(FloatingText(text, fx, fy, 380f, color))
    }

    private fun spawnBurst(x: Float, y: Float, colorName: String) {
        val (br, bg, bb) = colorMap[colorName] ?: Triple(255, 220, 150)
        val cx = x + flowerSize * 0.5f
        val cy = y + flowerSize * 0.5f
        for (i in 0 until 12) {
            val angle = Random.nextFloat() * (PI.toFloat() * 2f)
            val speed = Random.nextFloat() * 4.5f + 2.0f
            val vx = cos(angle) * speed
            val vy = sin(angle) * speed - 1.5f
            val rad = Random.nextFloat() * 4.0f + 4.0f
            burstParticles.add(BurstParticle(cx, cy, vx, vy, rad, 255f, br, bg, bb))
        }
    }

    private fun spawnZapShader(r: Int, c: Int) {
        sound.play("zap")
        val (fx, fy) = cellToXY(r, c)
        val cx = fx + flowerSize * 0.5f
        val cy = fy + flowerSize * 0.5f
        specialEffects.add(
            SpecialEffect(type = "zap", r = r, c = c, cx = cx, cy = cy, maxTimer = 24)
        )
        val sparkCols = arrayOf(
            Triple(255, 250, 110),
            Triple(130, 245, 255),
            Triple(255, 255, 230)
        )
        for (i in 0 until 28) {
            val px: Float
            val py: Float
            val vx: Float
            val vy: Float
            if (Random.nextBoolean()) {
                px = boardStartX + Random.nextFloat() * (boardCol * cellSize)
                py = cy + Random.nextFloat() * 20f - 10f
                vx = (if (Random.nextBoolean()) 1f else -1f) * (Random.nextFloat() * 6f + 3f)
                vy = Random.nextFloat() * 4.4f - 2.2f
            } else {
                px = cx + Random.nextFloat() * 20f - 10f
                py = boardStartY + Random.nextFloat() * (boardRow * cellSize)
                vx = Random.nextFloat() * 4.4f - 2.2f
                vy = (if (Random.nextBoolean()) 1f else -1f) * (Random.nextFloat() * 6f + 3f)
            }
            val (cr, cg, cb) = sparkCols[Random.nextInt(sparkCols.size)]
            burstParticles.add(BurstParticle(px, py, vx, vy, Random.nextFloat() * 3f + 3.5f, 255f, cr, cg, cb))
        }
    }

    private fun spawnRainbowShader(r: Int, c: Int, targetCells: List<Pair<Int, Int>>) {
        sound.play("rainbow")
        val (fx, fy) = cellToXY(r, c)
        val cx = fx + flowerSize * 0.5f
        val cy = fy + flowerSize * 0.5f
        val rainbowCols = arrayOf(
            Triple(255, 95, 120),
            Triple(255, 175, 85),
            Triple(255, 240, 100),
            Triple(110, 245, 150),
            Triple(95, 220, 255),
            Triple(175, 130, 255),
            Triple(255, 120, 225)
        )
        val targets = mutableListOf<Pair<Float, Float>>()
        for ((tr, tc) in targetCells) {
            val (tx, ty) = cellToXY(tr, tc)
            val tcx = tx + flowerSize * 0.5f
            val tcy = ty + flowerSize * 0.5f
            targets.add(tcx to tcy)
            for (i in 0 until 8) {
                val ang = Random.nextFloat() * (PI.toFloat() * 2f)
                val spd = Random.nextFloat() * 4.5f + 2.5f
                val (cr, cg, cb) = rainbowCols[Random.nextInt(rainbowCols.size)]
                burstParticles.add(
                    BurstParticle(
                        tcx,
                        tcy,
                        cos(ang) * spd,
                        sin(ang) * spd - 1.2f,
                        Random.nextFloat() * 3.5f + 4.5f,
                        255f,
                        cr,
                        cg,
                        cb
                    )
                )
            }
        }
        specialEffects.add(
            SpecialEffect(type = "rainbow", cx = cx, cy = cy, targets = targets, maxTimer = 30)
        )
    }

    private fun spawnBombShader(r: Int, c: Int, r0: Int, c0: Int) {
        sound.play("bomb")
        val (fx, fy) = cellToXY(r, c)
        val cx = fx + flowerSize * 0.5f
        val cy = fy + flowerSize * 0.5f
        val bx = boardStartX + c0 * cellSize
        val by = boardStartY + r0 * cellSize
        val bw = min(5, boardCol - c0) * cellSize
        val bh = min(5, boardRow - r0) * cellSize
        screenShake = max(screenShake, 10f)
        specialEffects.add(
            SpecialEffect(
                type = "bomb",
                cx = cx,
                cy = cy,
                rect = RectF(bx, by, bx + bw, by + bh),
                maxTimer = 28
            )
        )
        val fireCols = arrayOf(
            Triple(255, 120, 60),
            Triple(255, 210, 80),
            Triple(255, 90, 185),
            Triple(255, 245, 200)
        )
        for (i in 0 until 42) {
            val ang = Random.nextFloat() * (PI.toFloat() * 2f)
            val spd = Random.nextFloat() * 8.5f + 3.0f
            val (cr, cg, cb) = fireCols[Random.nextInt(fireCols.size)]
            burstParticles.add(
                BurstParticle(
                    cx + Random.nextFloat() * 36f - 18f,
                    cy + Random.nextFloat() * 36f - 18f,
                    cos(ang) * spd,
                    sin(ang) * spd - 1.5f,
                    Random.nextFloat() * 5f + 5.5f,
                    255f,
                    cr,
                    cg,
                    cb
                )
            )
        }
    }

    private fun checkBoard() {
        for (row in 0 until boardRow - 2) {
            for (col in 0 until boardCol) {
                val n = board[row][col]?.name ?: continue
                if (board[row + 1][col]?.name == n && board[row + 2][col]?.name == n) {
                    matchesFound.add(listOf(row to col, (row + 1) to col, (row + 2) to col))
                }
            }
        }
        for (col in 0 until boardCol - 2) {
            for (row in 0 until boardRow) {
                val n = board[row][col]?.name ?: continue
                if (board[row][col + 1]?.name == n && board[row][col + 2]?.name == n) {
                    matchesFound.add(listOf(row to col, row to (col + 1), row to (col + 2)))
                }
            }
        }
    }

    private fun deleteAndReplaceFlowers(instant: Boolean = false) {
        if (matchesFound.isEmpty()) {
            if (!instant) comboCount = 0
            return
        }

        val seen = mutableSetOf<Pair<Int, Int>>()
        val orderedPositions = mutableListOf<Pair<Int, Int>>()
        for (matchItem in matchesFound) {
            for (pos in matchItem) {
                if (seen.add(pos)) {
                    orderedPositions.add(pos)
                }
            }
        }
        matchesFound.clear()

        val expanded = orderedPositions.toMutableList()
        val expandedSet = orderedPositions.toMutableSet()
        for ((r, c) in orderedPositions) {
            val fl = board[r][c] ?: continue
            if (fl.special == "zap" || fl.special == "line") {
                if (!instant && userFirstMove) {
                    spawnZapShader(r, c)
                }
                for (cc in 0 until boardCol) {
                    if (expandedSet.add(r to cc)) expanded.add(r to cc)
                }
                for (rr in 0 until boardRow) {
                    if (expandedSet.add(rr to c)) expanded.add(rr to c)
                }
            } else if (fl.special == "bomb") {
                val r0 = max(0, min(boardRow - 5, r - 2))
                val c0 = max(0, min(boardCol - 5, c - 2))
                if (!instant && userFirstMove) {
                    spawnBombShader(r, c, r0, c0)
                }
                for (rr in r0 until min(boardRow, r0 + 5)) {
                    for (cc in c0 until min(boardCol, c0 + 5)) {
                        if (expandedSet.add(rr to cc)) expanded.add(rr to cc)
                    }
                }
            } else if (fl.special == "rainbow") {
                val targetColor = fl.name
                val rainbowTargets = mutableListOf<Pair<Int, Int>>()
                for (rr in 0 until boardRow) {
                    for (cc in 0 until boardCol) {
                        if (board[rr][cc]?.name == targetColor) {
                            rainbowTargets.add(rr to cc)
                            if (expandedSet.add(rr to cc)) expanded.add(rr to cc)
                        }
                    }
                }
                if (!instant && userFirstMove) {
                    spawnRainbowShader(r, c, rainbowTargets)
                }
            }
        }

        if (instant) {
            for ((r, c) in expanded) {
                val (tx, ty) = cellToXY(r, c)
                board[r][c] = createFlower(tx, ty)
            }
            return
        }

        val spawnPos = orderedPositions[0]
        val spawnColor = board[spawnPos.first][spawnPos.second]?.name ?: "red"
        val spawnSpecial = when {
            orderedPositions.size >= 6 -> "bomb"
            orderedPositions.size == 5 -> "rainbow"
            orderedPositions.size == 4 -> "zap"
            else -> null
        }

        if (userFirstMove) {
            comboCount += 1
            sound.playMatch(comboCount)
            val pointsEarned = expanded.size * 100 * comboCount
            userScore += pointsEarned
            saveCurrentScore()

            var sumX = 0f
            var sumY = 0f
            var countValid = 0
            for ((r, c) in expanded) {
                board[r][c]?.let {
                    sumX += it.x
                    sumY += it.y
                    countValid++
                }
            }
            val avgX = if (countValid > 0) sumX / countValid else 380f
            val avgY = if (countValid > 0) sumY / countValid else 300f
            val label = if (comboCount == 1) "+$pointsEarned" else "+$pointsEarned (${comboCount}x COMBO!)"
            addFloatingText(label, avgX, avgY, Color.rgb(255, 245, 140))

            val maxTime = 3599
            if (orderedPositions.size >= 5 && currentTime < maxTime) {
                val addedBonus = min(3, maxTime - currentTime)
                currentTime += addedBonus
                addFloatingText("+${addedBonus}s TIME BONUS!", avgX, avgY - 32f, Color.rgb(150, 255, 190))
            }

            if (userScore >= levelTarget) {
                level += 1
                levelTarget += level * 1800
                val addedLvl = max(0, min(15, maxTime - currentTime))
                currentTime += addedLvl
                shufflesLeft = min(5, shufflesLeft + 1)
                sound.play("levelup")
                val lvlMsg = if (addedLvl > 0) "LEVEL $level! +${addedLvl}s" else "LEVEL $level!"
                addFloatingText(lvlMsg, 380f, 300f, Color.rgb(255, 210, 255))
            }
        }

        for ((r, c) in expanded) {
            val fl = board[r][c]
            if (fl != null && userFirstMove) {
                spawnBurst(fl.x, fl.y, fl.name)
            }
            board[r][c] = null
        }

        if (userFirstMove && spawnSpecial != null) {
            val (sr, sc) = spawnPos
            val (tx, ty) = cellToXY(sr, sc)
            board[sr][sc] = Flower(
                name = spawnColor,
                x = tx,
                y = ty,
                targetX = tx,
                targetY = ty,
                surf = getFlowerSurf(spawnColor, spawnSpecial),
                special = spawnSpecial
            )
        }

        for (c in 0 until boardCol) {
            val remaining = mutableListOf<Flower>()
            for (r in boardRow - 1 downTo 0) {
                board[r][c]?.let { remaining.add(it) }
            }
            val missingCount = boardRow - remaining.size
            for ((idxFromBottom, fl) in remaining.withIndex()) {
                val targetR = boardRow - 1 - idxFromBottom
                val (tx, ty) = cellToXY(targetR, c)
                fl.targetX = tx
                fl.targetY = ty
                board[targetR][c] = fl
            }
            for (m in 0 until missingCount) {
                val targetR = missingCount - 1 - m
                val (tx, ty) = cellToXY(targetR, c)
                val startY = boardStartY - (m + 1) * cellSize
                val newFl = createFlower(tx, startY)
                newFl.targetX = tx
                newFl.targetY = ty
                board[targetR][c] = newFl
            }
        }

        isFalling = true
        hintPair = null
        lastActionTimeMs = ticksMs()
    }

    private fun checkMove(pos1: Pair<Int, Int>, pos2: Pair<Int, Int>): SwapAnim? {
        val (r1, c1) = pos1
        val (r2, c2) = pos2
        if (r1 == r2 && c1 == c2) return null
        if (max(abs(r1 - r2), abs(c1 - c2)) != 1) return null

        val f1 = board[r1][c1] ?: return null
        val f2 = board[r2][c2] ?: return null
        val (t1x, t1y) = cellToXY(r2, c2)
        val (t2x, t2y) = cellToXY(r1, c1)

        board[r1][c1] = f2
        board[r2][c2] = f1

        userFirstMove = true
        comboCount = 0
        hintPair = null
        lastActionTimeMs = ticksMs()
        sound.play("swap")
        return SwapAnim(f1, f2, t1x, t1y, t2x, t2y, r1, c1, r2, c2)
    }

    private fun getCellAtPos(vx: Float, vy: Float): Pair<Int, Int>? {
        if (vx < boardStartX || vy < boardStartY) return null
        val c = ((vx - boardStartX) / cellSize).toInt()
        val r = ((vy - boardStartY) / cellSize).toInt()
        if (r in 0 until boardRow && c in 0 until boardCol) {
            return r to c
        }
        return null
    }

    private fun triggerTimeOver() {
        if (isTimeOver) return
        currentTime = 0
        isTimeOver = true
        timeOverStartMs = ticksMs()
        animData = null
        isFalling = false
        flowersSelected.clear()
        hintPair = null
        dragStartCell = null
        saveCurrentScore()
        sound.play("gameover")

        timeOverFlowers.clear()
        for (r in 0 until boardRow) {
            for (c in 0 until boardCol) {
                val fl = board[r][c] ?: continue
                val delay = (boardRow - 1 - r) * 3f + abs(c - 4.5f) * 1.5f + Random.nextFloat() * 4f
                val vx = Random.nextFloat() * 7.2f - 3.6f
                val vy = -(Random.nextFloat() * 3.7f + 1.5f)
                val angVel = (if (Random.nextBoolean()) 1f else -1f) * (Random.nextFloat() * 6f + 3.5f)
                timeOverFlowers.add(
                    TimeOverFlower(fl.surf, fl.x, fl.y, vx, vy, 0f, angVel, delay, fl.name, false)
                )
            }
        }
    }

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
        val sx = w.toFloat() / virtualW
        val sy = h.toFloat() / virtualH
        viewScale = min(sx, sy)
        viewOffsetX = (w - virtualW * viewScale) * 0.5f
        viewOffsetY = (h - virtualH * viewScale) * 0.5f
    }

    private fun toVirtualX(screenX: Float): Float = (screenX - viewOffsetX) / viewScale
    private fun toVirtualY(screenY: Float): Float = (screenY - viewOffsetY) / viewScale

    override fun onTouchEvent(event: MotionEvent): Boolean {
        val vx = toVirtualX(event.x)
        val vy = toVirtualY(event.y)
        lastTouchX = vx
        lastTouchY = vy

        when (mode) {
            GameMode.MAIN_MENU -> handleMainMenuTouch(event, vx, vy)
            GameMode.GAME_SCREEN -> handleGameScreenTouch(event, vx, vy)
            GameMode.END_SCREEN -> handleEndScreenTouch(event)
        }
        return true
    }

    private fun handleMainMenuTouch(event: MotionEvent, vx: Float, vy: Float) {
        if (event.action == MotionEvent.ACTION_UP) {
            if (showCreditsModal) {
                sound.play("select")
                if (creditsUrlRect.contains(vx, vy)) {
                    try {
                        val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://knrf.itch.io/"))
                        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        context.startActivity(intent)
                    } catch (_: Exception) {
                    }
                } else {
                    showCreditsModal = false
                }
                return
            }
            if (titleRect.contains(vx, vy)) {
                titleColorIndex = (titleColorIndex + 1) % titlePalette.size
                val now = ticksMs()
                titleClickTimes.removeAll { now - it > 30000L }
                titleClickTimes.add(now)
                if (titleClickTimes.size >= 10) {
                    showCreditsModal = true
                    titleClickTimes.clear()
                    sound.play("levelup")
                } else {
                    sound.play("select")
                }
            } else {
                sound.play("select")
                resetGameScreen()
                mode = GameMode.GAME_SCREEN
            }
        }
    }

    private fun handleEndScreenTouch(event: MotionEvent) {
        if (event.action == MotionEvent.ACTION_UP) {
            sound.play("select")
            highScores = HighScoreManager.loadScores(context)
            mode = GameMode.MAIN_MENU
        }
    }

    private fun handleGameScreenTouch(event: MotionEvent, vx: Float, vy: Float) {
        if (showHowToPlay) {
            if (event.action == MotionEvent.ACTION_UP) {
                sound.play("select")
                showHowToPlay = false
                lastActionTimeMs = ticksMs()
                lastSecondTickMs = ticksMs()
            }
            return
        }

        if (isTimeOver) {
            if (event.action == MotionEvent.ACTION_UP && ticksMs() - timeOverStartMs > 1200L) {
                goToEndScreen()
            }
            return
        }

        when (event.action) {
            MotionEvent.ACTION_DOWN -> {
                if (animData == null && !isFalling) {
                    hintPair = null
                    lastActionTimeMs = ticksMs()
                    if (shuffleBtnRect.contains(vx, vy) && shufflesLeft > 0) {
                        shufflesLeft -= 1
                        shuffleBoard()
                    } else if (helpBtnRect.contains(vx, vy)) {
                        sound.play("select")
                        showHowToPlay = true
                    } else {
                        dragStartCell = getCellAtPos(vx, vy)
                    }
                }
            }
            MotionEvent.ACTION_MOVE -> {
                val startCell = dragStartCell
                if (startCell != null && animData == null && !isFalling) {
                    val curCell = getCellAtPos(vx, vy)
                    if (curCell != null && curCell != startCell) {
                        if (max(abs(curCell.first - startCell.first), abs(curCell.second - startCell.second)) == 1) {
                            animData = checkMove(startCell, curCell)
                            flowersSelected.clear()
                            dragStartCell = null
                        }
                    }
                }
            }
            MotionEvent.ACTION_UP -> {
                hintPair = null
                lastActionTimeMs = ticksMs()
                val startCell = dragStartCell
                if (animData == null && !isFalling && startCell != null) {
                    val clickedPos = getCellAtPos(vx, vy)
                    if (clickedPos != null) {
                        if (clickedPos != startCell &&
                            max(abs(clickedPos.first - startCell.first), abs(clickedPos.second - startCell.second)) == 1
                        ) {
                            animData = checkMove(startCell, clickedPos)
                            flowersSelected.clear()
                        } else if (flowersSelected.size == 1 && flowersSelected[0] == clickedPos) {
                            flowersSelected.clear()
                        } else {
                            sound.play("select")
                            flowersSelected.add(clickedPos)
                            if (flowersSelected.size == 2) {
                                animData = checkMove(flowersSelected[0], flowersSelected[1])
                                if (animData == null) {
                                    flowersSelected.clear()
                                    flowersSelected.add(clickedPos)
                                } else {
                                    flowersSelected.clear()
                                }
                            }
                        }
                    }
                }
                dragStartCell = null
            }
        }
    }

    private fun goToEndScreen() {
        saveCurrentScore()
        finalScore = userScore
        highScores = HighScoreManager.loadScores(context)
        mode = GameMode.END_SCREEN
    }

    private fun updateClouds() {
        val t = ticksMs() * 0.0012f
        var a1 = cloud1XY.first + 0.42f + sin(t * 0.55f) * 0.08f
        if (a1 > 1380f) a1 = -420f
        cloud1XY = a1 to (22f + sin(t * 0.85f) * 5f)

        var a2 = cloud2XY.first + 0.19f + sin(t * 0.55f + 2.1f) * 0.05f
        if (a2 > 1380f) a2 = -260f
        cloud2XY = a2 to (135f + sin(t * 0.85f + 2.1f) * 3.5f)

        var a3 = cloud3XY.first + 0.30f + sin(t * 0.55f + 4.2f) * 0.06f
        if (a3 > 1380f) a3 = -320f
        cloud3XY = a3 to (72f + sin(t * 0.85f + 4.2f) * 4.5f)
    }

    private fun updateGameLogic() {
        val now = ticksMs()
        if (!showHowToPlay && !isTimeOver) {
            if (now - lastSecondTickMs >= 1000L) {
                lastSecondTickMs += 1000L
                currentTime -= 1
                if (currentTime in 1..10) {
                    sound.play("tick")
                }
                if (currentTime <= 0) {
                    triggerTimeOver()
                    return
                }
            }
        } else {
            lastSecondTickMs = now
        }

        if (isTimeOver) {
            if (now - timeOverStartMs >= 3200L) {
                goToEndScreen()
            }
            return
        }

        val curAnim = animData
        if (curAnim != null) {
            for ((fl, tx, ty) in arrayOf(
                Triple(curAnim.f1, curAnim.t1x, curAnim.t1y),
                Triple(curAnim.f2, curAnim.t2x, curAnim.t2y)
            )) {
                fl.x = if (abs(fl.x - tx) <= flowerMatchSpeedAnim) tx
                else if (fl.x < tx) fl.x + flowerMatchSpeedAnim else fl.x - flowerMatchSpeedAnim

                fl.y = if (abs(fl.y - ty) <= flowerMatchSpeedAnim) ty
                else if (fl.y < ty) fl.y + flowerMatchSpeedAnim else fl.y - flowerMatchSpeedAnim
            }
            lastActionTimeMs = now
            if (abs(curAnim.f1.x - curAnim.t1x) < 0.5f &&
                abs(curAnim.f1.y - curAnim.t1y) < 0.5f &&
                abs(curAnim.f2.x - curAnim.t2x) < 0.5f &&
                abs(curAnim.f2.y - curAnim.t2y) < 0.5f
            ) {
                animData = null
            }
        } else if (isFalling) {
            var stillFalling = false
            for (r in 0 until boardRow) {
                for (c in 0 until boardCol) {
                    val fl = board[r][c] ?: continue
                    if (abs(fl.y - fl.targetY) > 0.5f) {
                        stillFalling = true
                        fl.y = if (fl.y < fl.targetY) {
                            min(fl.targetY, fl.y + fallSpeed)
                        } else {
                            max(fl.targetY, fl.y - fallSpeed)
                        }
                    } else {
                        fl.y = fl.targetY
                    }
                }
            }
            isFalling = stillFalling
            lastActionTimeMs = now
        } else {
            checkBoard()
            if (matchesFound.isNotEmpty()) {
                deleteAndReplaceFlowers(instant = false)
            } else if (!showHowToPlay) {
                if (hintPair == null && now - lastActionTimeMs > 6000L) {
                    val move = findHintMove()
                    if (move != null) {
                        hintPair = move
                    } else {
                        shuffleBoard()
                    }
                }
            }
        }
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        canvas.drawColor(Color.BLACK)

        canvas.save()
        canvas.translate(viewOffsetX, viewOffsetY)
        canvas.scale(viewScale, viewScale)
        canvas.clipRect(0f, 0f, virtualW, virtualH)

        when (mode) {
            GameMode.MAIN_MENU -> {
                updateClouds()
                drawMainMenu(canvas)
            }
            GameMode.GAME_SCREEN -> {
                updateGameLogic()
                drawGameScreen(canvas)
            }
            GameMode.END_SCREEN -> {
                updateClouds()
                drawEndScreen(canvas)
            }
        }

        canvas.restore()
        if (!isPaused) {
            postInvalidateOnAnimation()
        }
    }

    private fun getMenuClouds(): List<Pair<Bitmap, Pair<Float, Float>>> {
        val list = mutableListOf<Pair<Bitmap, Pair<Float, Float>>>()
        cloud1Bmp?.let { list.add(it to cloud1XY) }
        cloud2Bmp?.let { list.add(it to cloud2XY) }
        cloud3Bmp?.let { list.add(it to cloud3XY) }
        return list
    }

    private fun drawMainMenu(canvas: Canvas) {
        val now = ticksMs()
        val t = now * 0.003f
        shader.drawParallaxBackground(canvas, now, lastTouchX, lastTouchY, getMenuClouds(), muted = false)
        shader.drawAtmosphere(canvas, now)

        val (mainCol, glowCol) = titlePalette[titleColorIndex]
        val titleStr = "Flowers"
        textMeasurePaint.textSize = 92f
        val tw = textMeasurePaint.measureText(titleStr)
        val tx = (virtualW - tw) * 0.5f
        val ty = 20f + sin(t * 1.6f) * 6f
        titleRect.set(tx - 12f, ty - 6f, tx + tw + 12f, ty + 108f)
        shader.drawGlowText(canvas, typeface, 92f, titleStr, tx, ty, mainCol, glowCol, offset = 4f)
        shader.drawGlowText(
            canvas,
            typeface,
            26f,
            "Android Version",
            0f,
            212f + sin(t * 1.6f) * 3f,
            mainColor = Color.rgb(160, 255, 210),
            offset = 2f,
            centerWidth = virtualW
        )

        val subStr = "Swap blooms in 8 directions, trigger cascading combos & race the clock!"
        val sw = 1040f
        val sh = 52f
        val sx = (virtualW - sw) * 0.5f
        val sy = 135f + sin(t * 1.6f) * 4f
        shader.drawGlowPanel(canvas, now, sx, sy, sw, sh)
        shader.drawGlowText(
            canvas,
            typeface,
            27f,
            subStr,
            sx,
            sy + 10f,
            mainColor = Color.rgb(255, 245, 190),
            offset = 2f,
            maxWidth = sw - 32f,
            centerWidth = sw
        )

        val hsW = 430f
        val hsH = 215f
        val hsX = (virtualW - hsW) * 0.5f
        val hsY = 285f
        shader.drawGlowPanel(canvas, now, hsX, hsY, hsW, hsH)
        shader.drawGlowText(
            canvas,
            typeface,
            36f,
            "Top 3 High Scores",
            hsX,
            hsY + 14f,
            mainColor = Color.rgb(255, 235, 150),
            offset = 2f,
            maxWidth = hsW - 32f,
            centerWidth = hsW
        )
        val medalCols = intArrayOf(
            Color.rgb(255, 235, 130),
            Color.rgb(225, 235, 255),
            Color.rgb(255, 195, 150)
        )
        for (idx in 0 until 3) {
            val scoreTxt = if (idx < highScores.size) "${highScores[idx]} pts" else "---"
            shader.drawGlowText(
                canvas,
                typeface,
                27f,
                "#${idx + 1}    $scoreTxt",
                hsX,
                hsY + 72f + idx * 44f,
                mainColor = medalCols[idx],
                offset = 2f,
                maxWidth = hsW - 32f,
                centerWidth = hsW
            )
        }

        val startStr = "Tap anywhere to start!"
        textMeasurePaint.textSize = 36f
        val bw = textMeasurePaint.measureText(startStr) + 64f
        val bh = 68f
        val bx = (virtualW - bw) * 0.5f
        val by = 615f
        shader.drawGlowPanel(canvas, now, bx, by, bw, bh, hovered = !showCreditsModal)
        shader.drawGlowText(canvas, typeface, 36f, startStr, bx, by + 14f, offset = 2f, centerWidth = bw)

        if (showCreditsModal) {
            paint.style = Paint.Style.FILL
            paint.color = Color.argb(185, 12, 6, 30)
            canvas.drawRect(0f, 0f, virtualW, virtualH, paint)
            val mw = 680f
            val mh = 330f
            val mx = (virtualW - mw) * 0.5f
            val my = (virtualH - mh) * 0.5f
            shader.drawGlowPanel(canvas, now, mx, my, mw, mh, hovered = true)
            shader.drawGlowText(
                canvas,
                typeface,
                64f,
                "Made by Frank Mulvie",
                mx,
                my + 30f,
                mainColor = Color.rgb(255, 240, 150),
                offset = 3f,
                maxWidth = mw - 48f,
                centerWidth = mw
            )
            shader.drawGlowText(
                canvas,
                typeface,
                36f,
                "Version 1.0.0",
                mx,
                my + 125f,
                mainColor = Color.rgb(180, 240, 255),
                offset = 2f,
                maxWidth = mw - 48f,
                centerWidth = mw
            )
            creditsUrlRect.set(mx + 120f, my + 180f, mx + mw - 120f, my + 228f)
            shader.drawGlowText(
                canvas,
                typeface,
                36f,
                "https://knrf.itch.io/",
                mx,
                my + 185f,
                mainColor = Color.rgb(255, 185, 245),
                offset = 2f,
                maxWidth = mw - 48f,
                centerWidth = mw
            )
            shader.drawGlowText(
                canvas,
                typeface,
                27f,
                "Tap anywhere to close",
                mx,
                my + 255f,
                mainColor = Color.rgb(230, 225, 255),
                offset = 2f,
                maxWidth = mw - 48f,
                centerWidth = mw
            )
        }
    }

    private fun drawBoardBorderShader(canvas: Canvas, now: Long) {
        val boardW = boardCol * cellSize
        val boardH = boardRow * cellSize
        val bx = boardStartX
        val by = boardStartY
        val cycleDuration = 5500f
        val totalPos = now / cycleDuration
        val idx = totalPos.toInt() % boardPulsePalette.size
        val nxt = (idx + 1) % boardPulsePalette.size
        val rawT = totalPos - totalPos.toInt()
        val blend = rawT * rawT * (3f - 2f * rawT)

        val (c1, b1) = boardPulsePalette[idx]
        val (c2, b2) = boardPulsePalette[nxt]
        val glowR = (c1.first + (c2.first - c1.first) * blend).toInt()
        val glowG = (c1.second + (c2.second - c1.second) * blend).toInt()
        val glowB = (c1.third + (c2.third - c1.third) * blend).toInt()
        val bgR = (b1.first + (b2.first - b1.first) * blend).toInt()
        val bgG = (b1.second + (b2.second - b1.second) * blend).toInt()
        val bgB = (b1.third + (b2.third - b1.third) * blend).toInt()

        val breath = (sin(now * 0.0022f) + 1f) * 0.5f

        paint.style = Paint.Style.FILL
        paint.color = Color.argb(145, bgR, bgG, bgB)
        rectF.set(bx - 12f, by - 12f, bx + boardW + 12f, by + boardH + 12f)
        canvas.drawRoundRect(rectF, 16f, 16f, paint)

        paint.style = Paint.Style.STROKE
        paint.strokeWidth = 1f
        paint.color = Color.argb(38, glowR, glowG, glowB)
        for (r in 0 until boardRow) {
            for (c in 0 until boardCol) {
                val cx = bx + c * cellSize + 3f
                val cy = by + r * cellSize + 3f
                rectF.set(cx, cy, cx + cellSize - 6f, cy + cellSize - 6f)
                canvas.drawRoundRect(rectF, 10f, 10f, paint)
            }
        }

        paint.strokeWidth = 4f
        for (layer in 5 downTo 1) {
            val spread = layer * 3f
            val alpha = ((42f + 22f * breath) * (6 - layer) / 5f).toInt().coerceIn(0, 255)
            paint.color = Color.argb(alpha, glowR, glowG, glowB)
            rectF.set(
                bx - 12f - spread,
                by - 12f - spread,
                bx + boardW + 12f + spread,
                by + boardH + 12f + spread
            )
            canvas.drawRoundRect(rectF, 16f + spread, 16f + spread, paint)
        }

        paint.strokeWidth = 3f
        paint.color = Color.argb(
            245,
            min(255, glowR + 55),
            min(255, glowG + 55),
            min(255, glowB + 55)
        )
        rectF.set(bx - 12f, by - 12f, bx + boardW + 12f, by + boardH + 12f)
        canvas.drawRoundRect(rectF, 16f, 16f, paint)
    }

    private fun drawLightningBolt(
        canvas: Canvas,
        x1: Float,
        y1: Float,
        x2: Float,
        y2: Float,
        glowColor: Int,
        coreColor: Int,
        width: Float,
        segments: Int,
        jitter: Float
    ) {
        val dx = (x2 - x1) / segments
        val dy = (y2 - y1) / segments
        val plen = hypot(-dy, dx).coerceAtLeast(1f)
        val px = -dy / plen
        val py = dx / plen

        val ptsX = FloatArray(segments + 1)
        val ptsY = FloatArray(segments + 1)
        ptsX[0] = x1
        ptsY[0] = y1
        for (i in 1 until segments) {
            val off = (Random.nextFloat() * 2f - 1f) * jitter
            ptsX[i] = x1 + dx * i + px * off
            ptsY[i] = y1 + dy * i + py * off
        }
        ptsX[segments] = x2
        ptsY[segments] = y2

        paint.style = Paint.Style.STROKE
        paint.strokeCap = Paint.Cap.ROUND
        paint.strokeWidth = width + 4f
        paint.color = glowColor
        for (i in 0 until segments) {
            canvas.drawLine(ptsX[i], ptsY[i], ptsX[i + 1], ptsY[i + 1], paint)
        }
        paint.strokeWidth = max(2f, width)
        paint.color = coreColor
        for (i in 0 until segments) {
            canvas.drawLine(ptsX[i], ptsY[i], ptsX[i + 1], ptsY[i + 1], paint)
        }
    }

    private fun drawEffects(canvas: Canvas) {
        if (specialEffects.isNotEmpty()) {
            val boardW = boardCol * cellSize
            val boardH = boardRow * cellSize
            val rainbowPalette = arrayOf(
                Triple(255, 80, 110),
                Triple(255, 165, 70),
                Triple(255, 240, 90),
                Triple(95, 245, 145),
                Triple(85, 215, 255),
                Triple(170, 120, 255),
                Triple(255, 110, 220)
            )
            val iter = specialEffects.iterator()
            while (iter.hasNext()) {
                val eff = iter.next()
                eff.timer += 1
                if (eff.timer > eff.maxTimer) {
                    iter.remove()
                    continue
                }
                val prog = eff.timer.toFloat() / eff.maxTimer.toFloat()
                val fade = 1f - prog

                when (eff.type) {
                    "zap" -> {
                        val rowY = boardStartY + eff.r * cellSize
                        val colX = boardStartX + eff.c * cellSize
                        val beamAlpha = (175f * fade.pow(0.8f)).toInt().coerceIn(0, 255)
                        val coreAlpha = (245f * fade).toInt().coerceIn(0, 255)

                        paint.style = Paint.Style.FILL
                        paint.color = Color.argb(beamAlpha / 2, 255, 225, 70)
                        rectF.set(boardStartX, rowY + 8f, boardStartX + boardW, rowY + cellSize - 8f)
                        canvas.drawRoundRect(rectF, 12f, 12f, paint)
                        rectF.set(colX + 8f, boardStartY, colX + cellSize - 8f, boardStartY + boardH)
                        canvas.drawRoundRect(rectF, 12f, 12f, paint)

                        drawLightningBolt(
                            canvas,
                            boardStartX,
                            eff.cy,
                            boardStartX + boardW,
                            eff.cy,
                            Color.argb(beamAlpha, 255, 230, 60),
                            Color.argb(coreAlpha, 255, 255, 235),
                            width = 4f,
                            segments = 16,
                            jitter = 13f * fade + 3f
                        )
                        drawLightningBolt(
                            canvas,
                            eff.cx,
                            boardStartY,
                            eff.cx,
                            boardStartY + boardH,
                            Color.argb(beamAlpha, 120, 240, 255),
                            Color.argb(coreAlpha, 255, 255, 235),
                            width = 4f,
                            segments = 14,
                            jitter = 13f * fade + 3f
                        )
                        paint.style = Paint.Style.FILL
                        paint.color = Color.argb(beamAlpha, 255, 250, 150)
                        canvas.drawCircle(eff.cx, eff.cy, 38f * fade + 10f, paint)
                        paint.color = Color.argb(coreAlpha, 255, 255, 255)
                        canvas.drawCircle(eff.cx, eff.cy, 18f * fade + 4f, paint)
                    }

                    "rainbow" -> {
                        val alpha = (235f * fade).toInt().coerceIn(0, 255)
                        val baseRad = 18f + prog * 360f
                        paint.style = Paint.Style.STROKE
                        paint.strokeWidth = 4f
                        for ((idx, rgb) in rainbowPalette.withIndex()) {
                            val rad = max(4f, baseRad - idx * 5f)
                            paint.color = Color.argb((alpha * 0.75f).toInt(), rgb.first, rgb.second, rgb.third)
                            canvas.drawCircle(eff.cx, eff.cy, rad, paint)
                        }

                        for ((idx, target) in eff.targets.withIndex()) {
                            val col1 = rainbowPalette[(idx + eff.timer) % rainbowPalette.size]
                            val col2 = rainbowPalette[(idx + eff.timer + 2) % rainbowPalette.size]
                            paint.style = Paint.Style.STROKE
                            paint.strokeWidth = 7f
                            paint.color = Color.argb((alpha * 0.7f).toInt(), col1.first, col1.second, col1.third)
                            canvas.drawLine(eff.cx, eff.cy, target.first, target.second, paint)

                            paint.strokeWidth = 3f
                            paint.color = Color.argb(alpha, col2.first, col2.second, col2.third)
                            canvas.drawLine(eff.cx, eff.cy, target.first, target.second, paint)

                            paint.strokeWidth = 1.5f
                            paint.color = Color.argb(alpha, 255, 255, 255)
                            canvas.drawLine(eff.cx, eff.cy, target.first, target.second, paint)

                            val burstR = 12f + 16f * sin(prog * PI.toFloat())
                            paint.style = Paint.Style.FILL
                            paint.color = Color.argb((alpha * 0.65f).toInt(), col1.first, col1.second, col1.third)
                            canvas.drawCircle(target.first, target.second, burstR, paint)
                            paint.color = Color.argb(alpha, 255, 255, 255)
                            canvas.drawCircle(target.first, target.second, max(3f, burstR * 0.5f), paint)
                        }
                    }

                    "bomb" -> {
                        val alpha = (230f * fade.pow(0.85f)).toInt().coerceIn(0, 255)
                        paint.style = Paint.Style.FILL
                        paint.color = Color.argb((120f * fade).toInt(), 255, 95, 50)
                        canvas.drawRoundRect(eff.rect, 18f, 18f, paint)

                        paint.style = Paint.Style.STROKE
                        paint.strokeWidth = 4f
                        paint.color = Color.argb(alpha, 255, 220, 110)
                        canvas.drawRoundRect(eff.rect, 18f, 18f, paint)

                        val maxRad = max(eff.rect.width(), eff.rect.height()) * 0.62f
                        val shockRad = max(8f, prog * maxRad)
                        val innerRad = max(4f, (1f - prog * 0.5f) * maxRad * 0.55f)

                        paint.style = Paint.Style.FILL
                        paint.color = Color.argb((155f * fade).toInt(), 255, 110, 45)
                        canvas.drawCircle(eff.cx, eff.cy, innerRad, paint)
                        paint.color = Color.argb((210f * fade).toInt(), 255, 235, 140)
                        canvas.drawCircle(eff.cx, eff.cy, innerRad * 0.6f, paint)

                        paint.style = Paint.Style.STROKE
                        paint.strokeWidth = 6f
                        paint.color = Color.argb(alpha, 255, 95, 195)
                        canvas.drawCircle(eff.cx, eff.cy, shockRad, paint)
                        paint.strokeWidth = 3f
                        paint.color = Color.argb(alpha, 255, 245, 170)
                        canvas.drawCircle(eff.cx, eff.cy, max(4f, shockRad - 10f), paint)
                    }
                }
            }
        }

        if (burstParticles.isNotEmpty()) {
            paint.style = Paint.Style.FILL
            val iter = burstParticles.iterator()
            while (iter.hasNext()) {
                val p = iter.next()
                p.x += p.vx
                p.y += p.vy
                p.vy += 0.22f
                p.alpha -= 9f
                if (p.alpha <= 0f) {
                    iter.remove()
                    continue
                }
                val a = p.alpha.toInt().coerceIn(0, 255)
                paint.color = Color.argb(a / 2, p.r, p.g, p.b)
                canvas.drawCircle(p.x, p.y, p.radius * 1.8f, paint)
                paint.color = Color.argb(a, p.r, p.g, p.b)
                canvas.drawCircle(p.x, p.y, p.radius, paint)
                paint.color = Color.argb(a, 255, 255, 255)
                canvas.drawCircle(p.x, p.y, max(1f, p.radius * 0.4f), paint)
            }
        }

        if (floatingTexts.isNotEmpty()) {
            val iter = floatingTexts.iterator()
            while (iter.hasNext()) {
                val ft = iter.next()
                ft.y -= 0.75f
                ft.alpha -= 2.4f
                if (ft.alpha <= 0f) {
                    iter.remove()
                    continue
                }
                val a = min(255, ft.alpha.toInt())
                val mainCol = Color.argb(a, Color.red(ft.color), Color.green(ft.color), Color.blue(ft.color))
                val glowCol = Color.argb(a, 60, 20, 120)
                shader.drawGlowText(canvas, typeface, 30f, ft.text, ft.x, ft.y, mainCol, glowCol, offset = 2f)
            }
        }
    }

    private fun drawGameScreen(canvas: Canvas) {
        val now = ticksMs()
        shader.drawParallaxBackground(canvas, now, lastTouchX, lastTouchY, muted = true)
        shader.drawAtmosphere(canvas, now)

        val hudX = 875f
        val hudY = 60f
        val hudW = 355f
        val hudH = 435f
        val padX = hudX + 22f
        val innerW = hudW - 44f

        shader.drawGlowPanel(canvas, now, hudX, hudY, hudW, hudH)
        shader.drawGlowText(
            canvas, typeface, 30f, "Level $level", padX, 70f,
            mainColor = Color.rgb(180, 240, 255), offset = 2f, maxWidth = innerW
        )
        shader.drawGlowText(
            canvas, typeface, 30f, "Score: $userScore", padX, 112f,
            mainColor = Color.rgb(255, 240, 170), offset = 2f, maxWidth = innerW
        )
        shader.drawGlowText(
            canvas, typeface, 21f, "High Score: ${max(bestScore, userScore)}", padX, 154f,
            mainColor = Color.rgb(210, 255, 195), offset = 1f, maxWidth = innerW
        )

        val prevTarget = if (level > 1) (level - 1) * 1500 else 0
        val span = max(1, levelTarget - prevTarget)
        val prog = ((userScore - prevTarget).toFloat() / span.toFloat()).coerceIn(0f, 1f)
        val barX = padX
        val barY = 196f
        val barW = innerW
        val barH = 18f
        paint.style = Paint.Style.FILL
        paint.color = Color.rgb(25, 15, 55)
        rectF.set(barX, barY, barX + barW, barY + barH)
        canvas.drawRoundRect(rectF, 9f, 9f, paint)
        if (prog > 0f) {
            paint.color = Color.rgb(140, 235, 255)
            rectF.set(barX, barY, barX + barW * prog, barY + barH)
            canvas.drawRoundRect(rectF, 9f, 9f, paint)
        }
        paint.style = Paint.Style.STROKE
        paint.strokeWidth = 2f
        paint.color = Color.rgb(210, 180, 255)
        rectF.set(barX, barY, barX + barW, barY + barH)
        canvas.drawRoundRect(rectF, 9f, 9f, paint)

        shader.drawGlowText(
            canvas, typeface, 21f, "Next Level: $levelTarget", padX, 222f,
            offset = 1f, maxWidth = innerW
        )

        val timeCol = if (currentTime <= 10) Color.rgb(255, 110, 110) else Color.rgb(245, 235, 255)
        val mins = max(0, currentTime) / 60
        val secs = max(0, currentTime) % 60
        val timeStr = String.format("Time: %02d:%02d", mins, secs)
        shader.drawGlowText(
            canvas, typeface, 30f, timeStr, padX, 258f,
            mainColor = timeCol, offset = 2f, maxWidth = innerW
        )
        if (comboCount > 1) {
            shader.drawGlowText(
                canvas, typeface, 30f, "Combo: ${comboCount}x!", padX, 300f,
                mainColor = Color.rgb(255, 220, 120), offset = 2f, maxWidth = innerW
            )
        }

        shader.drawGlowText(
            canvas, typeface, 21f, "8-Way & Drag Swap Enabled", padX, 344f,
            mainColor = Color.rgb(210, 210, 255), offset = 1f, maxWidth = innerW
        )
        shader.drawGlowText(
            canvas, typeface, 21f, "Match 4: Zap (Clears Row & Col)", padX, 378f,
            mainColor = Color.rgb(255, 235, 140), offset = 1f, maxWidth = innerW
        )
        shader.drawGlowText(
            canvas, typeface, 21f, "Match 5: Rainbow (Clears Color)", padX, 410f,
            mainColor = Color.rgb(255, 195, 245), offset = 1f, maxWidth = innerW
        )
        shader.drawGlowText(
            canvas, typeface, 21f, "Match 6+: Bomb (5x5 Blast)", padX, 442f,
            mainColor = Color.rgb(160, 255, 210), offset = 1f, maxWidth = innerW
        )

        shader.drawGlowPanel(
            canvas, now, shuffleBtnRect.left, shuffleBtnRect.top,
            shuffleBtnRect.width(), shuffleBtnRect.height(),
            hovered = shufflesLeft > 0 && !showHowToPlay
        )
        shader.drawGlowText(
            canvas, typeface, 30f, "Shuffle ($shufflesLeft)",
            shuffleBtnRect.left, shuffleBtnRect.top + 12f,
            offset = 2f, maxWidth = shuffleBtnRect.width() - 28f, centerWidth = shuffleBtnRect.width()
        )

        shader.drawGlowPanel(
            canvas, now, helpBtnRect.left, helpBtnRect.top,
            helpBtnRect.width(), helpBtnRect.height(),
            hovered = !showHowToPlay
        )
        shader.drawGlowText(
            canvas, typeface, 30f, "How to Play",
            helpBtnRect.left, helpBtnRect.top + 12f,
            offset = 2f, maxWidth = helpBtnRect.width() - 28f, centerWidth = helpBtnRect.width()
        )

        drawBoard(canvas, now)

        if (showHowToPlay) {
            drawHowToPlayModal(canvas, now)
        }
    }

    private fun drawBoard(canvas: Canvas, now: Long) {
        drawBoardBorderShader(canvas, now)
        if (isTimeOver) {
            drawTimeOverShader(canvas, now)
            drawEffects(canvas)
            return
        }

        val selectedSet = flowersSelected.toSet()
        val hintSet = hintPair?.let { setOf(it.first, it.second) } ?: emptySet()
        val t = now * 0.015f

        var shakeX = 0f
        var shakeY = 0f
        if (screenShake > 0.2f) {
            shakeX = (Random.nextFloat() * 2f - 1f) * screenShake
            shakeY = (Random.nextFloat() * 2f - 1f) * screenShake
            screenShake *= 0.84f
        } else {
            screenShake = 0f
        }

        for (r in 0 until boardRow) {
            for (c in 0 until boardCol) {
                val flower = board[r][c] ?: continue
                var drawX = flower.x + shakeX
                val drawY = flower.y + shakeY
                val pos = r to c

                if (pos in hintSet) {
                    drawX += sin(t) * 3.5f
                    paint.style = Paint.Style.STROKE
                    paint.strokeWidth = 3f
                    paint.color = Color.argb(180, 120, 255, 240)
                    canvas.drawCircle(
                        drawX + flowerSize * 0.5f,
                        drawY + flowerSize * 0.5f,
                        flowerSize * 0.5f + 4f,
                        paint
                    )
                }

                if (pos in selectedSet) {
                    val pulse = (sin(now * 0.008f) + 1f) * 0.5f
                    paint.style = Paint.Style.FILL
                    paint.color = Color.argb((80 + 70 * pulse).toInt(), 255, 235, 130)
                    canvas.drawCircle(
                        drawX + flowerSize * 0.5f,
                        drawY + flowerSize * 0.5f,
                        flowerSize * 0.54f,
                        paint
                    )
                }

                paint.alpha = 255
                canvas.drawBitmap(flower.surf, drawX, drawY, paint)
                drawSpecialBadge(canvas, flower, drawX, drawY, now)
            }
        }

        drawEffects(canvas)
    }

    private fun drawSpecialBadge(canvas: Canvas, flower: Flower, drawX: Float, drawY: Float, now: Long) {
        if (flower.special == null || flower.special == "bomb" || flower.special == "zap" || flower.special == "line") {
            return
        }
        if (flower.special == "rainbow") {
            val t = now * 0.008f
            val cx = drawX + flowerSize * 0.5f
            val cy = drawY + flowerSize * 0.5f
            val r = (127 + 127 * sin(t)).toInt().coerceIn(0, 255)
            val g = (127 + 127 * sin(t + 2.1f)).toInt().coerceIn(0, 255)
            val b = (127 + 127 * sin(t + 4.2f)).toInt().coerceIn(0, 255)
            paint.style = Paint.Style.FILL
            paint.color = Color.rgb(r, g, b)
            canvas.drawCircle(cx, cy, 7f, paint)
        }
    }

    private fun drawTimeOverShader(canvas: Canvas, now: Long) {
        val elapsed = (now - timeOverStartMs).toFloat()
        val t = elapsed * 0.004f
        val boardW = boardCol * cellSize
        val boardH = boardRow * cellSize
        val cx = boardStartX + boardW * 0.5f
        val cy = boardStartY + boardH * 0.5f

        val iter = timeOverFlowers.iterator()
        while (iter.hasNext()) {
            val tf = iter.next()
            if (tf.delay > 0f) {
                tf.delay -= 1f
                val jitterX = tf.x + sin(elapsed * 0.05f + tf.y) * 2.5f
                canvas.drawBitmap(tf.surf, jitterX, tf.y, paint)
            } else {
                if (!tf.launched) {
                    tf.launched = true
                    if (Random.nextFloat() < 0.35f) {
                        spawnBurst(tf.x, tf.y, tf.colorName)
                    }
                }
                tf.x += tf.vx
                tf.y += tf.vy
                tf.vy += 0.58f
                tf.angle = (tf.angle + tf.angVel) % 360f
                if (tf.y < 790f) {
                    canvas.save()
                    canvas.rotate(tf.angle, tf.x + flowerSize * 0.5f, tf.y + flowerSize * 0.5f)
                    canvas.drawBitmap(tf.surf, tf.x, tf.y, paint)
                    canvas.restore()
                } else {
                    iter.remove()
                }
            }
        }

        val washAlpha = min(135, (elapsed * 0.08f).toInt())
        paint.style = Paint.Style.FILL
        paint.color = Color.argb(washAlpha, 28, 10, 52)
        rectF.set(boardStartX - 12f, boardStartY - 12f, boardStartX + boardW + 12f, boardStartY + boardH + 12f)
        canvas.drawRoundRect(rectF, 16f, 16f, paint)

        paint.style = Paint.Style.STROKE
        paint.strokeWidth = 4f
        for (ringIdx in 0 until 3) {
            val ringProg = (elapsed - ringIdx * 260f) * 0.42f
            if (ringProg in 1f..520f) {
                val ringAlpha = (190f * (1f - ringProg / 520f)).toInt().coerceIn(0, 255)
                paint.color = if (ringIdx % 2 == 0) {
                    Color.argb(ringAlpha, 255, 120, 210)
                } else {
                    Color.argb(ringAlpha, 120, 230, 255)
                }
                canvas.drawCircle(cx, cy, ringProg, paint)
            }
        }

        val bannerW = 520f
        val bannerH = 155f
        val bx = cx - bannerW * 0.5f
        val by = cy - bannerH * 0.5f + sin(t * 2f) * 6f
        shader.drawGlowPanel(canvas, now, bx, by, bannerW, bannerH, hovered = true)

        val pulse = (sin(t * 3f) + 1f) * 0.5f
        val mainCol = Color.rgb(255, (215 + 35 * pulse).toInt(), (140 + 60 * pulse).toInt())
        val glowCol = Color.rgb(210, 35, 115)
        shader.drawGlowText(
            canvas, typeface, 84f, "TIME OVER!", bx, by + 26f,
            mainColor = mainCol, glowColor = glowCol, offset = 4f,
            maxWidth = bannerW - 40f, centerWidth = bannerW
        )
    }

    private fun drawHowToPlayModal(canvas: Canvas, now: Long) {
        paint.style = Paint.Style.FILL
        paint.color = Color.argb(185, 12, 6, 30)
        canvas.drawRect(0f, 0f, virtualW, virtualH, paint)

        val mx = 180f
        val my = 55f
        val mw = 920f
        val mh = 610f
        shader.drawGlowPanel(canvas, now, mx, my, mw, mh)
        shader.drawGlowText(
            canvas, typeface, 56f, "How to Play Flowers", mx, my + 22f,
            mainColor = Color.rgb(255, 240, 160), offset = 3f,
            maxWidth = mw - 48f, centerWidth = mw
        )

        val lines = arrayOf(
            Triple("Goal:", "Match 3 or more flowers of the same color in a row or column!", Color.rgb(180, 245, 255)),
            Triple("8-Way Swap:", "Tap 2 neighbors OR drag horizontally, vertically, or diagonally.", Color.rgb(245, 235, 255)),
            Triple("Match 4 (Zap):", "Spawns a zap flower that clears its full row & column!", Color.rgb(255, 235, 140)),
            Triple("Match 5 (Rainbow):", "Spawns a rainbow-ring flower that clears all flowers of its color (+3s)!", Color.rgb(255, 195, 245)),
            Triple("Match 6+ (Bomb):", "Spawns a bomb flower that blasts a 5x5 area around it (+3s)!", Color.rgb(160, 255, 210)),
            Triple("Combos & Levels:", "Chain cascades boost your multiplier (2x, 3x...). Level up for +15s!", Color.rgb(245, 235, 255)),
            Triple("Hints & Shuffle:", "Wait 6s for an auto-hint wiggle, or tap Shuffle when stuck.", Color.rgb(220, 215, 255))
        )

        var yCursor = my + 110f
        for ((heading, desc, col) in lines) {
            shader.drawGlowText(
                canvas, typeface, 30f, heading, mx + 38f, yCursor,
                mainColor = col, offset = 2f, maxWidth = 275f
            )
            shader.drawGlowText(
                canvas, typeface, 21f, desc, mx + 320f, yCursor + 6f,
                mainColor = Color.rgb(245, 240, 255), offset = 1f, maxWidth = mw - 350f
            )
            yCursor += 58f
        }

        shader.drawGlowPanel(
            canvas, now, howToPlayCloseRect.left, howToPlayCloseRect.top,
            howToPlayCloseRect.width(), howToPlayCloseRect.height(),
            hovered = true
        )
        shader.drawGlowText(
            canvas, typeface, 30f, "Got It - Let's Play! (Tap)",
            howToPlayCloseRect.left, howToPlayCloseRect.top + 13f,
            mainColor = Color.rgb(255, 245, 190), offset = 2f,
            maxWidth = howToPlayCloseRect.width() - 28f, centerWidth = howToPlayCloseRect.width()
        )
    }

    private fun drawEndScreen(canvas: Canvas) {
        val now = ticksMs()
        val t = now * 0.003f
        shader.drawParallaxBackground(canvas, now, lastTouchX, lastTouchY, getMenuClouds(), muted = false)
        shader.drawAtmosphere(canvas, now)

        val msg1Str = "Your Score: $finalScore"
        val msg2Str = "Tap anywhere to play again"
        textMeasurePaint.textSize = 72f
        val pw = max(460f, textMeasurePaint.measureText(msg1Str) + 64f)
        val px = (virtualW - pw) * 0.5f
        val ty = 50f + sin(t * 1.6f) * 6f
        shader.drawGlowPanel(canvas, now, px, ty - 16f, pw, 108f)
        shader.drawGlowText(
            canvas, typeface, 72f, msg1Str, px, ty,
            offset = 3f, maxWidth = pw - 32f, centerWidth = pw
        )

        val hsW = 460f
        val hsH = 290f
        val hsX = (virtualW - hsW) * 0.5f
        val hsY = 225f
        shader.drawGlowPanel(canvas, now, hsX, hsY, hsW, hsH)
        shader.drawGlowText(
            canvas, typeface, 34f, "Top High Scores", hsX, hsY + 18f,
            mainColor = Color.rgb(255, 235, 150), offset = 2f, centerWidth = hsW
        )
        for ((idx, hs) in highScores.take(5).withIndex()) {
            val col = if (hs == finalScore && finalScore > 0) {
                Color.rgb(255, 240, 140)
            } else {
                Color.rgb(240, 230, 255)
            }
            shader.drawGlowText(
                canvas, typeface, 26f, "#${idx + 1}    $hs pts",
                hsX, hsY + 80f + idx * 40f,
                mainColor = col, offset = 2f, centerWidth = hsW
            )
        }

        val bw = 540f
        val bh = 68f
        val bx = (virtualW - bw) * 0.5f
        val by = 590f
        shader.drawGlowPanel(canvas, now, bx, by, bw, bh, hovered = true)
        shader.drawGlowText(
            canvas, typeface, 34f, msg2Str, bx, by + 14f,
            offset = 2f, maxWidth = bw - 32f, centerWidth = bw
        )
    }

    fun onResume() {
        isPaused = false
        lastSecondTickMs = ticksMs()
        postInvalidateOnAnimation()
    }

    fun onPause() {
        isPaused = true
        saveCurrentScore()
    }

    fun onDestroy() {
        saveCurrentScore()
    }
}
