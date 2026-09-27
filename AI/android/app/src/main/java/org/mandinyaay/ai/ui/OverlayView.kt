package org.mandinyaay.ai.ui

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.View
import org.mandinyaay.ai.domain.PhysicalSampleUnit
import org.mandinyaay.ai.ml.ProduceCondition
import org.mandinyaay.ai.ml.ProduceDetection

class OverlayView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    private var detections: List<ProduceDetection> = emptyList()
    private var sampleUnits: Map<String, PhysicalSampleUnit> = emptyMap()
    private var scaleX: Float = 1f
    private var scaleY: Float = 1f
    var onOnionTappedListener: ((ProduceDetection, PhysicalSampleUnit?) -> Unit)? = null

    private val boxPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = 6f
    }

    private val textBgPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
    }

    private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        textSize = 34f
        isFakeBoldText = true
    }

    fun setDetections(
        newDetections: List<ProduceDetection>,
        newUnits: Map<String, PhysicalSampleUnit>,
        sourceWidth: Int,
        sourceHeight: Int
    ) {
        this.detections = newDetections
        this.sampleUnits = newUnits
        if (sourceWidth > 0 && sourceHeight > 0 && width > 0 && height > 0) {
            this.scaleX = width.toFloat() / sourceWidth.toFloat()
            this.scaleY = height.toFloat() / sourceHeight.toFloat()
        }
        invalidate()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        for (det in detections) {
            val color = det.condition.colorHex.toInt()
            boxPaint.color = color
            textBgPaint.color = color

            // Scale bounding box to display coordinates
            val scaledRect = RectF(
                det.bbox.left * scaleX,
                det.bbox.top * scaleY,
                det.bbox.right * scaleX,
                det.bbox.bottom * scaleY
            )

            // Draw bounding box
            canvas.drawRoundRect(scaledRect, 12f, 12f, boxPaint)

            // Draw badge header: "Healthy 76%" or "Rotten 70%"
            val label = "${det.condition.displayName} ${(det.confidence * 100).toInt()}%"
            val textWidth = textPaint.measureText(label)
            val badgeHeight = 48f
            val badgeRect = RectF(
                scaledRect.left,
                scaledRect.top - badgeHeight,
                scaledRect.left + textWidth + 24f,
                scaledRect.top
            )
            canvas.drawRoundRect(badgeRect, 8f, 8f, textBgPaint)
            canvas.drawText(label, scaledRect.left + 12f, scaledRect.top - 12f, textPaint)
        }
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (event.action == MotionEvent.ACTION_UP) {
            val touchX = event.x
            val touchY = event.y

            // Find closest tapped detection
            for (det in detections) {
                val scaledRect = RectF(
                    det.bbox.left * scaleX,
                    det.bbox.top * scaleY,
                    det.bbox.right * scaleX,
                    det.bbox.bottom * scaleY
                )
                if (scaledRect.contains(touchX, touchY)) {
                    val unit = sampleUnits.values.find { u ->
                        u.observations.any { it.observationId == det.id }
                    }
                    onOnionTappedListener?.invoke(det, unit)
                    return true
                }
            }
        }
        return true
    }
}
