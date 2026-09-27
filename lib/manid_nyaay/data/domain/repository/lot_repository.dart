import 'dart:async';

import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/work_load_metrics.dart';



abstract class LotRepository {

  Stream<List<Lot>> observeAllLots();

  Stream<List<Lot>> observeActiveLots();

  Future<Lot?> getLotById(String id);

  Future<void> createLot(Lot lot);

  Future<void> updateLotStatus(String id, LotStatus status);

  Future<void> updateSamplingPlan(String id, SamplingPlan plan);

  Future<WorkloadMetrics> getWorkloadMetrics();
}