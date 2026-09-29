import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';

class AiInferenceScreen extends StatelessWidget {
  final InspectionUiState uiState;
  final VoidCallback onCancel;

  const AiInferenceScreen({
    super.key,
    required this.uiState,
    required this.onCancel,
  });

  @override
  Widget build(BuildContext context) {
    // ---------- MediaQuery ----------
    final mq = MediaQuery.of(context);
    final double screenWidth = mq.size.width;
    final bool isTablet = screenWidth >= 600;

    // Scale factor relative to a 360dp design width, clamped to stay sane
    final double scale = (screenWidth / 360).clamp(0.85, 1.4);

    final double outerPadding = (screenWidth * 0.06).clamp(16.0, 40.0);
    final double cardPadding = 24.0 * scale;
    final double loaderSize = 64.0 * scale;
    final double titleFont = 18.0 * scale;
    final double subtitleFont = 13.0 * scale;
    final double stepFont = 12.0 * scale;
    final double stepIconSize = 16.0 * scale;
    final double maxCardWidth = isTablet ? 500 : double.infinity;

    return Scaffold(
      backgroundColor: const Color(0xFFF4F5F7),
      appBar: const MandiTopAppBar(
        title: "AI Produce Inspection",
        subtitle: "ONNX Neural Inference Active",
        showBack: false,
      ),
      body: Center(
        child: Padding(
          padding: EdgeInsets.all(outerPadding),
          child: ConstrainedBox(
            constraints: BoxConstraints(maxWidth: maxCardWidth),
            child: Card(
              elevation: 4.0,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16.0)),
              child: Padding(
                padding: EdgeInsets.all(cardPadding),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SizedBox(
                      width: loaderSize,
                      height: loaderSize,
                      child: const CircularProgressIndicator(
                        strokeWidth: 4,
                        color: Color(0xFF1565C0),
                      ),
                    ),
                    SizedBox(height: 24 * scale),
                    Text(
                      "Running ONNX Model Inference",
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: titleFont,
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFF1E293B),
                      ),
                    ),
                    SizedBox(height: 8 * scale),
                    Text(
                      "Evaluating produce with onion-grading-v7.onnx\nSession: ${uiState.sessionId.isNotEmpty ? uiState.sessionId : 'Initializing...'}",
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: subtitleFont, color: const Color(0xFF64748B)),
                    ),
                    SizedBox(height: 20 * scale),
                    Container(
                      width: double.infinity,
                      padding: EdgeInsets.all(12 * scale),
                      decoration: BoxDecoration(
                        color: const Color(0xFFE1F5FE),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.check_circle, size: stepIconSize, color: const Color(0xFF1565C0)),
                              SizedBox(width: 8 * scale),
                              Expanded(
                                child: Text("Optical quality screening complete", style: TextStyle(fontSize: stepFont)),
                              ),
                            ],
                          ),
                          SizedBox(height: 6 * scale),
                          Row(
                            children: [
                              Icon(Icons.check_circle, size: stepIconSize, color: const Color(0xFF1565C0)),
                              SizedBox(width: 8 * scale),
                              Expanded(
                                child: Text("Produce boundary segmentation", style: TextStyle(fontSize: stepFont)),
                              ),
                            ],
                          ),
                          SizedBox(height: 6 * scale),
                          Row(
                            children: [
                              Icon(Icons.sync, size: stepIconSize, color: const Color(0xFF1565C0)),
                              SizedBox(width: 8 * scale),
                              Expanded(
                                child: Text(
                                  "Extracting Wilson confidence intervals...",
                                  style: TextStyle(fontSize: stepFont, fontWeight: FontWeight.bold),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    if (uiState.errorMessage != null) ...[
                      SizedBox(height: 16 * scale),
                      Text(
                        uiState.errorMessage!,
                        style: TextStyle(color: Colors.red, fontSize: subtitleFont),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}