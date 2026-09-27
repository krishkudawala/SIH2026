// Enhanced Enum in Dart
enum WeighbridgeCheck {
  withinExpectedRange("Within Expected Range", false),
  reviewSignal("Review Signal", true);

  final String displayLabel;
  final bool isFlagged;

  const WeighbridgeCheck(this.displayLabel, this.isFlagged);

  // Kotlin's companion object constant becomes a static const here
  static const String reviewSignalDisclaimer =
      "This is a review signal, not proof of fraud.";
}

class GradingResult {
  final String id;
  final String lotId;
  final String sessionId;
  final double gradeAByWeight;           // 0.0 – 1.0
  final double ursByWeight;
  final double rejectByWeight;
  final double gradeAByCount;            // 0.0 – 1.0 for comparison
  final double countToWeightDivergencePp;  // percentage-point difference
  final double ci95Low;
  final double ci95High;
  final int sampleCount;
  final WeighbridgeCheck weighbridgeCheck;
  final String rulePackVersion;
  final bool isSufficient;

  const GradingResult({
    required this.id,
    required this.lotId,
    required this.sessionId,
    required this.gradeAByWeight,
    required this.ursByWeight,
    required this.rejectByWeight,
    required this.gradeAByCount,
    required this.countToWeightDivergencePp,
    required this.ci95Low,
    required this.ci95High,
    required this.sampleCount,
    required this.weighbridgeCheck,
    required this.rulePackVersion,
    required this.isSufficient,
  });

  GradingResult copyWith({
    String? id,
    String? lotId,
    String? sessionId,
    double? gradeAByWeight,
    double? ursByWeight,
    double? rejectByWeight,
    double? gradeAByCount,
    double? countToWeightDivergencePp,
    double? ci95Low,
    double? ci95High,
    int? sampleCount,
    WeighbridgeCheck? weighbridgeCheck,
    String? rulePackVersion,
    bool? isSufficient,
  }) {
    return GradingResult(
      id: id ?? this.id,
      lotId: lotId ?? this.lotId,
      sessionId: sessionId ?? this.sessionId,
      gradeAByWeight: gradeAByWeight ?? this.gradeAByWeight,
      ursByWeight: ursByWeight ?? this.ursByWeight,
      rejectByWeight: rejectByWeight ?? this.rejectByWeight,
      gradeAByCount: gradeAByCount ?? this.gradeAByCount,
      countToWeightDivergencePp: countToWeightDivergencePp ?? this.countToWeightDivergencePp,
      ci95Low: ci95Low ?? this.ci95Low,
      ci95High: ci95High ?? this.ci95High,
      sampleCount: sampleCount ?? this.sampleCount,
      weighbridgeCheck: weighbridgeCheck ?? this.weighbridgeCheck,
      rulePackVersion: rulePackVersion ?? this.rulePackVersion,
      isSufficient: isSufficient ?? this.isSufficient,
    );
  }
}