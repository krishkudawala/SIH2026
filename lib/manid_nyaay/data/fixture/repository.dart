// Converted from Kotlin: com.mandiNyaay.data.fixture (repository fixtures)

import 'package:rxdart/rxdart.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/farmer.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/grading_result.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/inspection_session.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/onion_record.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/work_load_metrics.dart';
import 'package:sih2631/manid_nyaay/data/fixture/fixture_data.dart';
import 'package:sih2631/manid_nyaay/data/domain/repository/inspection_repository.dart';
import 'package:sih2631/manid_nyaay/data/domain/repository/sync_repository.dart';

// ---------------------------------------------------------------------------
// Fixture implementations
// ---------------------------------------------------------------------------

class FixtureInspectionRepository implements InspectionRepository {
  final Map<String, InspectionSession> _sessions = {};
  final Map<String, List<OnionRecord>> _onionRecords = {};
  final BehaviorSubject<GradingResult?> _gradingResults =
  BehaviorSubject<GradingResult?>.seeded(FixtureData.sampleGradingResult);

  @override
  Future<String> createSession(InspectionSession session) async {
    _sessions[session.id] = session;
    return session.id;
  }

  @override
  Future<InspectionSession?> getSession(String id) async => _sessions[id];

  @override
  Future<void> updateSessionState(String id, InspectionState state) async {
    final session = _sessions[id];
    if (session != null) {
      _sessions[id] = session.copyWith(currentState: state);
    }
  }

  @override
  Future<void> addBagSelection(String sessionId, BagSelection selection) async {
    final session = _sessions[sessionId];
    if (session != null) {
      _sessions[sessionId] = session.copyWith(
        selectedBags: [...session.selectedBags, selection],
      );
    }
  }

  @override
  Future<void> addBatchCapture(BatchCapture capture) async {
    final session = _sessions[capture.sessionId];
    if (session != null) {
      _sessions[capture.sessionId] = session.copyWith(
        batchCaptures: [...session.batchCaptures, capture],
      );
    }
  }

  @override
  Future<void> addInspectionEvent(InspectionEvent event) async {
    final session = _sessions[event.sessionId];
    if (session != null) {
      _sessions[event.sessionId] = session.copyWith(
        events: [...session.events, event],
      );
    }
  }

  @override
  Future<List<OnionRecord>> getOnionRecords(String sessionId) async =>
      _onionRecords[sessionId] ?? FixtureData.sampleOnionRecords;

  @override
  Future<void> saveOnionRecord(OnionRecord record) async {
    _onionRecords.putIfAbsent(record.sessionId, () => []).add(record);
  }

  @override
  Future<GradingResult?> getGradingResult(String lotId) async =>
      lotId == FixtureData.sampleGradingResult.lotId ? FixtureData.sampleGradingResult : null;

  @override
  Future<void> saveGradingResult(GradingResult result) async {
    _gradingResults.add(result);
  }

  @override
  Stream<GradingResult?> observeGradingResult(String lotId) => _gradingResults.stream;
}

class FixtureSyncRepository implements SyncRepository {
  final BehaviorSubject<SyncStatus> _status =
  BehaviorSubject<SyncStatus>.seeded(FixtureData.syncStatus);

  @override
  Stream<SyncStatus> observeSyncStatus() => _status.stream;

  @override
  Future<void> triggerSync() async {
    _status.add(_status.value.copyWith(pendingRecords: 0));
  }

  @override
  Future<int> getPendingRecordCount() async => _status.value.pendingRecords;
}

class FixtureFarmerRepository implements FarmerRepository {
  @override
  Future<Farmer?> getFarmerById(String id) async {
    for (final farmer in FixtureData.farmers) {
      if (farmer.id == id) return farmer;
    }
    return null;
  }

  @override
  Future<List<Farmer>> getAllFarmers() async => FixtureData.farmers;
}

class FixtureReviewRepository implements ReviewRepository {
  final BehaviorSubject<List<ReviewItem>> _items =
  BehaviorSubject<List<ReviewItem>>.seeded(FixtureData.reviewItems);

  @override
  Stream<List<ReviewItem>> observeReviewItems() => _items.stream;

  @override
  Future<void> acceptReview(String sampleId) async {
    _items.add([
      for (final item in _items.value)
        if (item.sampleId == sampleId) item.copyWith(status: ReviewStatus.accepted) else item,
    ]);
  }

  @override
  Future<void> overrideReview(String sampleId, Grade grade, String reason) async {
    _items.add([
      for (final item in _items.value)
        if (item.sampleId == sampleId)
          item.copyWith(status: ReviewStatus.overridden, tentativeGrade: grade)
        else
          item,
    ]);
  }

  @override
  Future<void> requestRecapture(String sampleId) async {
    _items.add([
      for (final item in _items.value)
        if (item.sampleId == sampleId)
          item.copyWith(status: ReviewStatus.recaptureRequested)
        else
          item,
    ]);
  }
}

class FixtureConfigRepository implements ConfigRepository {
  @override
  Future<RulePack> getActivRulePack() async => FixtureData.activeRulePack;

  @override
  Future<CalibrationHealth> getCalibrationHealth() async => FixtureData.calibrationHealth;
}
