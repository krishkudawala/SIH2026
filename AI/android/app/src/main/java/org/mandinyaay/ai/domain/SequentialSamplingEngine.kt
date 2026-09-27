package org.mandinyaay.ai.domain

import org.mandinyaay.ai.ml.ProduceCondition
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

data class DefectWilsonInterval(
    val defectCondition: ProduceCondition,
    val count: Int,
    val totalN: Int,
    val proportion: Float,
    val lowerBound: Float,
    val upperBound: Float,
    val displayString: String
)

enum class SamplingState {
    CONTINUE,
    SUFFICIENT,
    REJECT_BOUNDARY,
    ACCEPT_BOUNDARY,
    MANUAL_REVIEW
}

data class SamplingProgressReport(
    val state: SamplingState,
    val currentSampleSize: Int,
    val targetSampleSize: Int,
    val intervals: List<DefectWilsonInterval>,
    val reason: String,
    val recommendedGrade: String
)

object SequentialSamplingEngine {

    fun computeWilsonInterval(
        count: Int,
        sampleN: Int,
        z: Float = 1.96f, // 95% confidence level
        lotPopulationN: Int? = null
    ): Pair<Float, Float> {
        if (sampleN <= 0) return Pair(0f, 1f)

        val p = count.toFloat() / sampleN.toFloat()
        val denom = 1f + (z * z) / sampleN
        val center = (p + (z * z) / (2f * sampleN)) / denom
        var margin = (z / denom) * sqrt((p * (1f - p) / sampleN) + ((z * z) / (4f * sampleN * sampleN)))

        // Finite Population Correction
        if (lotPopulationN != null && lotPopulationN > sampleN) {
            val fpc = sqrt((lotPopulationN - sampleN).toFloat() / max(1f, (lotPopulationN - 1).toFloat()))
            margin *= fpc
        }

        val low = max(0f, center - margin)
        val high = min(1f, center + margin)
        return Pair(low, high)
    }

    fun evaluateSampling(
        tracker: SampleUnitTracker,
        minTarget: Int = 20,
        maxRottenPctLimit: Float = 5.0f,
        maxDamagedPctLimit: Float = 10.0f,
        lotPopulationN: Int? = 1000,
        allowEarlyStopping: Boolean = true
    ): SamplingProgressReport {
        val n = tracker.getPhysicalSampleCount()
        val counts = tracker.getConditionCounts()
        val conflictCount = tracker.getConflictCount()

        // Build intervals for all defects
        val intervals = mutableListOf<DefectWilsonInterval>()
        for (cond in listOf(ProduceCondition.ROTTEN, ProduceCondition.DAMAGED, ProduceCondition.SPROUTED)) {
            val c = counts[cond] ?: 0
            val (low, high) = computeWilsonInterval(c, n, lotPopulationN = lotPopulationN)
            val pct = (c.toFloat() / max(1, n)) * 100f
            val lowPct = low * 100f
            val highPct = high * 100f

            intervals.add(
                DefectWilsonInterval(
                    defectCondition = cond,
                    count = c,
                    totalN = n,
                    proportion = c.toFloat() / max(1, n),
                    lowerBound = low,
                    upperBound = high,
                    displayString = "$c / $n (${"%.1f".format(pct)}%), 95% Wilson CI: [${"%.1f".format(lowPct)}%, ${"%.1f".format(highPct)}%]"
                )
            )
        }

        // 1. Conflict Check -> MANUAL_REVIEW
        if (conflictCount > 0) {
            return SamplingProgressReport(
                state = SamplingState.MANUAL_REVIEW,
                currentSampleSize = n,
                targetSampleSize = minTarget,
                intervals = intervals,
                reason = "Session contains $conflictCount cross-view conflict(s). Human inspector review required.",
                recommendedGrade = "MANUAL_REVIEW"
            )
        }

        // 2. Statistical Boundaries Check (if early stopping permitted)
        if (allowEarlyStopping && n >= 10) {
            val rotInterval = intervals.find { it.defectCondition == ProduceCondition.ROTTEN }
            if (rotInterval != null && (rotInterval.lowerBound * 100f) > maxRottenPctLimit) {
                return SamplingProgressReport(
                    state = SamplingState.REJECT_BOUNDARY,
                    currentSampleSize = n,
                    targetSampleSize = minTarget,
                    intervals = intervals,
                    reason = "Early reject boundary reached: Wilson 95% lower bound (${"%.1f".format(rotInterval.lowerBound * 100f)}%) exceeds allowable rotten limit ($maxRottenPctLimit%).",
                    recommendedGrade = "REJECT"
                )
            }
        }

        // 3. Sample Sufficiency Check
        if (n >= minTarget) {
            val rotCount = counts[ProduceCondition.ROTTEN] ?: 0
            val rotPct = (rotCount.toFloat() / n) * 100f

            val grade = if (rotPct > maxRottenPctLimit) "REJECT" else "GRADE_A"
            return SamplingProgressReport(
                state = SamplingState.SUFFICIENT,
                currentSampleSize = n,
                targetSampleSize = minTarget,
                intervals = intervals,
                reason = "Target sample size ($n >= $minTarget) satisfied under APMC RulePack with zero conflicts.",
                recommendedGrade = grade
            )
        } else {
            val shortfall = minTarget - n
            return SamplingProgressReport(
                state = SamplingState.CONTINUE,
                currentSampleSize = n,
                targetSampleSize = minTarget,
                intervals = intervals,
                reason = "Sampling in progress: $n / $minTarget SampleUnits recorded. Capture $shortfall more bulb(s).",
                recommendedGrade = "IN_PROGRESS"
            )
        }
    }
}
