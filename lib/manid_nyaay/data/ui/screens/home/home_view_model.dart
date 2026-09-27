import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:rxdart/rxdart.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/work_load_metrics.dart';
import 'package:sih2631/manid_nyaay/data/fixture/fixture_data.dart';
import 'package:sih2631/manid_nyaay/data/fixture/lot_repository.dart';
import 'package:sih2631/manid_nyaay/data/fixture/repository.dart';

// --- State Data Class ---
class HomeUiState {
  final Inspector inspector;
  final SyncStatus syncStatus;
  final WorkloadMetrics workloadMetrics;
  final List<Lot> activeLots;
  final bool isLoading;

  const HomeUiState({
    required this.inspector,
    required this.syncStatus,
    required this.workloadMetrics,
    this.activeLots = const [],
    this.isLoading = true,
  });

  HomeUiState copyWith({
    Inspector? inspector,
    SyncStatus? syncStatus,
    WorkloadMetrics? workloadMetrics,
    List<Lot>? activeLots,
    bool? isLoading,
  }) {
    return HomeUiState(
      inspector: inspector ?? this.inspector,
      syncStatus: syncStatus ?? this.syncStatus,
      workloadMetrics: workloadMetrics ?? this.workloadMetrics,
      activeLots: activeLots ?? this.activeLots,
      isLoading: isLoading ?? this.isLoading,
    );
  }
}

// --- ViewModel ---
class HomeViewModel extends ChangeNotifier {
  final FixtureLotRepository _lotRepository = FixtureLotRepository();
  final FixtureSyncRepository _syncRepository = FixtureSyncRepository();

  StreamSubscription? _subscription;

  // Initialize with default state mapping to FixtureData
  late HomeUiState _uiState;

  HomeUiState get uiState => _uiState;

  HomeViewModel() {
    _uiState = HomeUiState(
      inspector: FixtureData.inspector,
      syncStatus: FixtureData.syncStatus,
      workloadMetrics: FixtureData.workloadMetrics,
    );
    _initObservers();
  }

  void _initObservers() {
    _subscription = Rx.combineLatest2(
      _lotRepository.observeActiveLots(),
      _syncRepository.observeSyncStatus(),
          (List<Lot> activeLots, SyncStatus syncStatus) {

        final int reviewNeededCount = FixtureData.lots.where((lot) =>
        lot.status == LotStatus.needsReview ||
            lot.status == LotStatus.disputed
        ).length;

        return _uiState.copyWith(
          activeLots: activeLots,
          syncStatus: syncStatus,
          workloadMetrics: WorkloadMetrics(
            activeLots: activeLots.length,
            reviewNeeded: reviewNeededCount,
            syncPending: syncStatus.pendingRecords,
          ),
          isLoading: false,
        );
      },
    ).listen((newState) {
      _uiState = newState;
      notifyListeners();
    });
  }

  @override
  void dispose() {
    _subscription?.cancel();
    super.dispose();
  }
}
