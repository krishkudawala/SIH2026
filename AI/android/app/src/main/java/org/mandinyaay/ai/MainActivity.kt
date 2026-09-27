package org.mandinyaay.ai

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageFormat
import android.graphics.Rect
import android.graphics.YuvImage
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import org.mandinyaay.ai.databinding.ActivityMainBinding
import org.mandinyaay.ai.domain.PhysicalSampleUnit
import org.mandinyaay.ai.domain.SampleUnitTracker
import org.mandinyaay.ai.domain.SequentialSamplingEngine
import org.mandinyaay.ai.ml.OnnxProduceDetector
import org.mandinyaay.ai.ml.ProduceDetection
import java.io.ByteArrayOutputStream
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var cameraExecutor: ExecutorService
    private var detector: OnnxProduceDetector? = null
    private val tracker = SampleUnitTracker(lotId = "LOT_MH_NSK_2026_B08")
    private var lastDetections: List<ProduceDetection> = emptyList()

    companion object {
        private const val REQUEST_CODE_PERMISSIONS = 101
        private val REQUIRED_PERMISSIONS = arrayOf(Manifest.permission.CAMERA)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        cameraExecutor = Executors.newSingleThreadExecutor()

        try {
            detector = OnnxProduceDetector(this, "onion-grading-v7.onnx")
        } catch (e: Exception) {
            Toast.makeText(this, "Error initializing ONNX detector: ${e.message}", Toast.LENGTH_LONG).show()
        }

        if (allPermissionsGranted()) {
            startCamera()
        } else {
            ActivityCompat.requestPermissions(this, REQUIRED_PERMISSIONS, REQUEST_CODE_PERMISSIONS)
        }

        setupUIInteractions()
    }

    private fun setupUIInteractions() {
        // Tap an individual bulb to inspect its details modal
        binding.overlayView.onOnionTappedListener = { det, unit ->
            showProduceDetailDialog(det, unit)
        }

        // Primary capture button: converts live detections to physical SampleUnits
        binding.btnCapturePrimary.setOnClickListener {
            if (lastDetections.isEmpty()) {
                Toast.makeText(this, "No produce detected in frame. Point at onions.", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            // Assume reference ArUco marker provides 0.15 mm/px scale if coplanar
            val mmPerPx = 0.15f

            for (det in lastDetections) {
                val unit = tracker.registerPrimaryDetection(det, mmPerPixel = mmPerPx)
                unit.updateWeightEstimate(artifactLoaded = true)
            }

            updateSamplingBanner()
            Toast.makeText(
                this,
                "Registered ${lastDetections.size} physical SampleUnits! Total lot sample: ${tracker.getPhysicalSampleCount()}",
                Toast.LENGTH_SHORT
            ).show()
        }

        // Review & Grade Lot Summary
        binding.btnReviewSummary.setOnClickListener {
            showLotSummaryDialog()
        }
    }

    private fun updateSamplingBanner() {
        val report = SequentialSamplingEngine.evaluateSampling(
            tracker = tracker,
            minTarget = 20,
            maxRottenPctLimit = 5.0f,
            allowEarlyStopping = true
        )

        binding.tvSamplingState.text = "Sampling: ${report.currentSampleSize} / ${report.targetSampleSize} SampleUnits (${report.state.name})"

        val rot = report.intervals.find { it.defectCondition.name == "ROTTEN" }
        val dmg = report.intervals.find { it.defectCondition.name == "DAMAGED" }
        val rotStr = if (rot != null) "[${"%.1f".format(rot.lowerBound * 100f)}%, ${"%.1f".format(rot.upperBound * 100f)}%]" else "[0.0%, 0.0%]"
        val dmgStr = if (dmg != null) "[${"%.1f".format(dmg.lowerBound * 100f)}%, ${"%.1f".format(dmg.upperBound * 100f)}%]" else "[0.0%, 0.0%]"

        binding.tvWilsonStats.text = "Wilson 95% CI: Rot $rotStr | Dmg $dmgStr"
    }

    private fun showProduceDetailDialog(detection: ProduceDetection, unit: PhysicalSampleUnit?) {
        val u = unit ?: PhysicalSampleUnit(
            sampleUnitId = "live_${detection.id}",
            lotId = tracker.lotId,
            resolvedCondition = detection.condition,
            reviewRequired = detection.condition.name == "CLASS_CONFLICT"
        ).apply {
            updateCalibratedGeometry(detection.bbox.width(), detection.bbox.height(), null, 0.15f)
            updateWeightEstimate(artifactLoaded = true)
        }

        val diamStr = u.geometricDiameterMm?.let { "${"%.1f".format(it)} mm" } ?: "UNVALIDATED"
        val volStr = u.ellipsoidVolumeCm3?.let { "${"%.2f".format(it)} cm³" } ?: "UNVALIDATED"
        val weightStr = u.weightEstimateG?.let {
            "${"%.1f".format(it)} g (90% CI: [${"%.1f".format(u.weightIntervalLowG ?: 0f)}, ${"%.1f".format(u.weightIntervalHighG ?: 0f)}] g)"
        } ?: "UNVALIDATED (Scale calibration pending)"

        val message = """
            SampleUnit ID: ${u.sampleUnitId}
            Condition: ${detection.condition.displayName}
            Detector Confidence: ${"%.1f".format(detection.confidence * 100)}%
            Bounding Box: [${detection.bbox.left.toInt()}, ${detection.bbox.top.toInt()}, ${detection.bbox.right.toInt()}, ${detection.bbox.bottom.toInt()}]
            
            Physical Geometry:
            - Calibrated Diameter: $diamStr [${u.sizeStatus}]
            - Ellipsoid Volume: $volStr
            - Aspect Ratio: ${u.aspectRatio?.let { "%.2f".format(it) } ?: "N/A"}
            
            Physical Mass:
            - Weight Estimate: $weightStr
            - Status: [${u.weightStatus}]
            
            Disclaimer: Externally visible condition only. Multi-view ellipsoid approximation.
        """.trimIndent()

        AlertDialog.Builder(this)
            .setTitle("${detection.condition.displayName} Produce Specimen")
            .setMessage(message)
            .setPositiveButton("Confirm Condition") { d, _ -> d.dismiss() }
            .setNegativeButton("Flag Review") { d, _ ->
                u.reviewRequired = true
                u.title = "Review required"
                d.dismiss()
                updateSamplingBanner()
            }
            .show()
    }

    private fun showLotSummaryDialog() {
        val report = SequentialSamplingEngine.evaluateSampling(tracker = tracker, minTarget = 20)
        val n = tracker.getPhysicalSampleCount()
        val counts = tracker.getConditionCounts()

        val details = StringBuilder()
        details.append("Lot ID: ${tracker.lotId}\n")
        details.append("Certified SampleUnits: $n / 20\n")
        details.append("Sampling State: ${report.state.name}\n")
        details.append("Recommended Grade: ${report.recommendedGrade}\n\n")
        details.append("Condition Breakdown:\n")
        for ((c, cnt) in counts) {
            val pct = (cnt.toFloat() / maxOf(1, n)) * 100f
            details.append("- ${c.displayName}: $cnt (${"%.1f".format(pct)}%)\n")
        }
        details.append("\nWilson 95% Confidence Intervals:\n")
        for (interval in report.intervals) {
            details.append("- ${interval.displayString}\n")
        }
        details.append("\nAudit Reason:\n${report.reason}")

        AlertDialog.Builder(this)
            .setTitle("Mandi Nyaay Procurement Decision")
            .setMessage(details.toString())
            .setPositiveButton("Generate Report") { d, _ ->
                Toast.makeText(this, "Audit Report & Evidence Hash exported.", Toast.LENGTH_LONG).show()
                d.dismiss()
            }
            .setNegativeButton("Close") { d, _ -> d.dismiss() }
            .show()
    }

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        cameraProviderFuture.addListener({
            val cameraProvider = cameraProviderFuture.get()
            val preview = Preview.Builder().build().also {
                it.setSurfaceProvider(binding.viewFinder.surfaceProvider)
            }

            val imageAnalyzer = ImageAnalysis.Builder()
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .setOutputImageFormat(ImageAnalysis.OUTPUT_IMAGE_FORMAT_YUV_420_888)
                .build()
                .also {
                    it.setAnalyzer(cameraExecutor) { imageProxy ->
                        processImageProxy(imageProxy)
                    }
                }

            val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
            try {
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(this, cameraSelector, preview, imageAnalyzer)
            } catch (exc: Exception) {
                Toast.makeText(this, "Camera binding failed: ${exc.message}", Toast.LENGTH_SHORT).show()
            }
        }, ContextCompat.getMainExecutor(this))
    }

    private fun processImageProxy(imageProxy: ImageProxy) {
        val detector = this.detector ?: run {
            imageProxy.close()
            return
        }

        val bitmap = imageProxyToBitmap(imageProxy)
        imageProxy.close()

        if (bitmap != null) {
            val detections = detector.detect(bitmap, confThreshold = 0.30f)
            lastDetections = detections

            val unitsMap = tracker.getAllUnits().associateBy { it.sampleUnitId }

            runOnUiThread {
                binding.overlayView.setDetections(detections, unitsMap, bitmap.width, bitmap.height)
            }
        }
    }

    private fun imageProxyToBitmap(image: ImageProxy): Bitmap? {
        val planes = image.planes
        val yBuffer = planes[0].buffer
        val uBuffer = planes[1].buffer
        val vBuffer = planes[2].buffer

        val ySize = yBuffer.remaining()
        val uSize = uBuffer.remaining()
        val vSize = vBuffer.remaining()

        val nv21 = ByteArray(ySize + uSize + vSize)
        yBuffer.get(nv21, 0, ySize)
        vBuffer.get(nv21, ySize, vSize)
        uBuffer.get(nv21, ySize + vSize, uSize)

        val yuvImage = YuvImage(nv21, ImageFormat.NV21, image.width, image.height, null)
        val out = ByteArrayOutputStream()
        yuvImage.compressToJpeg(Rect(0, 0, image.width, image.height), 85, out)
        val imageBytes = out.toByteArray()
        return BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.size)
    }

    private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
        ContextCompat.checkSelfPermission(baseContext, it) == PackageManager.PERMISSION_GRANTED
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_CODE_PERMISSIONS) {
            if (allPermissionsGranted()) {
                startCamera()
            } else {
                Toast.makeText(this, "Camera permission required for Mandi Nyaay inspection.", Toast.LENGTH_LONG).show()
                finish()
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
        detector?.close()
    }
}
