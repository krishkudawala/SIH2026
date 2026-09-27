import 'dart:io';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:path_provider/path_provider.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/inspection_session.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';

// --- Theme Colors ---
const Color institutionalBlue = Color(0xFF1565C0);
const Color statusGreen = Color(0xFF4CAF50);
const Color statusOrange = Color(0xFFFF9800);
const Color surfaceWhite = Colors.white;
const Color textSecondary = Color(0xFF64748B);
const Color textPrimary = Color(0xFF1E293B);

class BatchCaptureScreen extends StatefulWidget {
  final InspectionUiState uiState;
  final VoidCallback onCaptureComplete;
  final VoidCallback onBack;

  const BatchCaptureScreen({
    super.key,
    required this.uiState,
    required this.onCaptureComplete,
    required this.onBack,
  });

  @override
  State<BatchCaptureScreen> createState() => _BatchCaptureScreenState();
}

class _BatchCaptureScreenState extends State<BatchCaptureScreen> with WidgetsBindingObserver {
  CameraController? _cameraController;
  bool _hasCameraPermission = false;
  bool _isCapturing = false;
  bool _isFlashOn = false;
  int _selectedTab = 0; // 0: Camera, 1: Gallery

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeCamera();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _cameraController?.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    final CameraController? cameraController = _cameraController;
    if (cameraController == null || !cameraController.value.isInitialized) return;

