import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:sih2631/manid_nyaay/data/api/api_config.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;

  ApiException(this.statusCode, this.message);

  @override
  String toString() => 'ApiException (HTTP $statusCode): $message';
}

class MandiApiClient {
  static final MandiApiClient _instance = MandiApiClient._internal();
  factory MandiApiClient() => _instance;
  MandiApiClient._internal();

  String get _base => ApiConfig.baseUrl;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };

  Future<dynamic> _handleResponse(http.Response res) async {
    if (res.statusCode >= 200 && res.statusCode < 300) {
      if (res.body.isEmpty) return {};
      return jsonDecode(utf8.decode(res.bodyBytes));
    } else {
      String errMsg = 'Request failed with status ${res.statusCode}';
      try {
        final errJson = jsonDecode(utf8.decode(res.bodyBytes));
        if (errJson is Map && errJson.containsKey('detail')) {
          errMsg = errJson['detail'].toString();
        }
      } catch (_) {}
      throw ApiException(res.statusCode, errMsg);
    }
  }

  // System Health
  Future<Map<String, dynamic>> checkHealth() async {
    final uri = Uri.parse('$_base/health');
    final res = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 5));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // 1. POST /sessions
  Future<Map<String, dynamic>> createSession({
    required String lotId,
    String sourceReference = 'BAG_INSPECTOR_SELECTED',
    int targetSampleSize = 20,
    String rulePackId = 'AGMARK_ONION_2024_V1',
    int? declaredBagCount,
    double? certifiedLotWeightKg,
  }) async {
    final uri = Uri.parse('$_base/sessions');
    final body = jsonEncode({
      'lot_id': lotId,
      'source_reference': sourceReference,
      'target_sample_size': targetSampleSize,
      'rule_pack_id': rulePackId,
      if (declaredBagCount != null) 'declared_bag_count': declaredBagCount,
      if (certifiedLotWeightKg != null) 'certified_lot_weight_kg': certifiedLotWeightKg,
    });
    final res = await http.post(uri, headers: _headers, body: body).timeout(const Duration(seconds: 10));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // GET /sessions
  Future<List<dynamic>> listSessions({int limit = 50}) async {
    final uri = Uri.parse('$_base/sessions?limit=$limit');
    final res = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));
    return List<dynamic>.from(await _handleResponse(res));
  }

  // GET /sessions/{id}
  Future<Map<String, dynamic>> getSession(String sessionId) async {
    final uri = Uri.parse('$_base/sessions/$sessionId');
    final res = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // 2. POST /sessions/{id}/captures
  Future<Map<String, dynamic>> addCapture(
    String sessionId, {
    String? imagePath,
    String? imageBase64,
    String? filename,
    String captureRole = 'PRIMARY_SAMPLE_CAPTURE',
    String viewAngle = 'TOP',
    String? targetSampleUnitId,
    String? targetCellId,
  }) async {
    final uri = Uri.parse('$_base/sessions/$sessionId/captures');
    final body = jsonEncode({
      if (imagePath != null) 'image_path': imagePath,
      if (imageBase64 != null) 'image_base64': imageBase64,
      if (filename != null) 'filename': filename,
      'capture_role': captureRole,
      'view_angle': viewAngle,
      if (targetSampleUnitId != null) 'target_sample_unit_id': targetSampleUnitId,
      if (targetCellId != null) 'target_cell_id': targetCellId,
    });
    final res = await http.post(uri, headers: _headers, body: body).timeout(const Duration(seconds: 30));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // GET /sessions/{id}/captures
  Future<List<dynamic>> getCaptures(String sessionId) async {
    final uri = Uri.parse('$_base/sessions/$sessionId/captures');
    final res = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));
    return List<dynamic>.from(await _handleResponse(res));
  }

  // 3. POST /sessions/{id}/inference
  Future<Map<String, dynamic>> runInference(
    String sessionId, {
    String? captureId,
  }) async {
    final uri = Uri.parse('$_base/sessions/$sessionId/inference');
    final body = jsonEncode({
      if (captureId != null) 'capture_id': captureId,
    });
    final res = await http.post(uri, headers: _headers, body: body).timeout(const Duration(seconds: 30));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // 4. GET /sessions/{id}/observations
  Future<List<dynamic>> getObservations(String sessionId) async {
    final uri = Uri.parse('$_base/sessions/$sessionId/observations');
    final res = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));
    return List<dynamic>.from(await _handleResponse(res));
  }

  // 5. GET /sessions/{id}/sample-units
  Future<List<dynamic>> getSampleUnits(String sessionId) async {
    final uri = Uri.parse('$_base/sessions/$sessionId/sample-units');
    final res = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));
    return List<dynamic>.from(await _handleResponse(res));
  }

  // 6. GET /sessions/{id}/sampling
  Future<Map<String, dynamic>> getSampling(String sessionId) async {
    final uri = Uri.parse('$_base/sessions/$sessionId/sampling');
    final res = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // 7. GET /sessions/{id}/measurement
  Future<Map<String, dynamic>> getMeasurement(String sessionId) async {
    final uri = Uri.parse('$_base/sessions/$sessionId/measurement');
    final res = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // 8. GET /sessions/{id}/weight
  Future<Map<String, dynamic>> getWeight(String sessionId) async {
    final uri = Uri.parse('$_base/sessions/$sessionId/weight');
    final res = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // 9. GET /sessions/{id}/review
  Future<Map<String, dynamic>> getReview(String sessionId) async {
    final uri = Uri.parse('$_base/sessions/$sessionId/review');
    final res = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // 10. POST /sessions/{id}/decision
  Future<Map<String, dynamic>> evaluateDecision(
    String sessionId, {
    String? rulePackId,
    String? overrideGrade,
    String? overrideReason,
  }) async {
    final uri = Uri.parse('$_base/sessions/$sessionId/decision');
    final body = jsonEncode({
      if (rulePackId != null) 'rule_pack_id': rulePackId,
      if (overrideGrade != null) 'override_grade': overrideGrade,
      if (overrideReason != null) 'override_reason': overrideReason,
    });
    final res = await http.post(uri, headers: _headers, body: body).timeout(const Duration(seconds: 15));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // 11. POST /sessions/{id}/dispute
  Future<Map<String, dynamic>> openDispute(
    String sessionId, {
    required String disputeReason,
    String openedBy = 'LOT_OWNER',
  }) async {
    final uri = Uri.parse('$_base/sessions/$sessionId/dispute');
    final body = jsonEncode({
      'dispute_reason': disputeReason,
      'opened_by': openedBy,
    });
    final res = await http.post(uri, headers: _headers, body: body).timeout(const Duration(seconds: 15));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // GET /sessions/{id}/dispute
  Future<Map<String, dynamic>?> getDispute(String sessionId) async {
    try {
      final uri = Uri.parse('$_base/sessions/$sessionId/dispute');
      final res = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));
      return Map<String, dynamic>.from(await _handleResponse(res));
    } catch (_) {
      return null;
    }
  }

  // POST /sessions/{id}/dispute/resolve
  Future<Map<String, dynamic>> resolveDispute(
    String sessionId, {
    required String finalGrade,
    required String arbitratorId,
    required String arbitrationNotes,
  }) async {
    final uri = Uri.parse('$_base/sessions/$sessionId/dispute/resolve');
    final body = jsonEncode({
      'final_grade': finalGrade,
      'arbitrator_id': arbitratorId,
      'arbitration_notes': arbitrationNotes,
    });
    final res = await http.post(uri, headers: _headers, body: body).timeout(const Duration(seconds: 15));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // 12. GET /sessions/{id}/evidence
  Future<Map<String, dynamic>> getEvidence(String sessionId) async {
    final uri = Uri.parse('$_base/sessions/$sessionId/evidence');
    final res = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 10));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // 13. POST /sessions/{id}/replay
  Future<Map<String, dynamic>> replaySession(String sessionId) async {
    final uri = Uri.parse('$_base/sessions/$sessionId/replay');
    final res = await http.post(uri, headers: _headers).timeout(const Duration(seconds: 30));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // 14. GET /sessions/{id}/report
  Future<Map<String, dynamic>> getReport(String sessionId) async {
    final uri = Uri.parse('$_base/sessions/$sessionId/report');
    final res = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 15));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // OCR
  Future<Map<String, dynamic>> scanOcr(String imagePath) async {
    final uri = Uri.parse('$_base/ocr/scan');
    final body = jsonEncode({'image_path': imagePath});
    final res = await http.post(uri, headers: _headers, body: body).timeout(const Duration(seconds: 15));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  // Calibration
  Future<Map<String, dynamic>> recordCalibrationSample({
    required String sampleUnitId,
    required String lotId,
    required double lengthMm,
    required double widthMm,
    required double thicknessMm,
    required double actualScaleWeightG,
    String condition = 'HEALTHY',
    double defectFraction = 0.0,
    String variety = 'Nashik Red',
    String operatorId = 'APMC-INS-01',
  }) async {
    final uri = Uri.parse('$_base/calibration/samples');
    final body = jsonEncode({
      'sample_unit_id': sampleUnitId,
      'lot_id': lotId,
      'length_mm': lengthMm,
      'width_mm': widthMm,
      'thickness_mm': thicknessMm,
      'actual_scale_weight_g': actualScaleWeightG,
      'condition': condition,
      'defect_fraction': defectFraction,
      'variety': variety,
      'operator_id': operatorId,
    });
    final res = await http.post(uri, headers: _headers, body: body).timeout(const Duration(seconds: 15));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }

  Future<List<dynamic>> listCalibrationSamples() async {
    final uri = Uri.parse('$_base/calibration/samples');
    final res = await http.get(uri, headers: _headers).timeout(const Duration(seconds: 15));
    return List<dynamic>.from(await _handleResponse(res));
  }

  Future<Map<String, dynamic>> trainWeightModel({
    double coverageTarget = 0.90,
    String modelVersion = 'conformal_ridge_v1',
  }) async {
    final uri = Uri.parse('$_base/calibration/train-weight-model');
    final body = jsonEncode({
      'coverage_target': coverageTarget,
      'model_version': modelVersion,
    });
    final res = await http.post(uri, headers: _headers, body: body).timeout(const Duration(seconds: 30));
    return Map<String, dynamic>.from(await _handleResponse(res));
  }
}
