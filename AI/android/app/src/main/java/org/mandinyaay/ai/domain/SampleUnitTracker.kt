package org.mandinyaay.ai.domain

import android.graphics.RectF
import org.mandinyaay.ai.ml.ProduceCondition
import org.mandinyaay.ai.ml.ProduceDetection
import java.util.UUID
import kotlin.math.PI
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow

enum class CaptureRole {
    PRIMARY_SAMPLE_CAPTURE,
    DETAIL_RECAPTURE
}

data class SampleObservationView(
    val observationId: String,
    val captureRole: CaptureRole,
    val viewPerspective: String, // "TOP", "SIDE", "DETAIL"
    val bbox: RectF,
    val condition: ProduceCondition,
    val confidence: Float
)

data class PhysicalSampleUnit(
    val sampleUnitId: String,
    val lotId: String,
    var resolvedCondition: ProduceCondition,
    val observations: MutableList<SampleObservationView> = mutableListOf(),
    var lengthMm: Float? = null,
    var widthMm: Float? = null,
    var thicknessMm: Float? = null,
    var geometricDiameterMm: Float? = null,
    var aspectRatio: Float? = null,
    var sphericity: Float? = null,
    var ellipsoidVolumeCm3: Float? = null,
    var weightEstimateG: Float? = null,
    var weightIntervalLowG: Float? = null,
    var weightIntervalHighG: Float? = null,
    var sizeStatus: String = "ONION_DIAMETER_UNVALIDATED",
    var weightStatus: String = "UNVALIDATED",
    var reviewRequired: Boolean = false,
    var title: String = "Healthy",
    var explanation: String = "No modeled visible defect detected."
) {
    fun addObservation(view: SampleObservationView) {
        observations.add(view)

        // Check for cross-view discrepancy
        val nonConflictConditions = observations
            .map { it.condition }
            .filter { it != ProduceCondition.CLASS_CONFLICT && it != ProduceCondition.UNKNOWN }
            .toSet()

        if (nonConflictConditions.size > 1) {
            resolvedCondition = ProduceCondition.CLASS_CONFLICT
            reviewRequired = true
            title = "Review required"
            explanation = "Multiple views of this onion disagree on the visible defect state. Flagged for inspector arbitration."
        } else if (nonConflictConditions.size == 1) {
            resolvedCondition = nonConflictConditions.first()
            title = resolvedCondition.displayName
            reviewRequired = false
            explanation = "Condition confirmed across views."
        }
    }

    fun updateCalibratedGeometry(
        topLengthPx: Float,
        topWidthPx: Float,
        sideThicknessPx: Float?,
        mmPerPixel: Float?
    ) {
        if (mmPerPixel == null || mmPerPixel <= 0f) {
            sizeStatus = "ONION_DIAMETER_UNVALIDATED"
            return
        }

        val l = max(topLengthPx, topWidthPx) * mmPerPixel
        val w = min(topLengthPx, topWidthPx) * mmPerPixel
        val t = (sideThicknessPx ?: (topWidthPx * 0.92f)) * mmPerPixel

        lengthMm = l
        widthMm = w
        thicknessMm = t

        val dg = (l * w * t).pow(1f / 3f)
        geometricDiameterMm = dg
        aspectRatio = l / max(0.1f, w)
        val maxDim = max(l, max(w, t))
        sphericity = min(1f, dg / max(0.1f, maxDim))

        // Ellipsoid Volume V = (PI / 6) * L * W * T mm^3 -> cm^3 (/ 1000)
        val volMm3 = (PI.toFloat() / 6f) * l * w * t
        ellipsoidVolumeCm3 = volMm3 / 1000f

        sizeStatus = "MEASUREMENT_AVAILABLE"
    }

    fun updateWeightEstimate(
        artifactLoaded: Boolean,
        calibratedDensity: Float = 1.01f,
        conformalQ: Float = 0.02f
    ) {
        val vol = ellipsoidVolumeCm3
        if (!artifactLoaded || vol == null || vol <= 0f) {
            weightStatus = "UNVALIDATED"
            weightEstimateG = null
            weightIntervalLowG = null
            weightIntervalHighG = null
            return
        }

        val estG = vol * calibratedDensity
        val marginG = estG * conformalQ * 1.5f
        weightEstimateG = estG
        weightIntervalLowG = max(1f, estG - marginG)
        weightIntervalHighG = estG + marginG
        weightStatus = "ESTIMATE_AVAILABLE"
    }
}

class SampleUnitTracker(val lotId: String) {

    private val units = mutableMapOf<String, PhysicalSampleUnit>()

    fun registerPrimaryDetection(detection: ProduceDetection, mmPerPixel: Float? = null): PhysicalSampleUnit {
        val unitId = "su_${UUID.randomUUID().toString().substring(0, 8)}"
        val unit = PhysicalSampleUnit(
            sampleUnitId = unitId,
            lotId = lotId,
            resolvedCondition = detection.condition,
            reviewRequired = detection.condition == ProduceCondition.CLASS_CONFLICT,
            title = detection.condition.displayName,
            explanation = if (detection.condition == ProduceCondition.CLASS_CONFLICT)
                "Review required: conflicting defect condition detected."
            else "Single-view observation established."
        )

        val view = SampleObservationView(
            observationId = detection.id,
            captureRole = CaptureRole.PRIMARY_SAMPLE_CAPTURE,
            viewPerspective = "TOP",
            bbox = detection.bbox,
            condition = detection.condition,
            confidence = detection.confidence
        )
        unit.addObservation(view)
        unit.updateCalibratedGeometry(detection.bbox.width(), detection.bbox.height(), null, mmPerPixel)

        units[unitId] = unit
        return unit
    }

    fun associateDetailView(targetUnitId: String, detection: ProduceDetection, viewPerspective: String = "SIDE", mmPerPixel: Float? = null): Boolean {
        val unit = units[targetUnitId] ?: return false
        val view = SampleObservationView(
            observationId = detection.id,
            captureRole = CaptureRole.DETAIL_RECAPTURE,
            viewPerspective = viewPerspective,
            bbox = detection.bbox,
            condition = detection.condition,
            confidence = detection.confidence
        )
        unit.addObservation(view)
        if (viewPerspective == "SIDE") {
            unit.updateCalibratedGeometry(
                detection.bbox.width(),
                detection.bbox.height(),
                detection.bbox.height(),
                mmPerPixel
            )
        }
        return true
    }

    fun getAllUnits(): List<PhysicalSampleUnit> = units.values.toList()

    fun getPhysicalSampleCount(): Int = units.size

    fun getConditionCounts(): Map<ProduceCondition, Int> {
        val map = mutableMapOf<ProduceCondition, Int>()
        for (u in units.values) {
            val cond = u.resolvedCondition
            map[cond] = (map[cond] ?: 0) + 1
        }
        return map
    }

    fun getConflictCount(): Int = units.values.count { it.resolvedCondition == ProduceCondition.CLASS_CONFLICT }
}
