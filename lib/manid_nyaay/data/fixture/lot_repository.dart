import 'dart:convert';
import 'package:rxdart/rxdart.dart';
import 'package:sih2631/manid_nyaay/data/api/api_client.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/work_load_metrics.dart';
import 'package:sih2631/manid_nyaay/data/domain/repository/lot_repository.dart';

class FixtureLotRepository implements LotRepository {
  static final FixtureLotRepository _instance = FixtureLotRepository._internal();
  factory FixtureLotRepository() => _instance;
  FixtureLotRepository._internal() {
    refreshLots();
  }

  final MandiApiClient _api = MandiApiClient();
  final BehaviorSubject<List<Lot>> _lots = BehaviorSubject<List<Lot>>.seeded(const []);

  @override
  Stream<List<Lot>> observeAllLots() {
    refreshLots();
    return _lots.stream;
  }

  @override
  Stream<List<Lot>> observeActiveLots() {
    refreshLots();
    return _lots.stream.map(
      (list) => list.where((lot) => lot.status == LotStatus.active).toList(),
    );
  }

  Future<List<Lot>> getAllLots() async {
    await refreshLots();
    return _lots.value;
  }

  Future<void> refreshLots() async {
    try {
      final sessions = await _api.listSessions(limit: 50);
      final mapped = <Lot>[];
      for (final s in sessions) {
        if (s is! Map) continue;
        final map = Map<String, dynamic>.from(s);

        int bagCount = 50;
        double certWeight = 1000.0;
        try {
          if (map['data_json'] != null) {
            final dj = jsonDecode(map['data_json'].toString());
            if (dj is Map) {
              if (dj['declared_bag_count'] != null) {
                bagCount = (dj['declared_bag_count'] as num).toInt();
              }
              if (dj['certified_lot_weight_kg'] != null) {
                certWeight = (dj['certified_lot_weight_kg'] as num).toDouble();
              }
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

        final lotId = map['lot_id']?.toString() ?? map['id']?.toString() ?? 'LOT-UNKNOWN';
        final targetSamples = (map['target_sample_size'] as num?)?.toInt() ?? 20;

        mapped.add(Lot(
          id: lotId,
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
            totalSamplesRequired: targetSamples,
            completedSamples: st == LotStatus.completed ? targetSamples : 0,
          ),
        ));
      }

      _lots.add(mapped);
    } catch (_) {
      // Backend not yet reachable or empty — keep current list without inventing mocks
    }
  }

  @override
  Future<Lot?> getLotById(String id) async {
    for (final lot in _lots.value) {
      if (lot.id == id) return lot;
    }
    // Attempt live fetch if not in local cache
    await refreshLots();
    for (final lot in _lots.value) {
      if (lot.id == id) return lot;
    }
    return null;
  }

  @override
  Future<void> createLot(Lot lot) async {
    try {
      await _api.createSession(
        lotId: lot.id,
        sourceReference: lot.farmerName,
        targetSampleSize: lot.samplingPlan?.totalSamplesRequired ?? 20,
        declaredBagCount: lot.bagCount,
        certifiedLotWeightKg: lot.certifiedWeightKg,
      );
    } catch (_) {}

    // Add locally to immediate stream
    final current = List<Lot>.from(_lots.value);
    current.removeWhere((l) => l.id == lot.id);
    current.insert(0, lot);
    _lots.add(current);

    await refreshLots();
  }

  @override
  Future<void> updateLotStatus(String id, LotStatus status) async {
    _lots.add([
      for (final lot in _lots.value)
        if (lot.id == id) lot.copyWith(status: status) else lot,
    ]);
  }

  @override
  Future<void> updateSamplingPlan(String id, SamplingPlan plan) async {
    _lots.add([
      for (final lot in _lots.value)
        if (lot.id == id) lot.copyWith(samplingPlan: plan) else lot,
    ]);
  }

  @override
  Future<WorkloadMetrics> getWorkloadMetrics() async {
    final all = _lots.value;
    return WorkloadMetrics(
      activeLots: all.where((lot) => lot.status == LotStatus.active).length,
      reviewNeeded: all
          .where((lot) => lot.status == LotStatus.needsReview || lot.status == LotStatus.disputed)
          .length,
      syncPending: 0,
    );
  }
}