import 'package:flutter/foundation.dart';
import 'package:sih2631/manid_nyaay/data/api/api_client.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/onion_record.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/work_load_metrics.dart';

class ReviewUiState {
  final List<ReviewItem> pendingItems;
  final List<ReviewItem> disputedItems;
  final int selectedTab;
  final bool showOverrideDialog;
  final String? overrideSampleId;
  final String overrideReason;
  final bool isLoading;

  const ReviewUiState({
    this.pendingItems = const [],
    this.disputedItems = const [],
    this.selectedTab = 0,
    this.showOverrideDialog = false,
    this.overrideSampleId,
    this.overrideReason = "",
    this.isLoading = true,
  });

  ReviewUiState copyWith({
    List<ReviewItem>? pendingItems,
    List<ReviewItem>? disputedItems,
    int? selectedTab,
    bool? showOverrideDialog,
    String? overrideSampleId,
    bool clearOverrideSampleId = false,
    String? overrideReason,
    bool? isLoading,
  }) {
    return ReviewUiState(
      pendingItems: pendingItems ?? this.pendingItems,
      disputedItems: disputedItems ?? this.disputedItems,
      selectedTab: selectedTab ?? this.selectedTab,
      showOverrideDialog: showOverrideDialog ?? this.showOverrideDialog,
      overrideSampleId: clearOverrideSampleId ? null : (overrideSampleId ?? this.overrideSampleId),
      overrideReason: overrideReason ?? this.overrideReason,
      isLoading: isLoading ?? this.isLoading,
    );
  }
}

class ReviewViewModel extends ChangeNotifier {
  final MandiApiClient _api = MandiApiClient();

  ReviewUiState _uiState = const ReviewUiState();
  ReviewUiState get uiState => _uiState;

  ReviewViewModel() {
    loadReviewItems();
  }

  Future<void> loadReviewItems() async {
    _uiState = _uiState.copyWith(isLoading: true);
    notifyListeners();

    try {
      final sessions = await _api.listSessions(limit: 50);
      final List<ReviewItem> pending = [];
      final List<ReviewItem> disputed = [];

      for (final s in sessions) {
        if (s is! Map) continue;
        final map = Map<String, dynamic>.from(s);
        final id = map['id']?.toString() ?? '';
        final lotId = map['lot_id']?.toString() ?? id;
        final farmer = map['source_reference']?.toString() ?? 'Farmer';
        final status = (map['status'] ?? '').toString().toUpperCase();
        final procGrade = (map['procurement_grade'] ?? '').toString().toUpperCase();

        if (status == 'DISPUTED') {
          disputed.add(ReviewItem(
            sampleId: id,
            lotId: lotId,
            farmerName: farmer,
            weightKg: 1000.0,
            reason: ReviewReason.manualFlag,
            tentativeGrade: Grade.urs,
            confidence: 0.85,
            status: ReviewStatus.disputed,
          ));
        } else if (procGrade == 'MANUAL_REVIEW' || status == 'NEEDS_REVIEW') {
          pending.add(ReviewItem(
            sampleId: id,
            lotId: lotId,
            farmerName: farmer,
            weightKg: 1000.0,
            reason: ReviewReason.weighbridgeSignal,
            tentativeGrade: Grade.urs,
            confidence: 0.88,
            status: ReviewStatus.pending,
          ));
        }
      }

      _uiState = _uiState.copyWith(
        pendingItems: pending,
        disputedItems: disputed,
        isLoading: false,
      );
    } catch (_) {
      _uiState = _uiState.copyWith(
        pendingItems: [],
        disputedItems: [],
        isLoading: false,
      );
    }
    notifyListeners();
  }

  void onTabSelected(int tab) {
    _uiState = _uiState.copyWith(selectedTab: tab);
    notifyListeners();
  }

  Future<void> acceptReview(String sampleId) async {
    try {
      await _api.evaluateDecision(
        sampleId,
        overrideGrade: 'GRADE_A',
        overrideReason: 'APMC Inspector approved review signal',
      );
      await loadReviewItems();
    } catch (_) {}
  }

  Future<void> requestRecapture(String sampleId) async {
    try {
      await _api.evaluateDecision(
        sampleId,
        overrideGrade: 'MANUAL_REVIEW',
        overrideReason: 'Recapture requested due to capture quality',
      );
      await loadReviewItems();
    } catch (_) {}
  }

  void openOverrideDialog(String sampleId) {
    _uiState = _uiState.copyWith(
      showOverrideDialog: true,
      overrideSampleId: sampleId,
      overrideReason: "",
    );
    notifyListeners();
  }

  void onOverrideReasonChanged(String reason) {
    _uiState = _uiState.copyWith(overrideReason: reason);
    notifyListeners();
  }

  void dismissOverrideDialog() {
    _uiState = _uiState.copyWith(
      showOverrideDialog: false,
      clearOverrideSampleId: true,
    );
    notifyListeners();
  }

  Future<void> confirmOverride(dynamic grade) async {
    final sampleId = _uiState.overrideSampleId;
    final reason = _uiState.overrideReason;

    if (sampleId == null || reason.trim().isEmpty) return;

    String gradeStr = 'GRADE_A';
    if (grade == Grade.urs) gradeStr = 'URS';
    if (grade == Grade.reject) gradeStr = 'REJECT';

    try {
      await _api.evaluateDecision(
        sampleId,
        overrideGrade: gradeStr,
        overrideReason: reason,
      );
      dismissOverrideDialog();
      await loadReviewItems();
    } catch (_) {
      dismissOverrideDialog();
    }
  }
}