    if (state == AppLifecycleState.inactive) {
      cameraController.dispose();
    } else if (state == AppLifecycleState.resumed) {
      _initializeCamera();
    }
  }

  Future<void> _initializeCamera() async {
    final status = await Permission.camera.request();
    setState(() => _hasCameraPermission = status.isGranted);

    if (status.isGranted) {
      try {
        final cameras = await availableCameras();
        final backCamera = cameras.firstWhere(
              (c) => c.lensDirection == CameraLensDirection.back,
          orElse: () => cameras.first,
        );

        _cameraController = CameraController(
          backCamera,
          ResolutionPreset.max,
          enableAudio: false,
        );

        await _cameraController!.initialize();
        if (mounted) setState(() {});
      } catch (_) {}
    }
  }

  Future<void> _toggleFlash() async {
    if (_cameraController == null || !_cameraController!.value.isInitialized) return;
    try {
      setState(() => _isFlashOn = !_isFlashOn);
      await _cameraController!.setFlashMode(_isFlashOn ? FlashMode.torch : FlashMode.off);
    } catch (_) {}
  }

  Future<void> _takePicture(BagSelection bag, CaptureOrientation orientation) async {
    if (_cameraController == null || !_cameraController!.value.isInitialized || _isCapturing) {
      return;
    }

    setState(() {
      _isCapturing = true;
    });

    try {
      final XFile image = await _cameraController!.takePicture();

      final directory = await getExternalStorageDirectory();
      final outputDir = Directory('${directory?.path}/mandiproof_captures');
      if (!await outputDir.exists()) {
        await outputDir.create(recursive: true);
      }

      final timestamp = "${DateTime.now().year}${DateTime.now().month}${DateTime.now().day}_${DateTime.now().hour}${DateTime.now().minute}${DateTime.now().second}";
      final fileName = "bag${bag.bagNumber}_${orientation.name}_$timestamp.jpg";
      final savedImage = File('${outputDir.path}/$fileName');

      await File(image.path).copy(savedImage.path);

      widget.onCaptureComplete();
    } catch (_) {
    } finally {
      if (mounted) setState(() => _isCapturing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final bag = widget.uiState.selectedBag;
    if (bag == null) return const SizedBox.shrink();

    final CaptureOrientation currentOrientation = () {
      if (!widget.uiState.completedOrientations.contains(CaptureOrientation.top)) {
        return CaptureOrientation.top;
      }
      if (!widget.uiState.completedOrientations.contains(CaptureOrientation.side)) {
        return CaptureOrientation.side;
      }
      return CaptureOrientation.underside;
    }();

    final gatesOk = widget.uiState.lightOk && widget.uiState.focusOk && widget.uiState.markerOk;

    return Scaffold(
      backgroundColor: const Color(0xFF1E1E1E),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: textPrimary),
          onPressed: widget.onBack,
        ),
        title: Text(
          "Capture Lot",
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: textPrimary,
          ),
        ),
        centerTitle: true,
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(48.0),
          child: Container(
            color: Colors.white,
            child: Row(
              children: [
                Expanded(
                  child: InkWell(
                    onTap: () => setState(() => _selectedTab = 0),
                    child: Container(
                      alignment: Alignment.center,
                      padding: const EdgeInsets.symmetric(vertical: 12.0),
                      decoration: BoxDecoration(
                        border: Border(
                          bottom: BorderSide(
                            color: _selectedTab == 0 ? institutionalBlue : Colors.transparent,
                            width: 2.5,
                          ),
                        ),
                      ),
                      child: Text(
                        "Camera",
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: _selectedTab == 0 ? institutionalBlue : textSecondary,
                        ),
                      ),
                    ),
                  ),
                ),
                Expanded(
                  child: InkWell(
                    onTap: () => setState(() => _selectedTab = 1),
                    child: Container(
                      alignment: Alignment.center,
                      padding: const EdgeInsets.symmetric(vertical: 12.0),
                      decoration: BoxDecoration(
                        border: Border(
                          bottom: BorderSide(
                            color: _selectedTab == 1 ? institutionalBlue : Colors.transparent,
                            width: 2.5,
                          ),
                        ),
                      ),
                      child: Text(
                        "Gallery",
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: _selectedTab == 1 ? institutionalBlue : textSecondary,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
      body: _selectedTab == 1
          ? Center(
              child: Text(
                "Gallery selection mode",
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.white),
              ),
            )
          : Column(
              children: [
                // ── Camera Preview & Viewfinder ───────────────────────────
                Expanded(
                  flex: 3,
                  child: Stack(
                    children: [
                      Positioned.fill(
                        child: _hasCameraPermission && _cameraController?.value.isInitialized == true
                            ? CameraPreview(_cameraController!)
                            : _buildPermissionFallback(),
                      ),

                      // Viewfinder frame & "Tap to capture"
                      Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              width: 260.0,
                              height: 200.0,
                              decoration: BoxDecoration(
                                border: Border.all(color: Colors.white, width: 2.5),
                                borderRadius: BorderRadius.circular(8.0),
                              ),
                              alignment: Alignment.center,
                              child: Text(
                                "Tap to capture",
                                style: TextStyle(
                                  color: Colors.white.withOpacity(0.9),
                                  fontWeight: FontWeight.w600,
                                  fontSize: 14.0,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),

                      // Quality Gate Indicators
                      Positioned(
                        top: 12.0,
                        right: 12.0,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            _QualityGateIndicator("LIGHT", widget.uiState.lightOk),
                            const SizedBox(height: 4.0),
                            _QualityGateIndicator("FOCUS", widget.uiState.focusOk),
                            const SizedBox(height: 4.0),
                            _QualityGateIndicator("MARKER", widget.uiState.markerOk),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                // ── Capture Guidelines Card ───────────────────────────────
                Container(
                  color: surfaceWhite,
                  padding: const EdgeInsets.all(14.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        "Capture Guidelines",
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: textPrimary,
                        ),
                      ),
                      const SizedBox(height: 8.0),
                      Row(
                        children: [
                          const Expanded(child: _GuidelineItem("Good lighting")),
                          const Expanded(child: _GuidelineItem("Multiple angles")),
                        ],
                      ),
                      const SizedBox(height: 6.0),
                      Row(
                        children: [
                          const Expanded(child: _GuidelineItem("Include size reference (e.g. scale)")),
                          const Expanded(child: _GuidelineItem("Clear and focused images")),
                        ],
                      ),
                    ],
                  ),
                ),

                // ── Bottom Action Toolbar ─────────────────────────────────
                Container(
                  color: surfaceWhite,
                  padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      IconButton(
                        icon: Icon(
                          _isFlashOn ? Icons.flash_on : Icons.flash_off,
                          color: institutionalBlue,
                        ),
                        onPressed: _toggleFlash,
                      ),
                      GestureDetector(
                        onTap: () {
                          if (gatesOk && _hasCameraPermission && !_isCapturing) {
                            _takePicture(bag, currentOrientation);
                          }
                        },
                        child: Container(
                          width: 68.0,
                          height: 68.0,
                          decoration: BoxDecoration(
                            color: institutionalBlue,
                            shape: BoxShape.circle,
                            border: Border.all(color: Colors.white, width: 3.0),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.2),
                                blurRadius: 6.0,
                              ),
                            ],
                          ),
                          alignment: Alignment.center,
                          child: _isCapturing
                              ? const SizedBox(
                                  width: 24.0,
                                  height: 24.0,
                                  child: CircularProgressIndicator(
                                    color: Colors.white,
                                    strokeWidth: 2.5,
                                  ),
                                )
                              : const Icon(
                                  Icons.camera_alt,
                                  color: Colors.white,
                                  size: 32.0,
                                ),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.photo_library, color: institutionalBlue),
                        onPressed: () => setState(() => _selectedTab = 1),
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }

  Widget _buildPermissionFallback() {
    return Container(
      color: const Color(0xFF1A1A1A),
      alignment: Alignment.center,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.camera_alt, color: Colors.white.withOpacity(0.4), size: 64.0),
          const SizedBox(height: 8.0),
          Text(
            "Camera permission required",
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Colors.white.withOpacity(0.7),
            ),
          ),
          const SizedBox(height: 12.0),
          ElevatedButton(
            onPressed: _initializeCamera,
            child: const Text("Grant Camera Permission"),
          ),
        ],
      ),
    );
  }
}

class _GuidelineItem extends StatelessWidget {
  final String text;

  const _GuidelineItem(this.text);

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Icon(Icons.check_circle, color: statusGreen, size: 16.0),
        const SizedBox(width: 6.0),
        Expanded(
          child: Text(
            text,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: textSecondary,
              fontSize: 11.0,
            ),
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}

class _QualityGateIndicator extends StatelessWidget {
  final String label;
  final bool isOk;

  const _QualityGateIndicator(this.label, this.isOk);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.6),
        borderRadius: BorderRadius.circular(12.0),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8.0,
            height: 8.0,
            decoration: BoxDecoration(
              color: isOk ? statusGreen : statusOrange,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 4.0),
          Text(
            label,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: Colors.white,
              fontSize: 10.0,
            ),
          ),
        ],
      ),
    );
  }
}
