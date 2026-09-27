import 'package:flutter/foundation.dart';
// --- Assumed Imports (Replace with actual paths) ---
// import 'package:mandi_nyaay/domain/model/review_item.dart';
// import 'package:mandi_nyaay/domain/model/review_status.dart';
// import 'package:mandi_nyaay/domain/model/grade.dart';
// import 'package:mandi_nyaay/data/fixture/fixture_review_repository.dart';

class ReviewUiState {
  final List<dynamic> pendingItems; // Replace dynamic with ReviewItem
  final List<dynamic> disputedItems; // Replace dynamic with ReviewItem
  final int selectedTab;
  final bool showOverrideDialog;
  final String? overrideSampleId;
  final String overrideReason;

  const ReviewUiState({
    this.pendingItems = const [],
    this.disputedItems = const [],
    this.selectedTab = 0,
    this.showOverrideDialog = false,
    this.overrideSampleId,
    this.overrideReason = "",
  });

  ReviewUiState copyWith({
    List<dynamic>? pendingItems,
    List<dynamic>? disputedItems,
    int? selectedTab,
    bool? showOverrideDialog,
    String? overrideSampleId,
    bool clearOverrideSampleId = false, // Flag to explicitly nullify
    String? overrideReason,
  }) {
    return ReviewUiState(
      pendingItems: pendingItems ?? this.pendingItems,
      disputedItems: disputedItems ?? this.disputedItems,
      selectedTab: selectedTab ?? this.selectedTab,
      showOverrideDialog: showOverrideDialog ?? this.showOverrideDialog,
      overrideSampleId: clearOverrideSampleId ? null : (overrideSampleId ?? this.overrideSampleId),
      overrideReason: overrideReason ?? this.overrideReason,
    );
  }
}

class ReviewViewModel extends ChangeNotifier {
  // final FixtureReviewRepository _repository = FixtureReviewRepository();

  ReviewUiState _uiState = const ReviewUiState();
  ReviewUiState get uiState => _uiState;

  ReviewViewModel() {
    _initObservers();
  }

  void _initObservers() {
    // Equivalent to repository.observeReviewItems().collect
    // For now, loading dummy empty data to prevent errors
    _uiState = _uiState.copyWith(
      pendingItems: [],
      disputedItems: [],
    );
    notifyListeners();
  }

  void onTabSelected(int tab) {
    _uiState = _uiState.copyWith(selectedTab: tab);
    notifyListeners();
  }

  void acceptReview(String sampleId) async {
    // await _repository.acceptReview(sampleId);
  }

  void requestRecapture(String sampleId) async {
    // await _repository.requestRecapture(sampleId);
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

  void confirmOverride(dynamic grade) async { // Replace dynamic with Grade
    final sampleId = _uiState.overrideSampleId;
    final reason = _uiState.overrideReason;

    if (sampleId == null || reason.trim().isEmpty) return;

    // await _repository.overrideReview(sampleId, grade, reason);
    dismissOverrideDialog();
  }
}