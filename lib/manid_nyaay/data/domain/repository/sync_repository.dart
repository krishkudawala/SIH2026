import 'dart:async';

import 'package:sih2631/manid_nyaay/data/domain/model/farmer.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/onion_record.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/work_load_metrics.dart';



abstract class SyncRepository {
  Stream<SyncStatus> observeSyncStatus();

  Future<void> triggerSync();

  Future<int> getPendingRecordCount();
}


abstract class FarmerRepository {
  Future<Farmer?> getFarmerById(String id);

  Future<List<Farmer>> getAllFarmers();
}


abstract class ReviewRepository {
  Stream<List<ReviewItem>> observeReviewItems();

  Future<void> acceptReview(String sampleId);

  Future<void> overrideReview(String sampleId, Grade grade, String reason);

  Future<void> requestRecapture(String sampleId);
}


abstract class ConfigRepository {
  Future<RulePack> getActivRulePack();

  Future<CalibrationHealth> getCalibrationHealth();
}