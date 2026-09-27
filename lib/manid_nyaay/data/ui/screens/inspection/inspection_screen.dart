import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/inspection_session.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/batch_capture_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/cross_view_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/per_onion_screen.dart';
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
          body: Center(child: CircularProgressIndicator()),
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
          onConfirm: () => _vm.confirmCorrespondence(),
          onBack: () => _vm.sampleNextBag(),
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
          onFinish: () => _vm.finishInspection(),
          onBack: () => _vm.sampleNextBag(),
        );

      case InspectionState.finalResult:
        return GradingResultScreen(lotId: widget.lotId);
    }
  }
}