import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class ApiConfig {
  static const String _defaultUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );

  static String _baseUrl = _defaultUrl;
  static final ValueNotifier<String> baseUrlNotifier = ValueNotifier<String>(_defaultUrl);
  static final ValueNotifier<bool> isConnectedNotifier = ValueNotifier<bool>(false);
  static final ValueNotifier<String?> lastErrorNotifier = ValueNotifier<String?>(null);

  static Timer? _healthTimer;

  static String get baseUrl => _baseUrl;

  static void setBaseUrl(String url) {
    String cleaned = url.trim();
    if (cleaned.endsWith('/')) {
      cleaned = cleaned.substring(0, cleaned.length - 1);
    }
    _baseUrl = cleaned;
    baseUrlNotifier.value = cleaned;
    checkConnection();
  }

  /// Starts a background health-poll every [intervalSeconds] seconds.
  /// Safe to call multiple times — only one timer is active at a time.
  static void startPeriodicHealthCheck({int intervalSeconds = 15}) {
    _healthTimer?.cancel();
    // Immediate first check
    checkConnection();
    _healthTimer = Timer.periodic(
      Duration(seconds: intervalSeconds),
      (_) => checkConnection(),
    );
  }

  static void stopPeriodicHealthCheck() {
    _healthTimer?.cancel();
    _healthTimer = null;
  }

  static Future<bool> checkConnection() async {
    try {
      final uri = Uri.parse('$_baseUrl/health');
      final res = await http.get(uri).timeout(const Duration(seconds: 4));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        if (data['status'] == 'HEALTHY') {
          isConnectedNotifier.value = true;
          lastErrorNotifier.value = null;
          return true;
        }
      }
      isConnectedNotifier.value = false;
      lastErrorNotifier.value = 'Server responded with status ${res.statusCode}';
      return false;
    } catch (e) {
      isConnectedNotifier.value = false;
      lastErrorNotifier.value = e.toString();
      return false;
    }
  }
}
