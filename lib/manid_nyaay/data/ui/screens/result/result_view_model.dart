import 'package:flutter/foundation.dart';
import 'package:sih2631/manid_nyaay/data/api/api_client.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/fixture/lot_repository.dart';

class ResultUiState {
  final dynamic result;
  final Lot? lot;
  final bool isLoading;
  final String? errorMessage;

  const ResultUiState({
    this.result,
    this.lot,
    this.isLoading = true,
    this.errorMessage,
  });

  ResultUiState copyWith({
    dynamic result,
    Lot? lot,
    bool? isLoading,
    String? errorMessage,
  }) {
    return ResultUiState(
      result: result ?? this.result,
      lot: lot ?? this.lot,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}

class ResultViewModel extends ChangeNotifier {
  final String lotId;
  final MandiApiClient _api = MandiApiClient();
  final FixtureLotRepository _lotRepo = FixtureLotRepository();

  ResultUiState _uiState = const ResultUiState();
  ResultUiState get uiState => _uiState;

  ResultViewModel({required this.lotId}) {
    _init();
  }

  Future<void> _init() async {
    _uiState = _uiState.copyWith(isLoading: true);
    notifyListeners();

    try {
      final lot = await _lotRepo.getLotById(lotId);
      final sessions = await _api.listSessions(limit: 50);

      Map<String, dynamic>? targetSession;
      for (final s in sessions) {
        if (s is Map && (s['lot_id'] == lotId || s['id'] == lotId)) {
          targetSession = Map<String, dynamic>.from(s);
          break;
        }
      }

      if (targetSession != null) {
        final sessionId = targetSession['id']?.toString() ?? '';
        final sampling = await _api.getSampling(sessionId);
        final obs = await _api.getObservations(sessionId);

        final total = obs.length;
        if (total > 0) {
          final healthy = obs.where((o) => (o['condition'] ?? '').toString().toUpperCase() == 'HEALTHY').length;
          final damaged = obs.where((o) {
            final c = (o['condition'] ?? '').toString().toUpperCase();
            return c == 'DAMAGED' || c == 'SPROUTED';
          }).length;
          final rotten = obs.where((o) => (o['condition'] ?? '').toString().toUpperCase() == 'ROTTEN').length;

          final gA = healthy / total;
          final gUrs = damaged / total;
          final gRej = rotten / total;

          final realResult = (
            gradeAByWeight: gA,
            ursByWeight: gUrs,
            rejectByWeight: gRej,
            gradeAByCount: gA,
            countToWeightDivergencePp: 0.0,
            ci95Low: (sampling['wilson_intervals']?['HEALTHY']?['lower_ci'] as num?)?.toDouble() ?? (gA * 0.9),
            ci95High: (sampling['wilson_intervals']?['HEALTHY']?['upper_ci'] as num?)?.toDouble() ?? (gA * 1.1),
            sampleCount: total,
            isSufficient: sampling['status'] == 'STOP',
            rulePackVersion: targetSession['rule_pack_version']?.toString() ?? "1.0.0",
            wbFlagged: false,
            wbLabel: "Unvalidated Weighbridge Signal",
          );

          _uiState = _uiState.copyWith(
            result: realResult,
            lot: lot,
            isLoading: false,
          );
          notifyListeners();
          return;
        }
      }

      // No observations yet for this lot
      _uiState = _uiState.copyWith(
        result: null,
        lot: lot,
        isLoading: false,
      );
    } catch (e) {
      _uiState = _uiState.copyWith(
        result: null,
        isLoading: false,
        errorMessage: "Unable to load inspection results: $e",
      );
    }
    notifyListeners();
  }
}