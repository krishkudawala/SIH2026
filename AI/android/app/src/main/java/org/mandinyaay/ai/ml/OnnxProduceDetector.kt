package org.mandinyaay.ai.ml

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.content.Context
import android.graphics.Bitmap
import android.graphics.RectF
import java.io.InputStream
import java.nio.FloatBuffer
import kotlin.math.max
import kotlin.math.min

enum class ProduceCondition(val displayName: String, val colorHex: Long) {
    HEALTHY("Healthy", 0xFF2E7D32),
    DAMAGED("Damaged", 0xFFE65100),
    SPROUTED("Sprouted", 0xFF6A1B9A),
    ROTTEN("Rotten", 0xFFC62828),
    CLASS_CONFLICT("Review Required", 0xFFD84315),
    UNKNOWN("Unknown", 0xFF757575)
}

data class ProduceDetection(
    val id: String,
    val bbox: RectF,
    val condition: ProduceCondition,
    val confidence: Float,
    val classId: Int
)

class OnnxProduceDetector(context: Context, modelAssetPath: String = "onion-grading-v7.onnx") {

    private val env: OrtEnvironment = OrtEnvironment.getEnvironment()
    private val session: OrtSession

    init {
        val modelBytes = context.assets.open(modelAssetPath).use { it.readBytes() }
        val opts = OrtSession.SessionOptions().apply {
            setIntraOpNumThreads(4)
        }
        session = env.createSession(modelBytes, opts)
    }

    fun detect(bitmap: Bitmap, confThreshold: Float = 0.25f, iouThreshold: Float = 0.45f): List<ProduceDetection> {
        val origW = bitmap.width.toFloat()
        val origH = bitmap.height.toFloat()

        // 1. 640x640 letterbox scaling
        val targetSize = 640
        val scale = min(targetSize / origW, targetSize / origH)
        val newW = (origW * scale).toInt()
        val newH = (origH * scale).toInt()
        val padX = (targetSize - newW) / 2f
        val padY = (targetSize - newH) / 2f

        val resized = Bitmap.createScaledBitmap(bitmap, newW, newH, true)

        // 2. Build FloatBuffer in NCHW RGB format normalized to [0, 1]
        val buffer = FloatBuffer.allocate(1 * 3 * targetSize * targetSize)
        val pixels = IntArray(newW * newH)
        resized.getPixels(pixels, 0, newW, 0, 0, newW, newH)

        val channelStride = targetSize * targetSize
        val topPad = padY.toInt()
        val leftPad = padX.toInt()

        // Default fill color 114 / 255.0f
        val fillVal = 114f / 255f
        for (i in 0 until channelStride * 3) {
            buffer.put(fillVal)
        }

        // Fill RGB channels
        for (y in 0 until newH) {
            for (x in 0 until newW) {
                val pixel = pixels[y * newW + x]
                val r = ((pixel shr 16) and 0xFF) / 255f
                val g = ((pixel shr 8) and 0xFF) / 255f
                val b = (pixel and 0xFF) / 255f

                val targetIdx = (topPad + y) * targetSize + (leftPad + x)
                buffer.put(0 * channelStride + targetIdx, r)
                buffer.put(1 * channelStride + targetIdx, g)
                buffer.put(2 * channelStride + targetIdx, b)
            }
        }
        buffer.rewind()

        // 3. Run ONNX Inference
        val inputName = session.inputNames.iterator().next()
        val shape = longArrayOf(1, 3, targetSize.toLong(), targetSize.toLong())
        val inputTensor = OnnxTensor.createTensor(env, buffer, shape)

        val results = session.run(mapOf(inputName to inputTensor))
        val outputTensor = results[0].value as Array<Array<FloatArray>> // [1, 8, 8400]
        val rawPredictions = outputTensor[0] // [8, 8400]

        // 4. Decode predictions
        val numFeatures = rawPredictions.size // 8 (cx, cy, w, h, score_0, score_1, score_2, score_3)
        val numCandidates = rawPredictions[0].size // 8400

        val candidateBoxes = mutableListOf<RectF>()
        val candidateConfidences = mutableListOf<Float>()
        val candidateClasses = mutableListOf<Int>()

        for (i in 0 until numCandidates) {
            val cx = rawPredictions[0][i]
            val cy = rawPredictions[1][i]
            val w = rawPredictions[2][i]
            val h = rawPredictions[3][i]

            // Find argmax among 4 class scores
            var maxScore = -1f
            var bestClass = -1
            for (c in 0 until (numFeatures - 4)) {
                val score = rawPredictions[4 + c][i]
                if (score > maxScore) {
                    maxScore = score
                    bestClass = c
                }
            }

            if (maxScore >= confThreshold) {
                // De-letterbox to original bitmap coordinates
                val x1 = (cx - w / 2f - padX) / scale
                val y1 = (cy - h / 2f - padY) / scale
                val x2 = (cx + w / 2f - padX) / scale
                val y2 = (cy + h / 2f - padY) / scale

                val clamped = RectF(
                    max(0f, min(origW, x1)),
                    max(0f, min(origH, y1)),
                    max(0f, min(origW, x2)),
                    max(0f, min(origH, y2))
                )

                if (clamped.width() > 5f && clamped.height() > 5f) {
                    candidateBoxes.add(clamped)
                    candidateConfidences.add(maxScore)
                    candidateClasses.add(bestClass)
                }
            }
        }

        // 5. Non-Maximum Suppression
        val keepIndices = nms(candidateBoxes, candidateConfidences, iouThreshold)

        return keepIndices.mapIndexed { idx, i ->
            val classId = candidateClasses[i]
            val condition = when (classId) {
                0 -> ProduceCondition.HEALTHY
                1 -> ProduceCondition.DAMAGED
                2 -> ProduceCondition.SPROUTED
                3 -> ProduceCondition.ROTTEN
                else -> ProduceCondition.UNKNOWN
            }

            ProduceDetection(
                id = "det_${System.currentTimeMillis()}_$idx",
                bbox = candidateBoxes[i],
                condition = condition,
                confidence = candidateConfidences[i],
                classId = classId
            )
        }
    }

    private fun nms(boxes: List<RectF>, scores: List<Float>, iouThreshold: Float): List<Int> {
        val sortedIndices = scores.indices.sortedByDescending { scores[it] }.toMutableList()
        val selected = mutableListOf<Int>()

        while (sortedIndices.isNotEmpty()) {
            val current = sortedIndices.removeAt(0)
            selected.add(current)

            val it = sortedIndices.iterator()
            while (it.hasNext()) {
                val candidate = it.next()
                if (computeIoU(boxes[current], boxes[candidate]) > iouThreshold) {
                    it.remove()
                }
            }
        }
        return selected
    }

    private fun computeIoU(a: RectF, b: RectF): Float {
        val interLeft = max(a.left, b.left)
        val interTop = max(a.top, b.top)
        val interRight = min(a.right, b.right)
        val interBottom = min(a.bottom, b.bottom)

        val interArea = max(0f, interRight - interLeft) * max(0f, interBottom - interTop)
        val unionArea = (a.width() * a.height()) + (b.width() * b.height()) - interArea

        return if (unionArea > 0f) interArea / unionArea else 0f
    }

    fun close() {
        session.close()
        env.close()
    }
}
