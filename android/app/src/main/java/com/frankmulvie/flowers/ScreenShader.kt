package com.frankmulvie.flowers

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.ColorMatrix
import android.graphics.ColorMatrixColorFilter
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.graphics.Typeface
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.sin
import kotlin.random.Random

class ScreenShader(context: Context, val width: Int = 1280, val height: Int = 720) {
    data class PollenParticle(
        var x: Float,
        var y: Float,
        val speed: Float,
        val radius: Float,
        val phase: Float,
        val r: Int,
        val g: Int,
        val b: Int
    )

    private val paint = Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG)
    private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val glowPaint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val rectF = RectF()
    private val beamPath = Path()

    val particles = Array(45) {
        val palette = arrayOf(
            Triple(255, 220, 130),
            Triple(255, 160, 220),
            Triple(160, 220, 255),
            Triple(190, 255, 180)
        )
        val col = palette[Random.nextInt(palette.size)]
        PollenParticle(
            x = Random.nextFloat() * width,
            y = Random.nextFloat() * height,
            speed = Random.nextFloat() * 1.2f + 0.6f,
            radius = Random.nextFloat() * 4.0f + 3.0f,
            phase = Random.nextFloat() * (PI.toFloat() * 2f),
            r = col.first,
            g = col.second,
            b = col.third
        )
    }

    init {
        ensureParallaxLayers(context)
    }

    fun drawParallaxBackground(
        canvas: Canvas,
        ticksMs: Long,
        touchX: Float,
        touchY: Float,
        clouds: List<Pair<Bitmap, Pair<Float, Float>>>? = null,
        muted: Boolean = true
    ) {
        val layerList = if (muted) parallaxMutedCache else parallaxVibrantCache
        if (layerList.isEmpty()) return

        val t = ticksMs * 0.0012f
        val normX = (touchX - width * 0.5f) / (width * 0.5f)
        val normY = (touchY - height * 0.5f) / (height * 0.5f)
        val driftX = sin(t) * 18.0f
        val driftY = cos(t * 0.8f) * 8.0f

        val activeClouds = clouds ?: if (cloudCache.isNotEmpty()) {
            val sec = ticksMs * 0.06f
            val specs = arrayOf(
                floatArrayOf(40f, 22f, 0.42f, 420f, 0.0f),
                floatArrayOf(460f, 135f, 0.19f, 260f, 2.1f),
                floatArrayOf(940f, 72f, 0.30f, 320f, 4.2f)
            )
            cloudCache.mapIndexed { idx, bmp ->
                val s = specs[minOf(idx, specs.lastIndex)]
                val span = 1380f + s[3]
                val breeze = sin(t * 0.55f + s[4]) * 18.0f
                val cx = (((s[0] + sec * s[2] + breeze + s[3]) % span + span) % span) - s[3]
                val cy = s[1] + sin(t * 0.85f + s[4]) * 5.0f
                bmp to (cx to cy)
            }
        } else emptyList()

        val cloudParallax = arrayOf(0.38f to 0.28f, 0.24f to 0.18f, 0.31f to 0.23f)
        val parallaxFactors = arrayOf(0.2f to 0.15f, 0.55f to 0.4f, 1.0f to 0.75f)

        paint.alpha = 255
        for ((idx, layerBmp) in layerList.withIndex()) {
            val (fx, fy) = parallaxFactors[minOf(idx, parallaxFactors.lastIndex)]
            val ox = -40f - (normX * 22.0f + driftX) * fx
            val oy = -22f - (normY * 14.0f + driftY) * fy
            canvas.drawBitmap(layerBmp, ox, oy, paint)
            if (idx == 0 && activeClouds.isNotEmpty()) {
                paint.alpha = 230
                for ((cIdx, pair) in activeClouds.withIndex()) {
                    val (cfx, cfy) = cloudParallax[minOf(cIdx, cloudParallax.lastIndex)]
                    val cox = pair.second.first - (normX * 22.0f + driftX) * cfx
                    val coy = pair.second.second - (normY * 14.0f + driftY) * cfy
                    canvas.drawBitmap(pair.first, cox, coy, paint)
                }
                paint.alpha = 255
            }
        }

        if (muted) {
            paint.style = Paint.Style.FILL
            paint.color = Color.argb(46, 24, 28, 42)
            canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), paint)
        }
    }

    fun drawAtmosphere(canvas: Canvas, ticksMs: Long) {
        val t = ticksMs * 0.003f
        paint.style = Paint.Style.FILL

        for (i in 0 until 5) {
            val beamX = 200f + i * 240f + sin(t + i) * 60f
            val beamAlpha = (18f + 12f * sin(t * 1.3f + i)).toInt().coerceIn(4, 40)
            paint.color = Color.argb(beamAlpha, 255, 245, 200)
            beamPath.reset()
            beamPath.moveTo(beamX - 60f, 0f)
            beamPath.lineTo(beamX + 60f, 0f)
            beamPath.lineTo(beamX + 220f, height.toFloat())
            beamPath.lineTo(beamX - 20f, height.toFloat())
            beamPath.close()
            canvas.drawPath(beamPath, paint)
        }

        for (p in particles) {
            p.y -= p.speed
            p.x += sin(t * 1.2f + p.phase) * 0.8f
            if (p.y < -20f) {
                p.y = height + 20f
                p.x = Random.nextFloat() * width
            }
            val glowAlpha = (90f + 80f * sin(t * 2.0f + p.phase)).toInt().coerceIn(10, 255)
            paint.color = Color.argb(glowAlpha / 3, p.r, p.g, p.b)
            canvas.drawCircle(p.x, p.y, p.radius * 2.4f, paint)
            paint.color = Color.argb(glowAlpha, p.r, p.g, p.b)
            canvas.drawCircle(p.x, p.y, p.radius, paint)
            paint.color = Color.argb(210, 255, 255, 255)
            canvas.drawCircle(p.x, p.y, max(1f, p.radius * 0.45f), paint)
        }
    }

    fun drawGlowText(
        canvas: Canvas,
        typeface: Typeface,
        textSize: Float,
        text: String,
        x: Float,
        y: Float,
        mainColor: Int = Color.rgb(245, 235, 255),
        glowColor: Int = Color.rgb(95, 45, 190),
        offset: Float = 2f,
        maxWidth: Float? = null,
        centerWidth: Float? = null
    ) {
        textPaint.typeface = typeface
        textPaint.textSize = textSize
        var rawW = textPaint.measureText(text)
        var effectiveSize = textSize
        if (maxWidth != null && rawW > maxWidth && rawW > 0f) {
            effectiveSize = textSize * (maxWidth / rawW)
            textPaint.textSize = effectiveSize
            rawW = textPaint.measureText(text)
        }
        glowPaint.typeface = typeface
        glowPaint.textSize = effectiveSize
        glowPaint.color = glowColor
        textPaint.color = mainColor

        val drawX = if (centerWidth != null) x + (centerWidth - rawW) * 0.5f else x
        val fm = textPaint.fontMetrics
        val baselineY = y - fm.ascent

        val offsets = arrayOf(
            -offset to 0f,
            offset to 0f,
            0f to -offset,
            0f to offset,
            (-offset + 1f) to (-offset + 1f),
            (offset - 1f) to (-offset + 1f),
            (-offset + 1f) to (offset - 1f),
            (offset - 1f) to (offset - 1f)
        )
        for ((ox, oy) in offsets) {
            canvas.drawText(text, drawX + ox, baselineY + oy, glowPaint)
        }
        canvas.drawText(text, drawX, baselineY, textPaint)
    }

    fun drawGlowPanel(
        canvas: Canvas,
        ticksMs: Long,
        x: Float,
        y: Float,
        w: Float,
        h: Float,
        hovered: Boolean = false
    ) {
        val t = ticksMs * 0.003f
        val pulse = (sin(t * 1.5f) + 1.0f) * 0.5f
        val bgAlpha = if (hovered) 200 else 160

        paint.style = Paint.Style.FILL
        paint.color = Color.argb(bgAlpha, 35, 20, 80)
        rectF.set(x, y, x + w, y + h)
        canvas.drawRoundRect(rectF, 20f, 20f, paint)

        paint.style = Paint.Style.STROKE
        paint.strokeWidth = 3f
        for (layer in 4 downTo 1) {
            val spread = layer * 3f
            val a = ((if (hovered) 45 else 25) * (5 - layer)) / 4
            paint.color = Color.argb(a, 190, 130, 255)
            rectF.set(x - spread, y - spread, x + w + spread, y + h + spread)
            canvas.drawRoundRect(rectF, 20f + spread, 20f + spread, paint)
        }

        paint.color = if (hovered) {
            Color.argb(255, 255, 230, 150)
        } else {
            Color.argb((190 + 60 * pulse).toInt().coerceIn(0, 255), 200, 165, 255)
        }
        rectF.set(x, y, x + w, y + h)
        canvas.drawRoundRect(rectF, 20f, 20f, paint)
    }

    companion object {
        var parallaxMutedCache: List<Bitmap> = emptyList()
            private set
        var parallaxVibrantCache: List<Bitmap> = emptyList()
            private set
        var cloudCache: List<Bitmap> = emptyList()
            private set

        fun scaleCloud(bmp: Bitmap, factor: Float = 0.6f): Bitmap {
            val w = max(1, (bmp.width * factor).toInt())
            val h = max(1, (bmp.height * factor).toInt())
            return Bitmap.createScaledBitmap(bmp, w, h, true)
        }

        private fun muteBitmap(src: Bitmap): Bitmap {
            val out = Bitmap.createBitmap(src.width, src.height, Bitmap.Config.ARGB_8888)
            val c = Canvas(out)
            val cm = ColorMatrix()
            cm.setSaturation(0.38f)
            val scale = ColorMatrix(
                floatArrayOf(
                    0.76f, 0f, 0f, 0f, 0f,
                    0f, 0.76f, 0f, 0f, 0f,
                    0f, 0f, 0.76f, 0f, 0f,
                    0f, 0f, 0f, 1f, 0f
                )
            )
            cm.postConcat(scale)
            val p = Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG)
            p.colorFilter = ColorMatrixColorFilter(cm)
            c.drawBitmap(src, 0f, 0f, p)
            return out
        }

        private fun keyOutWhite(src: Bitmap): Bitmap {
            val w = src.width
            val h = src.height
            val pixels = IntArray(w * h)
            src.getPixels(pixels, 0, w, 0, 0, w, h)
            for (i in pixels.indices) {
                val px = pixels[i]
                val r = Color.red(px)
                val g = Color.green(px)
                val b = Color.blue(px)
                if (abs(255 - r) <= 22 && abs(255 - g) <= 22 && abs(255 - b) <= 26) {
                    pixels[i] = Color.TRANSPARENT
                }
            }
            return Bitmap.createBitmap(pixels, w, h, Bitmap.Config.ARGB_8888)
        }

        fun ensureParallaxLayers(context: Context) {
            if (parallaxMutedCache.isNotEmpty()) return
            val assets = context.assets
            val vibrant = mutableListOf<Bitmap>()
            val muted = mutableListOf<Bitmap>()
            val specs = listOf(
                "imgs/bg-layer1.jpeg" to false,
                "imgs/bg-layer2.jpeg" to true,
                "imgs/bg-layer3.jpeg" to true
            )
            for ((path, keyWhite) in specs) {
                try {
                    assets.open(path).use { stream ->
                        var raw = BitmapFactory.decodeStream(stream)
                        if (raw != null) {
                            if (keyWhite) {
                                raw = keyOutWhite(raw)
                            }
                            val scaled = Bitmap.createScaledBitmap(raw, 1360, 765, true)
                            vibrant.add(scaled)
                            muted.add(muteBitmap(scaled))
                        }
                    }
                } catch (_: Exception) {
                }
            }
            parallaxVibrantCache = vibrant
            parallaxMutedCache = muted

            val clouds = mutableListOf<Bitmap>()
            for (cpath in listOf("imgs/N-Cloud-1.png", "imgs/N-Cloud-2.png", "imgs/N-Cloud-3.png")) {
                try {
                    assets.open(cpath).use { stream ->
                        val raw = BitmapFactory.decodeStream(stream)
                        if (raw != null) {
                            clouds.add(muteBitmap(scaleCloud(raw, 0.6f)))
                        }
                    }
                } catch (_: Exception) {
                }
            }
            cloudCache = clouds
        }
    }
}
