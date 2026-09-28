import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:sih2631/manid_nyaay/data/api/active_session_store.dart';
import 'package:sih2631/manid_nyaay/data/api/api_client.dart';
import 'package:sih2631/manid_nyaay/data/api/api_config.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/inspection_session.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/onion_record.dart';
import 'package:sih2631/manid_nyaay/data/fixture/lot_repository.dart';

class InspectionUiState {
  final String lotId;
  final String sessionId;
  final InspectionState currentState;
  final BagSelection? selectedBag;
  final List<CaptureOrientation> completedOrientations;
  final File? lastCapturedFile;
  final Uint8List? lastCapturedBytes;

  final bool isUploading;
  final String uploadStatusMessage;
  final bool isInferenceRunning;
  final String? errorMessage;
  final bool isBackendConnected;

  final List<Map<String, dynamic>> rawObservations;
  final List<Map<String, dynamic>> rawSampleUnits;
  final Map<String, dynamic>? samplingData;
  final Map<String, dynamic>? measurementData;
  final Map<String, dynamic>? weightData;
  final Map<String, dynamic>? reviewData;
  final Map<String, dynamic>? decisionData;
  final Map<String, dynamic>? evidenceData;
  final Map<String, dynamic>? replayData;
  final Map<String, dynamic>? reportData;
  final Map<String, dynamic>? disputeData;

  // Compatibility fields
  final List<OnionRecord> onionRecords;
  final SamplingPlan? samplingPlan;
  final bool lightOk;
  final bool focusOk;
  final bool markerOk;

  // Lot metadata from real session
  final int declaredBagCount;
  final double certifiedLotWeightKg;
  final String farmerName;

  const InspectionUiState({
    this.lotId = "",
    this.sessionId = "",
    this.currentState = InspectionState.idle,
    this.selectedBag,
    this.completedOrientations = const [],
    this.lastCapturedFile,
    this.lastCapturedBytes,
    this.isUploading = false,
    this.uploadStatusMessage = "",
    this.isInferenceRunning = false,
    this.errorMessage,
    this.isBackendConnected = false,
    this.rawObservations = const [],
    this.rawSampleUnits = const [],
    this.samplingData,
    this.measurementData,
    this.weightData,
    this.reviewData,
    this.decisionData,
    this.evidenceData,
    this.replayData,
    this.reportData,
    this.disputeData,
    this.onionRecords = const [],
    this.samplingPlan,
    this.lightOk = true,
    this.focusOk = true,
    this.markerOk = true,
    this.declaredBagCount = 0,
    this.certifiedLotWeightKg = 0.0,
    this.farmerName = '',
  });

  InspectionUiState copyWith({
    String? lotId,
    String? sessionId,
    InspectionState? currentState,
    BagSelection? selectedBag,
    bool clearSelectedBag = false,
    List<CaptureOrientation>? completedOrientations,
    File? lastCapturedFile,
    Uint8List? lastCapturedBytes,
    bool? isUploading,
    String? uploadStatusMessage,
    bool? isInferenceRunning,
    String? errorMessage,
    bool clearError = false,
    bool? isBackendConnected,
    List<Map<String, dynamic>>? rawObservations,
    List<Map<String, dynamic>>? rawSampleUnits,
    Map<String, dynamic>? samplingData,
    Map<String, dynamic>? measurementData,
    Map<String, dynamic>? weightData,
    Map<String, dynamic>? reviewData,
    Map<String, dynamic>? decisionData,
    Map<String, dynamic>? evidenceData,
    Map<String, dynamic>? replayData,
    Map<String, dynamic>? reportData,
    Map<String, dynamic>? disputeData,
    List<OnionRecord>? onionRecords,
    SamplingPlan? samplingPlan,
    bool? lightOk,
    bool? focusOk,
    bool? markerOk,
    int? declaredBagCount,
    double? certifiedLotWeightKg,
    String? farmerName,
  }) {
    return InspectionUiState(
      lotId: lotId ?? this.lotId,
      sessionId: sessionId ?? this.sessionId,
      currentState: currentState ?? this.currentState,
      selectedBag: clearSelectedBag ? null : (selectedBag ?? this.selectedBag),
      completedOrientations: completedOrientations ?? this.completedOrientations,
      lastCapturedFile: lastCapturedFile ?? this.lastCapturedFile,
      lastCapturedBytes: lastCapturedBytes ?? this.lastCapturedBytes,
      isUploading: isUploading ?? this.isUploading,
      uploadStatusMessage: uploadStatusMessage ?? this.uploadStatusMessage,
      isInferenceRunning: isInferenceRunning ?? this.isInferenceRunning,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      isBackendConnected: isBackendConnected ?? this.isBackendConnected,
      rawObservations: rawObservations ?? this.rawObservations,
      rawSampleUnits: rawSampleUnits ?? this.rawSampleUnits,
      samplingData: samplingData ?? this.samplingData,
      measurementData: measurementData ?? this.measurementData,
      weightData: weightData ?? this.weightData,
      reviewData: reviewData ?? this.reviewData,
      decisionData: decisionData ?? this.decisionData,
      evidenceData: evidenceData ?? this.evidenceData,
      replayData: replayData ?? this.replayData,
      reportData: reportData ?? this.reportData,
      disputeData: disputeData ?? this.disputeData,
      onionRecords: onionRecords ?? this.onionRecords,
      samplingPlan: samplingPlan ?? this.samplingPlan,
      lightOk: lightOk ?? this.lightOk,
      focusOk: focusOk ?? this.focusOk,
      markerOk: markerOk ?? this.markerOk,
      declaredBagCount: declaredBagCount ?? this.declaredBagCount,
      certifiedLotWeightKg: certifiedLotWeightKg ?? this.certifiedLotWeightKg,
      farmerName: farmerName ?? this.farmerName,
    );
  }
}

