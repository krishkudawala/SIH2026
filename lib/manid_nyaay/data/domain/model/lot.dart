// --- Enums ---

enum LotStatus {
  active("In Progress"),
  completed("Completed"),
  needsReview("Needs Review"),
  disputed("Disputed");

  final String displayLabel;
  const LotStatus(this.displayLabel);
}

// --- Data Classes ---

class SamplingPlan {
  final int totalSamplesRequired;
  final int completedSamples;

  const SamplingPlan({
    required this.totalSamplesRequired,
    required this.completedSamples,
  });

  // Kotlin's computed 'get()' properties become Dart getters
  double get progressFraction {
    if (totalSamplesRequired == 0) return 0.0;
    return completedSamples / totalSamplesRequired;
  }

  bool get isSufficient => completedSamples >= totalSamplesRequired;

  SamplingPlan copyWith({
    int? totalSamplesRequired,
    int? completedSamples,
  }) {
    return SamplingPlan(
      totalSamplesRequired: totalSamplesRequired ?? this.totalSamplesRequired,
      completedSamples: completedSamples ?? this.completedSamples,
    );
  }
}

class Lot {
  final String id;
  final String farmerId;
  final String farmerName;
  final String village;
  final int bagCount;
  final double certifiedWeightKg;
  final String weighbridgeRef;
  final String variety;
  final String location;
  final DateTime date; // Replaces java.time.LocalDate
  final LotStatus status;
  final SamplingPlan? samplingPlan;

  const Lot({
    required this.id,
    required this.farmerId,
    required this.farmerName,
    required this.village,
    required this.bagCount,
    required this.certifiedWeightKg,
    required this.weighbridgeRef,
    required this.variety,
    required this.location,
    required this.date,
    required this.status,
    this.samplingPlan,
  });

  Lot copyWith({
    String? id,
    String? farmerId,
    String? farmerName,
    String? village,
    int? bagCount,
    double? certifiedWeightKg,
    String? weighbridgeRef,
    String? variety,
    String? location,
    DateTime? date,
    LotStatus? status,
    SamplingPlan? samplingPlan,
  }) {
    return Lot(
      id: id ?? this.id,
      farmerId: farmerId ?? this.farmerId,
      farmerName: farmerName ?? this.farmerName,
      village: village ?? this.village,
      bagCount: bagCount ?? this.bagCount,
      certifiedWeightKg: certifiedWeightKg ?? this.certifiedWeightKg,
      weighbridgeRef: weighbridgeRef ?? this.weighbridgeRef,
      variety: variety ?? this.variety,
      location: location ?? this.location,
      date: date ?? this.date,
      status: status ?? this.status,
      // Note: passing null to a copyWith for nullable fields usually requires a special
      // wrapper or checking logic if you want to explicitly nullify a field.
      // Here, it falls back to the existing value if no new one is provided.
      samplingPlan: samplingPlan ?? this.samplingPlan,
    );
  }
}