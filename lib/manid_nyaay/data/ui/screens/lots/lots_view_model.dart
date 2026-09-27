import 'package:flutter/foundation.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/fixture/lot_repository.dart';
// Import your domain models and repositories
// import 'package:mandi_nyaay/domain/model/lot.dart';
// import 'package:mandi_nyaay/domain/model/lot_status.dart';
// import 'package:mandi_nyaay/data/fixture/fixture_lot_repository.dart';

enum LotFilter { all, active, completed, needsReview }

class LotsUiState {
  final String searchQuery;
  final LotFilter activeFilter;
  final List<Lot> filteredLots;

  const LotsUiState({
    this.searchQuery = "",
    this.activeFilter = LotFilter.all,
    this.filteredLots = const [],
  });

  LotsUiState copyWith({
    String? searchQuery,
    LotFilter? activeFilter,
    List<Lot>? filteredLots,
  }) {
    return LotsUiState(
      searchQuery: searchQuery ?? this.searchQuery,
      activeFilter: activeFilter ?? this.activeFilter,
      filteredLots: filteredLots ?? this.filteredLots,
    );
  }
}

class LotsViewModel extends ChangeNotifier {
  final FixtureLotRepository _repository = FixtureLotRepository();
  List<Lot> _allLots = [];

  LotsUiState _uiState = const LotsUiState();
  LotsUiState get uiState => _uiState;

  LotsViewModel() {
    _loadLots();
  }

  Future<void> _loadLots() async {
    _allLots = await _repository.getAllLots(); // Assume this exists in your repo
    _applyFilters();
  }

  void onSearchQueryChanged(String query) {
    _uiState = _uiState.copyWith(searchQuery: query);
    _applyFilters();
  }

  void onFilterChanged(LotFilter filter) {
    _uiState = _uiState.copyWith(activeFilter: filter);
    _applyFilters();
  }

  void _applyFilters() {
    final query = _uiState.searchQuery.toLowerCase();

    final filtered = _allLots.where((lot) {
      // Apply Search
      final matchesSearch = query.isEmpty ||
          lot.id.toLowerCase().contains(query) ||
          lot.farmerName.toLowerCase().contains(query) ||
          lot.village.toLowerCase().contains(query);

      if (!matchesSearch) return false;

      // Apply Filter Chip
      switch (_uiState.activeFilter) {
        case LotFilter.all:
          return true;
        case LotFilter.active:
          return lot.status == LotStatus.active;
        case LotFilter.completed:
          return lot.status == LotStatus.completed;
        case LotFilter.needsReview:
          return lot.status == LotStatus.needsReview;
      }
    }).toList();

    _uiState = _uiState.copyWith(filteredLots: filtered);
    notifyListeners();
  }
}