class InspectionViewModel extends ChangeNotifier {
  final String lotId;
  final MandiApiClient _api = MandiApiClient();
  final FixtureLotRepository _lotRepo = FixtureLotRepository();

  late InspectionUiState _uiState;
  InspectionUiState get uiState => _uiState;

  InspectionViewModel({required this.lotId}) {
    _uiState = InspectionUiState(lotId: lotId);
    _init();
  }

  Future<void> _init() async {
    _uiState = _uiState.copyWith(
      currentState: InspectionState.idle,
      uploadStatusMessage: "Checking backend connection...",
    );
    notifyListeners();

    final connected = await ApiConfig.checkConnection();
    final lot = await _lotRepo.getLotById(lotId);

    String sessionId = "";
    String? err;

    if (connected) {
      try {
        final sessionStore = ActiveSessionStore();
        await sessionStore.loadFromDisk();

        if (sessionStore.hasActiveSession && sessionStore.lotId == lotId) {
          sessionId = sessionStore.sessionId!;
        } else {
          final declaredBags = lot?.bagCount ?? 50;
          final certWeight = lot?.certifiedWeightKg ?? (declaredBags * 50.0);
          final srcRef = lot?.farmerName ?? "BAG_INSPECTOR_SELECTED";

          final session = await _api.createSession(
            lotId: lotId,
            sourceReference: srcRef,
            targetSampleSize: lot?.samplingPlan?.totalSamplesRequired ?? 20,
            rulePackId: "AGMARK_ONION_2024_V1",
            declaredBagCount: declaredBags,
            certifiedLotWeightKg: certWeight,
          );
          sessionId = session['id'] ?? "";
          sessionStore.setActiveSession(
            sessionId: sessionId,
            lotId: lotId,
            sourceReference: srcRef,
            createdAt: DateTime.now(),
            inspectionStatus: session['status'] ?? "CREATED",
            targetSampleSize: lot?.samplingPlan?.totalSamplesRequired ?? 20,
            declaredBagCount: declaredBags,
            certifiedLotWeightKg: certWeight,
          );
        }
      } catch (e) {
        err = "Failed to create backend session: $e";
      }
    } else {
      err = "Backend not reachable at ${ApiConfig.baseUrl}. Check LAN Wi-Fi connection.";
    }

    _uiState = _uiState.copyWith(
      isBackendConnected: connected,
      sessionId: sessionId,
      samplingPlan: lot?.samplingPlan,
      currentState: InspectionState.sourceSelection,
      errorMessage: err,
      declaredBagCount: lot?.bagCount ?? 0,
      certifiedLotWeightKg: lot?.certifiedWeightKg ?? 0.0,
      farmerName: lot?.farmerName ?? '',
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
      clearError: true,
    );
    notifyListeners();
  }

