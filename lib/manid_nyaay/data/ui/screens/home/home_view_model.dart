import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:sih2631/manid_nyaay/data/api/api_client.dart';
import 'package:sih2631/manid_nyaay/data/api/api_config.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/work_load_metrics.dart';
import 'package:sih2631/manid_nyaay/data/fixture/lot_repository.dart';

// --- State Data Class ---
class HomeUiState {
  final Inspector inspector;
  final SyncStatus syncStatus;
  final WorkloadMetrics workloadMetrics;
  final List<Lot> recentSessions;
  final bool isLoading;
  final String? errorMessage;

  const HomeUiState({
    required this.inspector,
    required this.syncStatus,
    required this.workloadMetrics,
    this.recentSessions = const [],
    this.isLoading = true,
    this.errorMessage,
  });

  HomeUiState copyWith({
    Inspector? inspector,
    SyncStatus? syncStatus,
    WorkloadMetrics? workloadMetrics,
    List<Lot>? recentSessions,
    bool? isLoading,
    String? errorMessage,
    bool clearError = false,
  }) {
    return HomeUiState(
      inspector: inspector ?? this.inspector,
      syncStatus: syncStatus ?? this.syncStatus,
      workloadMetrics: workloadMetrics ?? this.workloadMetrics,
      recentSessions: recentSessions ?? this.recentSessions,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }
}

// --- ViewModel ---
class HomeViewModel extends ChangeNotifier {
  final FixtureLotRepository _lotRepository = FixtureLotRepository();
  final MandiApiClient _api = MandiApiClient();
  StreamSubscription? _subscription;

  late HomeUiState _uiState;
  HomeUiState get uiState => _uiState;

  HomeViewModel() {
    _uiState = HomeUiState(
      inspector: Inspector(
        id: "APMC-INS-01",
        name: "APMC Inspector",
        apmc: "Nashik APMC",
      ),
      syncStatus: const SyncStatus(
        isOnline: false,
        pendingRecords: 0,
        lastSyncedAt: "Connecting...",
      ),
      workloadMetrics: const WorkloadMetrics(
        activeLots: 0,
        reviewNeeded: 0,
        syncPending: 0,
      ),
      isLoading: true,
    );
    _initObservers();
    _refreshDashboard();
  }

  void _initObservers() {
    _subscription = _lotRepository.observeAllLots().listen((allLots) {
      _updateWithLots(allLots);
    });
    ApiConfig.isConnectedNotifier.addListener(_onConnectionChanged);
  }

  void _onConnectionChanged() {
    final isConnected = ApiConfig.isConnectedNotifier.value;
    _uiState = _uiState.copyWith(
      syncStatus: SyncStatus(
        isOnline: isConnected,
        pendingRecords: 0,
        lastSyncedAt: isConnected ? "Live Connected" : "Offline — Last known state",
      ),
    );
    notifyListeners();
    if (isConnected) _refreshDashboard();
  }

  /// Pulls live session data from the backend and updates dashboard metrics.
  Future<void> _refreshDashboard() async {
    try {
      final sessions = await _api.listSessions(limit: 100);
      final allLots = _parseSessions(sessions);

      final activeLots = allLots.where((l) => l.status == LotStatus.active).toList();
      final reviewNeeded = allLots.where((l) =>
          l.status == LotStatus.needsReview || l.status == LotStatus.disputed).length;
      final completed = allLots.where((l) => l.status == LotStatus.completed).length;

      // Recent = last 5 sessions regardless of status
      final recent = allLots.take(5).toList();

      final isConnected = ApiConfig.isConnectedNotifier.value;
      _uiState = _uiState.copyWith(
        recentSessions: recent,
        syncStatus: SyncStatus(
          isOnline: isConnected,
          pendingRecords: 0,
          lastSyncedAt: isConnected ? "Live Connected" : "Offline",
        ),
        workloadMetrics: WorkloadMetrics(
          activeLots: activeLots.length,
          reviewNeeded: reviewNeeded,
          syncPending: completed,
        ),
        isLoading: false,
        clearError: true,
      );
      notifyListeners();
    } catch (e) {
      _uiState = _uiState.copyWith(
        isLoading: false,
        errorMessage: "Unable to load dashboard: $e",
      );
      notifyListeners();
    }
  }

  List<Lot> _parseSessions(List<dynamic> sessions) {
    final mapped = <Lot>[];
    for (final s in sessions) {
      if (s is! Map) continue;
      final map = Map<String, dynamic>.from(s);

      int bagCount = 0;
      double certWeight = 0.0;
      try {
        if (map['data_json'] != null) {
          final dj = jsonDecode(map['data_json'].toString());
          if (dj is Map) {
            bagCount = (dj['declared_bag_count'] as num?)?.toInt() ?? 0;
            certWeight = (dj['certified_lot_weight_kg'] as num?)?.toDouble() ?? 0.0;
          }
        }
      } catch (_) {}

      final statusStr = (map['status'] ?? '').toString().toUpperCase();
      final procGrade = (map['procurement_grade'] ?? '').toString().toUpperCase();

      LotStatus st;
      if (statusStr == 'DISPUTED') {
        st = LotStatus.disputed;
      } else if (procGrade == 'MANUAL_REVIEW') {
        st = LotStatus.needsReview;
      } else if (statusStr == 'COMPLETED' || procGrade.isNotEmpty) {
        st = LotStatus.completed;
      } else {
        st = LotStatus.active;
      }

      mapped.add(Lot(
        id: map['lot_id']?.toString() ?? map['id']?.toString() ?? 'LOT-UNKNOWN',
        farmerId: map['id']?.toString() ?? '',
        farmerName: map['source_reference']?.toString() ?? 'Inspector Selection',
        village: 'APMC Mandi Yard',
        bagCount: bagCount,
        certifiedWeightKg: certWeight,
        weighbridgeRef: 'WB-${map['id'] ?? 'REF'}',
        variety: 'Red Onion',
        location: 'Nashik APMC',
        date: DateTime.tryParse(map['created_at']?.toString() ?? '') ?? DateTime.now(),
        status: st,
        samplingPlan: SamplingPlan(
          totalSamplesRequired: (map['target_sample_size'] as num?)?.toInt() ?? 20,
          completedSamples: st == LotStatus.completed
              ? ((map['target_sample_size'] as num?)?.toInt() ?? 20)
              : 0,
        ),
      ));
    }
    return mapped;
  }

  void _updateWithLots(List<Lot> allLots) {
    final isConnected = ApiConfig.isConnectedNotifier.value;
    final activeLots = allLots.where((lot) => lot.status == LotStatus.active).toList();
    final reviewNeededCount = allLots.where((lot) =>
        lot.status == LotStatus.needsReview ||
        lot.status == LotStatus.disputed).length;
    final completedCount = allLots.where((lot) => lot.status == LotStatus.completed).length;

    _uiState = _uiState.copyWith(
      recentSessions: allLots.take(5).toList(),
      syncStatus: SyncStatus(
        isOnline: isConnected,
        pendingRecords: 0,
        lastSyncedAt: isConnected ? "Live Connected" : "Offline — Last known state",
      ),
      workloadMetrics: WorkloadMetrics(
        activeLots: activeLots.length,
        reviewNeeded: reviewNeededCount,
        syncPending: completedCount,
      ),
      isLoading: false,
    );
    notifyListeners();
  }

  /// Pull-to-refresh for the home screen
  Future<void> refresh() => _refreshDashboard();

  @override
  void dispose() {
    _subscription?.cancel();
    ApiConfig.isConnectedNotifier.removeListener(_onConnectionChanged);
    super.dispose();
  }
}
