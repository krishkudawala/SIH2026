import 'package:flutter/foundation.dart';

// --- Assumed Imports (Replace with actual paths) ---
// import 'package:mandi_nyaay/domain/model/calibration_health.dart';
// import 'package:mandi_nyaay/domain/model/rule_pack.dart';
// import 'package:mandi_nyaay/data/fixture/fixture_config_repository.dart';

// Placeholder Enums & Models (remove when importing real ones)
enum CalibrationState { good, driftDetected, unknown }
extension CalibrationStateExt on CalibrationState {
  String get displayLabel {
    switch (this) {
      case CalibrationState.good: return "GOOD";
      case CalibrationState.driftDetected: return "DRIFT DETECTED";
      default: return "UNKNOWN";
    }
  }
}

class CalibrationHealth {
  final CalibrationState currentState;
  final String lastChecked;
  final String referenceMarkerUsed;
  CalibrationHealth(this.currentState, this.lastChecked, this.referenceMarkerUsed);
}

class RulePack {
  final String commodity;
  final String version;
  final String effectiveDate;
  RulePack(this.commodity, this.version, this.effectiveDate);
}

// --- State Data Class ---
class MoreUiState {
  final CalibrationHealth? calibration;
  final RulePack? rulePack;

  const MoreUiState({
    this.calibration,
    this.rulePack,
  });

  MoreUiState copyWith({
    CalibrationHealth? calibration,
    RulePack? rulePack,
  }) {
    return MoreUiState(
      calibration: calibration ?? this.calibration,
      rulePack: rulePack ?? this.rulePack,
    );
  }
}

// --- ViewModel ---
class MoreViewModel extends ChangeNotifier {
  // final FixtureConfigRepository _repository = FixtureConfigRepository();

  MoreUiState _uiState = const MoreUiState();
  MoreUiState get uiState => _uiState;

  MoreViewModel() {
    _loadConfig();
  }

  Future<void> _loadConfig() async {
    // Simulating the repository call
    // final cal = await _repository.getCalibrationHealth();
    // final rp = await _repository.getActivRulePack();

    // Mock data based on your Kotlin flow
    final cal = CalibrationHealth(CalibrationState.good, "2026-09-20 08:00 AM", "Standard Marker A");
    final rp = RulePack("Onions", "1.4.2", "2026-01-01");

    _uiState = _uiState.copyWith(calibration: cal, rulePack: rp);
    notifyListeners();
  }
}