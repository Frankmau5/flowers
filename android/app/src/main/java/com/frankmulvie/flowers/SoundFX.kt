package com.frankmulvie.flowers

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import java.util.Random
import kotlin.math.PI
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow
import kotlin.math.sin

class SoundFX {
    private val sampleRate = 44100
    private val sounds = mutableMapOf<String, ShortArray>()

    init {
        sounds["select"] = makeTone(doubleArrayOf(660.0), 0.065, 0.65)
        sounds["swap"] = makeTone(doubleArrayOf(440.0, 554.0), 0.06, 0.65)
        sounds["shuffle"] = makeTone(doubleArrayOf(330.0, 440.0, 554.0, 660.0), 0.055, 0.65)
        sounds["tick"] = makeTone(doubleArrayOf(880.0), 0.055, 0.55)
        sounds["levelup"] = makeTone(doubleArrayOf(523.0, 659.0, 784.0, 1046.0), 0.09, 0.75)
        sounds["gameover"] = makeTone(doubleArrayOf(659.0, 587.0, 523.0, 392.0), 0.12, 0.75)
        sounds["zap"] = makeTone(doubleArrayOf(1320.0, 988.0, 1568.0, 784.0, 1760.0), 0.05, 0.75)
        sounds["rainbow"] = makeTone(
            doubleArrayOf(523.0, 659.0, 784.0, 988.0, 1175.0, 1318.0, 1568.0),
            0.05,
            0.75
        )
        sounds["bomb"] = makeBombSound(0.35, 0.85)
        for (combo in 1..7) {
            val base = 440.0 * 1.12.pow((combo - 1).toDouble())
            sounds["match_$combo"] = makeTone(
                doubleArrayOf(base, base * 1.25, base * 1.5),
                0.07,
                0.72
            )
        }
    }

    private fun makeTone(freqs: DoubleArray, durationPerNote: Double, volume: Double): ShortArray {
        val nSamplesPerNote = (sampleRate * durationPerNote).toInt()
        val buf = ShortArray(nSamplesPerNote * freqs.size)
        var idx = 0
        for (freq in freqs) {
            for (i in 0 until nSamplesPerNote) {
                val t = i.toDouble() / sampleRate
                val env = (1.0 - i.toDouble() / max(1, nSamplesPerNote)).pow(0.8)
                val wave = 0.75 * sin(2.0 * PI * freq * t) + 0.25 * sin(4.0 * PI * freq * t)
                val sample = (32767.0 * volume * env * wave).toInt().coerceIn(-32767, 32767)
                buf[idx++] = sample.toShort()
            }
        }
        return buf
    }

    private fun makeBombSound(duration: Double, volume: Double): ShortArray {
        val nSamples = (sampleRate * duration).toInt()
        val buf = ShortArray(nSamples)
        val rng = Random(42L)
        for (i in 0 until nSamples) {
            val t = i.toDouble() / sampleRate
            val prog = 1.0 - i.toDouble() / max(1, nSamples)
            val env = prog.pow(1.4)
            val freq = 150.0 * prog.pow(0.7) + 38.0
            val boom = sin(2.0 * PI * freq * t)
            val noise = (rng.nextDouble() * 1.3 - 0.65) * prog.pow(2.0)
            val sample = (32767.0 * volume * env * (0.72 * boom + 0.28 * noise))
                .toInt()
                .coerceIn(-32767, 32767)
            buf[i] = sample.toShort()
        }
        return buf
    }

    fun play(name: String) {
        val pcm = sounds[name] ?: return
        Thread {
            try {
                val track = AudioTrack.Builder()
                    .setAudioAttributes(
                        AudioAttributes.Builder()
                            .setUsage(AudioAttributes.USAGE_GAME)
                            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                            .build()
                    )
                    .setAudioFormat(
                        AudioFormat.Builder()
                            .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                            .setSampleRate(sampleRate)
                            .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                            .build()
                    )
                    .setBufferSizeInBytes(pcm.size * 2)
                    .setTransferMode(AudioTrack.MODE_STATIC)
                    .build()
                track.write(pcm, 0, pcm.size)
                track.play()
                Thread.sleep((pcm.size * 1000L / sampleRate) + 40L)
                track.release()
            } catch (_: Exception) {
            }
        }.start()
    }

    fun playMatch(combo: Int) {
        val idx = min(7, max(1, combo))
        play("match_$idx")
    }
}