  Future<void> handleImageBytesCaptured(
    Uint8List bytes,
    String filename,
    CaptureOrientation orientation,
  ) async {
    _uiState = _uiState.copyWith(
      isUploading: true,
      uploadStatusMessage: "Encoding image (${orientation.displayLabel})...",
      lastCapturedBytes: bytes,
      clearError: true,
    );
    notifyListeners();

    try {
      final base64String = base64Encode(bytes);

      _uiState = _uiState.copyWith(
        uploadStatusMessage: "Uploading capture to Mandi Nyaay Backend...",
      );
      notifyListeners();

      if (_uiState.sessionId.isNotEmpty) {
        await _api.addCapture(
          _uiState.sessionId,
          imageBase64: base64String,
          filename: filename,
          captureRole: orientation == CaptureOrientation.top
              ? "PRIMARY_SAMPLE_CAPTURE"
              : "DETAIL_RECAPTURE",
          viewAngle: orientation.name.toUpperCase(),
        );
      }

      final completed = List<CaptureOrientation>.from(_uiState.completedOrientations)
        ..add(orientation);

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
        isUploading: false,
        uploadStatusMessage: "",
        completedOrientations: completed,
        currentState: nextState,
      );
    } catch (e) {
      _uiState = _uiState.copyWith(
        isUploading: false,
        uploadStatusMessage: "",
        errorMessage: "Capture upload failed: $e",
      );
    }
    notifyListeners();
  }

  Future<void> handleImageCaptured(File file, CaptureOrientation orientation) async {
    try {
      final bytes = await file.readAsBytes();
      final filename = file.path.split(RegExp(r'[/\\]')).last;
      _uiState = _uiState.copyWith(lastCapturedFile: file);
      await handleImageBytesCaptured(bytes, filename, orientation);
    } catch (e) {
      _uiState = _uiState.copyWith(errorMessage: "Failed to read file: $e");
      notifyListeners();
    }
  }

  void completeCapture(CaptureOrientation orientation) {
    final completed = List<CaptureOrientation>.from(_uiState.completedOrientations);
    if (!completed.contains(orientation)) {
      completed.add(orientation);
    }

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

  Future<void> runAIInference() async {
    if (_uiState.sessionId.isEmpty) {
      _uiState = _uiState.copyWith(
        errorMessage: "Cannot run inference: No active backend session.",
      );
      notifyListeners();
      return;
    }

    _uiState = _uiState.copyWith(
      isInferenceRunning: true,
      currentState: InspectionState.aiInference,
      clearError: true,
    );
    notifyListeners();

    try {
      // 1. Run ONNX inference
      await _api.runInference(_uiState.sessionId);

      // 2. Fetch observations & sample units
      final rawObs = await _api.getObservations(_uiState.sessionId);
      final rawUnits = await _api.getSampleUnits(_uiState.sessionId);

      // 3. Fetch sampling, measurement, weight
      final sampling = await _api.getSampling(_uiState.sessionId);
      final meas = await _api.getMeasurement(_uiState.sessionId);
      final weight = await _api.getWeight(_uiState.sessionId);

      final obsList = rawObs.map((e) => Map<String, dynamic>.from(e)).toList();
      final unitsList = rawUnits.map((e) => Map<String, dynamic>.from(e)).toList();

      // Map to OnionRecord models for backward compatibility if needed
      final records = obsList.asMap().entries.map((entry) {
        final idx = entry.key + 1;
        final o = entry.value;
        final cond = o['condition'] ?? 'HEALTHY';
        Grade g = Grade.gradeA;
        if (cond == 'DAMAGED' || cond == 'SPROUTED') g = Grade.urs;
        if (cond == 'ROTTEN') g = Grade.reject;

        return OnionRecord(
          id: o['id'] ?? "obs_$idx",
          sessionId: _uiState.sessionId,
          batchCaptureIds: const [],
          diameterMm: (o['size_mm'] as num?)?.toDouble() ?? 0.0,
          estimatedWeightGrams: (o['weight_g'] as num?)?.toDouble() ?? 0.0,
          grade: g,
          defects: const [],
        );
      }).toList();

      _uiState = _uiState.copyWith(
        isInferenceRunning: false,
        rawObservations: obsList,
        rawSampleUnits: unitsList,
        samplingData: sampling,
        measurementData: meas,
        weightData: weight,
        onionRecords: records,
        currentState: InspectionState.perOnionResult,
      );
    } catch (e) {
      _uiState = _uiState.copyWith(
        isInferenceRunning: false,
        errorMessage: "Inference failed: $e",
        currentState: InspectionState.sourceSelection,
      );
    }
    notifyListeners();
  }

  void proceedToSufficiency() {
    _uiState = _uiState.copyWith(
      currentState: InspectionState.samplingSufficiency,
      clearError: true,
    );
    notifyListeners();
  }

  void proceedToMeasurementWeight() {
    _uiState = _uiState.copyWith(
      currentState: InspectionState.measurementWeight,
      clearError: true,
    );
    notifyListeners();
  }

  Future<void> proceedToReview() async {
    _uiState = _uiState.copyWith(
      currentState: InspectionState.reviewQueue,
      clearError: true,
    );
    notifyListeners();

    try {
      final review = await _api.getReview(_uiState.sessionId);
      _uiState = _uiState.copyWith(reviewData: review);
    } catch (e) {
      _uiState = _uiState.copyWith(errorMessage: "Failed to load review: $e");
    }
    notifyListeners();
  }

  Future<void> evaluateDecision({String? overrideGrade, String? overrideReason}) async {
    _uiState = _uiState.copyWith(
      currentState: InspectionState.decision,
      clearError: true,
    );
    notifyListeners();

    try {
      final dec = await _api.evaluateDecision(
        _uiState.sessionId,
        overrideGrade: overrideGrade,
        overrideReason: overrideReason,
      );
      _uiState = _uiState.copyWith(decisionData: dec);
    } catch (e) {
      _uiState = _uiState.copyWith(errorMessage: "Decision evaluation failed: $e");
    }
    notifyListeners();
  }

  Future<void> verifyEvidenceAndReplay() async {
    _uiState = _uiState.copyWith(
      currentState: InspectionState.evidenceReplay,
      clearError: true,
    );
    notifyListeners();

    try {
      final evidence = await _api.getEvidence(_uiState.sessionId);
      final replay = await _api.replaySession(_uiState.sessionId);
      _uiState = _uiState.copyWith(
        evidenceData: evidence,
        replayData: replay,
      );
    } catch (e) {
      _uiState = _uiState.copyWith(errorMessage: "Evidence / Replay failed: $e");
    }
    notifyListeners();
  }

  Future<void> generateReport() async {
    _uiState = _uiState.copyWith(
      currentState: InspectionState.reportReceipt,
      clearError: true,
    );
    notifyListeners();

    try {
      final report = await _api.getReport(_uiState.sessionId);
      _uiState = _uiState.copyWith(reportData: report);
    } catch (e) {
      _uiState = _uiState.copyWith(errorMessage: "Report generation failed: $e");
    }
    notifyListeners();
  }

  Future<void> openDispute(String reason, String openedBy) async {
    try {
      final disp = await _api.openDispute(
        _uiState.sessionId,
        disputeReason: reason,
        openedBy: openedBy,
      );
      _uiState = _uiState.copyWith(
        disputeData: disp,
        currentState: InspectionState.dispute,
      );
    } catch (e) {
      _uiState = _uiState.copyWith(errorMessage: "Failed to open dispute: $e");
    }
    notifyListeners();
  }

  Future<void> resolveDispute(String finalGrade, String arbitratorId, String notes) async {
    try {
      final resolved = await _api.resolveDispute(
        _uiState.sessionId,
        finalGrade: finalGrade,
        arbitratorId: arbitratorId,
        arbitrationNotes: notes,
      );
      _uiState = _uiState.copyWith(
        disputeData: resolved,
        currentState: InspectionState.dispute,
      );
    } catch (e) {
      _uiState = _uiState.copyWith(errorMessage: "Failed to resolve dispute: $e");
    }
    notifyListeners();
  }

  void sampleNextBag() {
    _uiState = _uiState.copyWith(
      currentState: InspectionState.sourceSelection,
      clearSelectedBag: true,
      completedOrientations: const [],
      clearError: true,
    );
    notifyListeners();
  }

  void finishInspection() {
    _uiState = _uiState.copyWith(currentState: InspectionState.finalResult);
    notifyListeners();
  }
}