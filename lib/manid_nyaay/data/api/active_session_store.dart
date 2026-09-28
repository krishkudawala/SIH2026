import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

/// Manages and persists the single authoritative active inspection session.
class ActiveSessionStore {
  static final ActiveSessionStore _instance = ActiveSessionStore._internal();
  factory ActiveSessionStore() => _instance;
  ActiveSessionStore._internal();

  String? _sessionId;
  String? _lotId;
  String? _sourceReference;
  DateTime? _createdAt;
  String? _inspectionStatus;
  int _targetSampleSize = 20;
  int? _declaredBagCount;
  double? _certifiedLotWeightKg;

  final ValueNotifier<String?> activeSessionNotifier = ValueNotifier<String?>(null);

  String? get sessionId => _sessionId;
  String? get lotId => _lotId;
  String? get sourceReference => _sourceReference;
  DateTime? get createdAt => _createdAt;
  String? get inspectionStatus => _inspectionStatus;
  int get targetSampleSize => _targetSampleSize;
  int? get declaredBagCount => _declaredBagCount;
  double? get certifiedLotWeightKg => _certifiedLotWeightKg;

  bool get hasActiveSession => _sessionId != null && _sessionId!.isNotEmpty;

  void setActiveSession({
    required String sessionId,
    required String lotId,
    required String sourceReference,
    required DateTime createdAt,
    required String inspectionStatus,
    int targetSampleSize = 20,
    int? declaredBagCount,
    double? certifiedLotWeightKg,
  }) {
    _sessionId = sessionId;
    _lotId = lotId;
    _sourceReference = sourceReference;
    _createdAt = createdAt;
    _inspectionStatus = inspectionStatus;
    _targetSampleSize = targetSampleSize;
    _declaredBagCount = declaredBagCount;
    _certifiedLotWeightKg = certifiedLotWeightKg;

    activeSessionNotifier.value = sessionId;
    _saveToDisk();
  }

  void updateStatus(String newStatus) {
    _inspectionStatus = newStatus;
    _saveToDisk();
  }

  void clear() {
    _sessionId = null;
    _lotId = null;
    _sourceReference = null;
    _createdAt = null;
    _inspectionStatus = null;
    activeSessionNotifier.value = null;
    _deleteDiskFile();
  }

  Future<void> _saveToDisk() async {
    if (kIsWeb) return;
    try {
      final dir = await getApplicationDocumentsDirectory();
      final file = File('${dir.path}/mandi_active_session.json');
      final data = {
        'sessionId': _sessionId,
        'lotId': _lotId,
        'sourceReference': _sourceReference,
        'createdAt': _createdAt?.toIso8601String(),
        'inspectionStatus': _inspectionStatus,
        'targetSampleSize': _targetSampleSize,
        'declaredBagCount': _declaredBagCount,
        'certifiedLotWeightKg': _certifiedLotWeightKg,
      };
      await file.writeAsString(jsonEncode(data));
    } catch (_) {}
  }

  Future<void> loadFromDisk() async {
    if (kIsWeb) return;
    try {
      final dir = await getApplicationDocumentsDirectory();
      final file = File('${dir.path}/mandi_active_session.json');
      if (await file.exists()) {
        final content = await file.readAsString();
        final map = jsonDecode(content);
        _sessionId = map['sessionId'];
        _lotId = map['lotId'];
        _sourceReference = map['sourceReference'];
        _createdAt = map['createdAt'] != null ? DateTime.tryParse(map['createdAt']) : null;
        _inspectionStatus = map['inspectionStatus'];
        _targetSampleSize = (map['targetSampleSize'] as num?)?.toInt() ?? 20;
        _declaredBagCount = (map['declaredBagCount'] as num?)?.toInt();
        _certifiedLotWeightKg = (map['certifiedLotWeightKg'] as num?)?.toDouble();
        activeSessionNotifier.value = _sessionId;
      }
    } catch (_) {}
  }

  Future<void> _deleteDiskFile() async {
    if (kIsWeb) return;
    try {
      final dir = await getApplicationDocumentsDirectory();
      final file = File('${dir.path}/mandi_active_session.json');
      if (await file.exists()) {
        await file.delete();
      }
    } catch (_) {}
  }
}
