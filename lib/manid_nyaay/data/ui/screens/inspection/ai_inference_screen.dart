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
    return Scaffold(
      backgroundColor: const Color(0xFFF4F5F7),
      appBar: const MandiTopAppBar(
        title: "AI Produce Inspection",
        subtitle: "ONNX Neural Inference Active",
        showBack: false,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Card(
            elevation: 4.0,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16.0)),
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const SizedBox(
                    width: 64,
                    height: 64,
                    child: CircularProgressIndicator(
                      strokeWidth: 4,
                      color: Color(0xFF1565C0),
                    ),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    "Running ONNX Model Inference",
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1E293B),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "Evaluating produce with onion-grading-v7.onnx\nSession: ${uiState.sessionId.isNotEmpty ? uiState.sessionId : 'Initializing...'}",
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 13, color: Color(0xFF64748B)),
                  ),
                  const SizedBox(height: 20),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE1F5FE),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.check_circle, size: 16, color: Color(0xFF1565C0)),
                            SizedBox(width: 8),
                            Text("Optical quality screening complete", style: TextStyle(fontSize: 12)),
                          ],
                        ),
                        SizedBox(height: 6),
                        Row(
                          children: [
                            Icon(Icons.check_circle, size: 16, color: Color(0xFF1565C0)),
                            SizedBox(width: 8),
                            Text("Produce boundary segmentation", style: TextStyle(fontSize: 12)),
                          ],
                        ),
                        SizedBox(height: 6),
                        Row(
                          children: [
                            Icon(Icons.sync, size: 16, color: Color(0xFF1565C0)),
                            SizedBox(width: 8),
                            Text("Extracting Wilson confidence intervals...", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                          ],
                        ),
                      ],
                    ),
                  ),
                  if (uiState.errorMessage != null) ...[
                    const SizedBox(height: 16),
                    Text(
                      uiState.errorMessage!,
                      style: const TextStyle(color: Colors.red, fontSize: 13),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
