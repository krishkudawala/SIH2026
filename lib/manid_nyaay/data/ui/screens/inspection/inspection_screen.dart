import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/inspection_session.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/ai_inference_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/batch_capture_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/cross_view_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/decision_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/dispute_dialog.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/evidence_replay_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/measurement_weight_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/per_onion_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/report_receipt_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/review_queue_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/sampling_sufficiency_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/source_selection_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/result/grading_result_screen.dart';

class InspectionScreen extends StatefulWidget {
  final String lotId;

  const InspectionScreen({super.key, required this.lotId});

  @override
  State<InspectionScreen> createState() => _InspectionScreenState();
}

class _InspectionScreenState extends State<InspectionScreen> {
  late final InspectionViewModel _vm;

  @override
  void initState() {
    super.initState();
    _vm = InspectionViewModel(lotId: widget.lotId);
    _vm.addListener(_onChanged);
  }

  void _onChanged() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _vm.removeListener(_onChanged);
    _vm.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = _vm.uiState;

    switch (s.currentState) {
      case InspectionState.idle:
        return const Scaffold(
          backgroundColor: Color(0xFFF4F5F7),
          body: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(color: Color(0xFF1565C0)),
                SizedBox(height: 16),
                Text(
                  "Initializing Mandi Nyaay Backend Session...",
                  style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF64748B)),
                ),
              ],
            ),
          ),
        );

      case InspectionState.sourceSelection:
        return SourceSelectionScreen(
          uiState: s,
          onBagSelected: (bagNum, tier) => _vm.selectBag(bagNum, tier),
          onBack: () => Navigator.of(context).maybePop(),
        );

      case InspectionState.batchTopCapture:
      case InspectionState.batchSideCapture:
      case InspectionState.batchUndersideCapture:
        return BatchCaptureScreen(
          uiState: s,
          onImageCaptured: (file, orientation) => _vm.handleImageCaptured(file, orientation),
          onBytesCaptured: (bytes, filename, orientation) => _vm.handleImageBytesCaptured(bytes, filename, orientation),
          onCaptureComplete: () {
            final orientation = !s.completedOrientations.contains(CaptureOrientation.top)
                ? CaptureOrientation.top
                : !s.completedOrientations.contains(CaptureOrientation.side)
                    ? CaptureOrientation.side
                    : CaptureOrientation.underside;
            _vm.completeCapture(orientation);
          },
          onBack: () => _vm.sampleNextBag(),
        );

      case InspectionState.crossViewCorrespondence:
        return CrossViewScreen(
          uiState: s,
          onConfirm: () => _vm.runAIInference(),
          onBack: () => _vm.sampleNextBag(),
        );

      case InspectionState.aiInference:
        return AiInferenceScreen(
          uiState: s,
          onCancel: () => _vm.sampleNextBag(),
        );

      case InspectionState.perOnionResult:
        return PerOnionResultScreen(
          uiState: s,
          onProceed: () => _vm.proceedToSufficiency(),
          onBack: () => _vm.sampleNextBag(),
        );

      case InspectionState.samplingSufficiency:
        return SamplingSufficiencyScreen(
          uiState: s,
          onSampleNextBag: () => _vm.sampleNextBag(),
          onProceed: () => _vm.proceedToMeasurementWeight(),
          onBack: () => _vm.sampleNextBag(),
        );

      case InspectionState.measurementWeight:
        return MeasurementWeightScreen(
          uiState: s,
          onProceed: () => _vm.proceedToReview(),
          onBack: () => _vm.proceedToSufficiency(),
        );

      case InspectionState.reviewQueue:
        return ReviewQueueScreen(
          uiState: s,
          onProceed: () => _vm.evaluateDecision(),
          onBack: () => _vm.proceedToMeasurementWeight(),
        );

      case InspectionState.decision:
        return DecisionScreen(
          uiState: s,
          onProceed: () => _vm.verifyEvidenceAndReplay(),
          onBack: () => _vm.proceedToReview(),
          onOverride: (grade, reason) => _vm.evaluateDecision(overrideGrade: grade, overrideReason: reason),
        );

      case InspectionState.evidenceReplay:
        return EvidenceReplayScreen(
          uiState: s,
          onProceed: () => _vm.generateReport(),
          onBack: () => _vm.evaluateDecision(),
          onOpenDispute: () {
            DisputeDialog.showOpenDisputeDialog(
              context: context,
              sessionId: s.sessionId,
              onSubmit: (reason, openedBy) => _vm.openDispute(reason, openedBy),
            );
          },
        );

      case InspectionState.reportReceipt:
        return ReportReceiptScreen(
          uiState: s,
          onFinish: () => Navigator.of(context).pop(),
          onBack: () => _vm.verifyEvidenceAndReplay(),
        );

      case InspectionState.dispute:
        return Scaffold(
          backgroundColor: const Color(0xFFF4F5F7),
          appBar: AppBar(
            title: const Text("Formal Lot Dispute"),
            backgroundColor: const Color(0xFFE65100),
            foregroundColor: Colors.white,
          ),
          body: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  "DISPUTE ARBITRATION ACTIVE",
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFFE65100)),
                ),
                const SizedBox(height: 8),
                Text(
                  "Dispute ID: ${s.disputeData?['id'] ?? 'Pending'}\nReason: ${s.disputeData?['dispute_reason'] ?? 'Grade challenge'}\nStatus: ${s.disputeData?['status'] ?? 'OPEN'}",
                  style: const TextStyle(fontSize: 13),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () {
                    DisputeDialog.showResolveDisputeDialog(
                      context: context,
                      sessionId: s.sessionId,
                      onSubmit: (grade, arbId, notes) => _vm.resolveDispute(grade, arbId, notes),
                    );
                  },
                  child: const Text("RECORD ARBITRATOR BINDING RULING"),
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: () => _vm.generateReport(),
                  child: const Text("CONTINUE TO REPORT"),
                ),
              ],
            ),
          ),
        );

      case InspectionState.finalResult:
        return GradingResultScreen(lotId: widget.lotId);
    }
  }
}