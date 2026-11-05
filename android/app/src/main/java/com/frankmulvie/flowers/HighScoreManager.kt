package com.frankmulvie.flowers

import android.content.Context
import org.json.JSONArray

object HighScoreManager {
    private const val PREFS_NAME = "flowers_highscores"
    private const val KEY_SCORES = "top_scores"

    fun loadScores(context: Context): List<Int> {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val raw = prefs.getString(KEY_SCORES, null) ?: return emptyList()
        return try {
            val arr = JSONArray(raw)
            val list = mutableListOf<Int>()
            for (i in 0 until minOf(5, arr.length())) {
                val v = arr.optInt(i, 0)
                if (v > 0) list.add(v)
            }
            list.sortedDescending().take(5)
        } catch (_: Exception) {
            emptyList()
        }
    }

    fun saveScoresList(context: Context, scores: List<Int>): List<Int> {
        val sorted = scores.filter { it > 0 }.sortedDescending().take(5)
        val arr = JSONArray()
        sorted.forEach { arr.put(it) }
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_SCORES, arr.toString())
            .apply()
        return sorted
    }

    fun addScore(context: Context, score: Int): List<Int> {
        val current = loadScores(context).toMutableList()
        if (score > 0) {
            current.add(score)
        }
        return saveScoresList(context, current)
    }
}
