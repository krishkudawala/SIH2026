import 'package:flutter/foundation.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/inspection_session.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/onion_record.dart';
import 'package:sih2631/manid_nyaay/data/fixture/lot_repository.dart';
import 'package:sih2631/manid_nyaay/data/fixture/repository.dart';
import 'package:uuid/uuid.dart';

class InspectionViewModel extends ChangeNotifier {
  final String lotId;

  final FixtureInspectionRepository _inspectionRepo =
  FixtureInspectionRepository();
  final FixtureLotRepository _lotRepo = FixtureLotRepository();
  final Uuid _uuid = const Uuid();

  late InspectionUiState _uiState;
  InspectionUiState get uiState => _uiState;

  InspectionViewModel({required this.lotId}) {
    _uiState = InspectionUiState(lotId: lotId);
    _init();
  }

  Future<void> _init() async {
    final lot = await _lotRepo.getLotById(lotId);

    _uiState = _uiState.copyWith(
      currentState: InspectionState.sourceSelection,
      samplingPlan: lot?.samplingPlan,
      sessionId: _uuid.v4(),
    );
    notifyListeners();
  }

  void selectBag(int bagNumber, BagTier tier) {
    final selection = BagSelection(
      bagNumber: bagNumber,
      tier: tier,
      selectedByInspector: true,
      timestamp: DateTime.now(),
    );

    _uiState = _uiState.copyWith(
      selectedBag: selection,
      currentState: InspectionState.batchTopCapture,
      completedOrientations: const [],
    );
    notifyListeners();
  }

  void completeCapture(CaptureOrientation orientation) {
    final completed = List<CaptureOrientation>.from(
      _uiState.completedOrientations,
    )..add(orientation);

    InspectionState nextState;
    if (!completed.contains(CaptureOrientation.top)) {
      nextState = InspectionState.batchTopCapture;
    } else if (!completed.contains(CaptureOrientation.side)) {
      nextState = InspectionState.batchSideCapture;
    } else if (!completed.contains(CaptureOrientation.underside)) {
      nextState = InspectionState.batchUndersideCapture;
    } else {
      nextState = InspectionState.crossViewCorrespondence;
    }

    _uiState = _uiState.copyWith(
      completedOrientations: completed,
      currentState: nextState,
    );
    notifyListeners();
  }

  Future<void> confirmCorrespondence() async {
    _uiState = _uiState.copyWith(currentState: InspectionState.perOnionResult);
    notifyListeners();

    final records = await _inspectionRepo.getOnionRecords(_uiState.sessionId);
    _uiState = _uiState.copyWith(onionRecords: records);
    notifyListeners();
  }

  void proceedToSufficiency() {
    _uiState = _uiState.copyWith(
      currentState: InspectionState.samplingSufficiency,
    );
    notifyListeners();
  }

  void sampleNextBag() {
    _uiState = _uiState.copyWith(
      currentState: InspectionState.sourceSelection,
      clearSelectedBag: true,
      completedOrientations: const [],
    );
    notifyListeners();
  }

  void finishInspection() {
    _uiState = _uiState.copyWith(currentState: InspectionState.finalResult);
    notifyListeners();
  }
}

class InspectionUiState {
  final String lotId;
  final InspectionState currentState;
  final BagSelection? selectedBag;
  final List<CaptureOrientation> completedOrientations;
  final List<OnionRecord> onionRecords;
  final SamplingPlan? samplingPlan;
  final String sessionId;
  final bool lightOk;
  final bool focusOk;
  final bool markerOk;

  const InspectionUiState({
    this.lotId = "",
    this.currentState = InspectionState.idle,
    this.selectedBag,
    this.completedOrientations = const [],
    this.onionRecords = const [],
    this.samplingPlan,
    this.sessionId = "",
    this.lightOk = true,
    this.focusOk = true,
    this.markerOk = true,
  });

  InspectionUiState copyWith({
    String? lotId,
    InspectionState? currentState,
    BagSelection? selectedBag,
    bool clearSelectedBag = false,
    List<CaptureOrientation>? completedOrientations,
    List<OnionRecord>? onionRecords,
    SamplingPlan? samplingPlan,
    String? sessionId,
    bool? lightOk,
    bool? focusOk,
    bool? markerOk,
  }) {
    return InspectionUiState(
      lotId: lotId ?? this.lotId,
      currentState: currentState ?? this.currentState,
      selectedBag:
      clearSelectedBag ? null : (selectedBag ?? this.selectedBag),
      completedOrientations:
      completedOrientations ?? this.completedOrientations,
      onionRecords: onionRecords ?? this.onionRecords,
      samplingPlan: samplingPlan ?? this.samplingPlan,
      sessionId: sessionId ?? this.sessionId,
      lightOk: lightOk ?? this.lightOk,
      focusOk: focusOk ?? this.focusOk,
      markerOk: markerOk ?? this.markerOk,
    );
  }
}