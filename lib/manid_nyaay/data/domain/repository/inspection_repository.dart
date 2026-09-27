import 'dart:async';

import 'package:sih2631/manid_nyaay/data/domain/model/grading_result.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/inspection_session.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/onion_record.dart';



abstract class InspectionRepository {

  Future<String> createSession(InspectionSession session);

  Future<InspectionSession?> getSession(String id);

  Future<void> updateSessionState(String id, InspectionState state);

  Future<void> addBagSelection(String sessionId, BagSelection selection);

  Future<void> addBatchCapture(BatchCapture capture);

  Future<void> addInspectionEvent(InspectionEvent event);

  Future<List<OnionRecord>> getOnionRecords(String sessionId);

  Future<void> saveOnionRecord(OnionRecord record);

  Future<GradingResult?> getGradingResult(String lotId);

  Future<void> saveGradingResult(GradingResult result);

  Stream<GradingResult?> observeGradingResult(String lotId);
}