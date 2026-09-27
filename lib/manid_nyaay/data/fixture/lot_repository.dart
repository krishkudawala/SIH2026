// Converted from Kotlin: com.mandiNyaay.data.fixture.FixtureLotRepository
//
// Same StateFlow -> BehaviorSubject translation as repositories.dart.
// Requires rxdart (see repositories.dart for the pubspec.yaml note).

import 'package:rxdart/rxdart.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/work_load_metrics.dart';
import 'package:sih2631/manid_nyaay/data/fixture/fixture_data.dart';
import 'package:sih2631/manid_nyaay/data/domain/repository/lot_repository.dart';

class FixtureLotRepository implements LotRepository {
  final BehaviorSubject<List<Lot>> _lots =
  BehaviorSubject<List<Lot>>.seeded(FixtureData.lots);

  @override
  Stream<List<Lot>> observeAllLots() => _lots.stream;

  @override
  Stream<List<Lot>> observeActiveLots() =>
      _lots.stream.map((list) => list.where((lot) => lot.status == LotStatus.active).toList());

  Future<List<Lot>> getAllLots() async => _lots.value;

  @override
  Future<Lot?> getLotById(String id) async {
    for (final lot in _lots.value) {
      if (lot.id == id) return lot;
    }
    return null;
  }

  @override
  Future<void> createLot(Lot lot) async {
    _lots.add([..._lots.value, lot]);
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
      syncPending: 1,
    );
  }
}