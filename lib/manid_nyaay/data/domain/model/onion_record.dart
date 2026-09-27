// --- Enums ---

enum CorrespondenceStatus {
  confirmed,
  uncertain,
}

enum Grade {
  gradeA("Grade A"),
  urs("URS"),
  reject("Reject");

  final String displayLabel;
  const Grade(this.displayLabel);

  // Companion object factory function mapped to a static method
  static Grade fromRulePack(String code) {
    switch (code.toUpperCase()) {
      case "GRADE_A":
      case "A":
        return Grade.gradeA;
      case "REJECT":
      case "C":
        return Grade.reject;
      case "URS":
      default:
        return Grade.urs;
    }
  }
}

enum DefectType {
  bruising("Bruising"),
  rot("Rot"),
  sprouting("Sprouting"),
  doubleBulb("Double Bulb"),
  mechanicalDamage("Mechanical Damage"),
  skinPeeling("Skin Peeling"),
  none("None");

  final String displayLabel;
  const DefectType(this.displayLabel);
}

// --- Data Classes ---

class Defect {
  // Companion object constant becomes a static const
  static const String externalOnlyStatement =
      "Externally visible condition only. Internal quality is not observed by an RGB camera.";

  final DefectType type;
  final String? evidenceCaptureId;
  final String ruleVersion;
  final String limitationStatement;

  const Defect({
    required this.type,
    this.evidenceCaptureId,
    required this.ruleVersion,
    this.limitationStatement = externalOnlyStatement,
  });

  Defect copyWith({
    DefectType? type,
    String? evidenceCaptureId,
    String? ruleVersion,
    String? limitationStatement,
  }) {
    return Defect(
      type: type ?? this.type,
      evidenceCaptureId: evidenceCaptureId ?? this.evidenceCaptureId,
      ruleVersion: ruleVersion ?? this.ruleVersion,
      limitationStatement: limitationStatement ?? this.limitationStatement,
    );
  }
}

class OnionRecord {
  final String id;
  final String sessionId;
  final List<String> batchCaptureIds;
  final double diameterMm;
  final double estimatedWeightGrams;
  final Grade grade;
  final List<Defect> defects;
  final CorrespondenceStatus correspondenceStatus;

  const OnionRecord({
    required this.id,
    required this.sessionId,
    required this.batchCaptureIds,
    required this.diameterMm,
    required this.estimatedWeightGrams,
    required this.grade,
    required this.defects,
    this.correspondenceStatus = CorrespondenceStatus.confirmed, // Default mapped here
  });

  OnionRecord copyWith({
    String? id,
    String? sessionId,
    List<String>? batchCaptureIds,
    double? diameterMm,
    double? estimatedWeightGrams,
    Grade? grade,
    List<Defect>? defects,
    CorrespondenceStatus? correspondenceStatus,
  }) {
    return OnionRecord(
      id: id ?? this.id,
      sessionId: sessionId ?? this.sessionId,
      batchCaptureIds: batchCaptureIds ?? this.batchCaptureIds,
      diameterMm: diameterMm ?? this.diameterMm,
      estimatedWeightGrams: estimatedWeightGrams ?? this.estimatedWeightGrams,
      grade: grade ?? this.grade,
      defects: defects ?? this.defects,
      correspondenceStatus: correspondenceStatus ?? this.correspondenceStatus,
    );
  }
}