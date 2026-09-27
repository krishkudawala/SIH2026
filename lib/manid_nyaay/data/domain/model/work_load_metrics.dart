// --- Enums ---

import 'package:sih2631/manid_nyaay/data/domain/model/onion_record.dart';

enum CalibrationState {
  good("Good"),
  driftDetected("Drift Detected"),
  uncalibrated("Uncalibrated"),
  unknown("Unknown");

  final String displayLabel;
  const CalibrationState(this.displayLabel);
}

enum ReviewReason {
  correspondenceUncertain("Correspondence Uncertain"),
  lowConfidence("Low Confidence"),
  weighbridgeSignal("Weighbridge Signal"),
  manualFlag("Manual Flag");

  final String displayLabel;
  const ReviewReason(this.displayLabel);
}

enum ReviewStatus {
  pending,
  disputed,
  accepted,
  overridden,
  recaptureRequested,
}

// --- Data Classes ---

class WorkloadMetrics {
  final int activeLots;
  final int reviewNeeded;
  final int syncPending;

  const WorkloadMetrics({
    required this.activeLots,
    required this.reviewNeeded,
    required this.syncPending,
  });

  WorkloadMetrics copyWith({
    int? activeLots,
    int? reviewNeeded,
    int? syncPending,
  }) {
    return WorkloadMetrics(
      activeLots: activeLots ?? this.activeLots,
      reviewNeeded: reviewNeeded ?? this.reviewNeeded,
      syncPending: syncPending ?? this.syncPending,
    );
  }
}

class Inspector {
  final String id;
  final String name;
  final String apmc;
  final String initials;

  // We generate the initials dynamically in the initializer list if none are provided.
  Inspector({
    required this.id,
    required this.name,
    required this.apmc,
    String? initials,
  }) : initials = initials ??
      name
          .split(' ')
          .where((word) => word.isNotEmpty)
          .map((word) => word[0])
          .take(2)
          .join('')
          .toUpperCase();

  Inspector copyWith({
    String? id,
    String? name,
    String? apmc,
    String? initials,
  }) {
    return Inspector(
      id: id ?? this.id,
      name: name ?? this.name,
      apmc: apmc ?? this.apmc,
      initials: initials ?? this.initials,
    );
  }
}

class SyncStatus {
  final bool isOnline;
  final int pendingRecords;
  final String? lastSyncedAt;

  const SyncStatus({
    required this.isOnline,
    required this.pendingRecords,
    this.lastSyncedAt,
  });

  SyncStatus copyWith({
    bool? isOnline,
    int? pendingRecords,
    String? lastSyncedAt,
  }) {
    return SyncStatus(
      isOnline: isOnline ?? this.isOnline,
      pendingRecords: pendingRecords ?? this.pendingRecords,
      lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
    );
  }
}

class CalibrationHealth {
  final String lastChecked;
  final String referenceMarkerUsed;
  final CalibrationState currentState;

  const CalibrationHealth({
    required this.lastChecked,
    required this.referenceMarkerUsed,
    required this.currentState,
  });

  CalibrationHealth copyWith({
    String? lastChecked,
    String? referenceMarkerUsed,
    CalibrationState? currentState,
  }) {
    return CalibrationHealth(
      lastChecked: lastChecked ?? this.lastChecked,
      referenceMarkerUsed: referenceMarkerUsed ?? this.referenceMarkerUsed,
      currentState: currentState ?? this.currentState,
    );
  }
}

class RulePack {
  final String id;
  final String version;
  final String effectiveDate;
  final String commodity;
  final String description;

  const RulePack({
    required this.id,
    required this.version,
    required this.effectiveDate,
    required this.commodity,
    required this.description,
  });

  RulePack copyWith({
    String? id,
    String? version,
    String? effectiveDate,
    String? commodity,
    String? description,
  }) {
    return RulePack(
      id: id ?? this.id,
      version: version ?? this.version,
      effectiveDate: effectiveDate ?? this.effectiveDate,
      commodity: commodity ?? this.commodity,
      description: description ?? this.description,
    );
  }
}

class ReviewItem {
  final String sampleId;
  final String lotId;
  final String farmerName;
  final double weightKg;
  final ReviewReason reason;
  // Note: Assuming 'Grade' enum is already imported/available from your previous code
  final Grade tentativeGrade;
  final double? confidence; // Maps to Kotlin's Float?
  final ReviewStatus status;

  const ReviewItem({
    required this.sampleId,
    required this.lotId,
    required this.farmerName,
    required this.weightKg,
    required this.reason,
    required this.tentativeGrade,
    this.confidence,
    required this.status,
  });

  ReviewItem copyWith({
    String? sampleId,
    String? lotId,
    String? farmerName,
    double? weightKg,
    ReviewReason? reason,
    Grade? tentativeGrade,
    double? confidence,
    ReviewStatus? status,
  }) {
    return ReviewItem(
      sampleId: sampleId ?? this.sampleId,
      lotId: lotId ?? this.lotId,
      farmerName: farmerName ?? this.farmerName,
      weightKg: weightKg ?? this.weightKg,
      reason: reason ?? this.reason,
      tentativeGrade: tentativeGrade ?? this.tentativeGrade,
      confidence: confidence ?? this.confidence,
      status: status ?? this.status,
    );
  }
}

class OverrideRecord {
  final String reviewItemId;
  final Grade originalGrade;
  final Grade overrideGrade;
  final String reason;
  final String inspectorId;
  final int timestamp; // Maps to Kotlin's Long

  const OverrideRecord({
    required this.reviewItemId,
    required this.originalGrade,
    required this.overrideGrade,
    required this.reason,
    required this.inspectorId,
    required this.timestamp,
  });

  OverrideRecord copyWith({
    String? reviewItemId,
    Grade? originalGrade,
    Grade? overrideGrade,
    String? reason,
    String? inspectorId,
    int? timestamp,
  }) {
    return OverrideRecord(
      reviewItemId: reviewItemId ?? this.reviewItemId,
      originalGrade: originalGrade ?? this.originalGrade,
      overrideGrade: overrideGrade ?? this.overrideGrade,
      reason: reason ?? this.reason,
      inspectorId: inspectorId ?? this.inspectorId,
      timestamp: timestamp ?? this.timestamp,
    );
  }
}

class ReportSummary {
  final String date;
  final int totalLots;
  final int gradeACount;
  final int ursCount;
  final int rejectCount;
  final int otherCount;

  const ReportSummary({
    required this.date,
    required this.totalLots,
    required this.gradeACount,
    required this.ursCount,
    required this.rejectCount,
    required this.otherCount,
  });

  ReportSummary copyWith({
    String? date,
    int? totalLots,
    int? gradeACount,
    int? ursCount,
    int? rejectCount,
    int? otherCount,
  }) {
    return ReportSummary(
      date: date ?? this.date,
      totalLots: totalLots ?? this.totalLots,
      gradeACount: gradeACount ?? this.gradeACount,
      ursCount: ursCount ?? this.ursCount,
      rejectCount: rejectCount ?? this.rejectCount,
      otherCount: otherCount ?? this.otherCount,
    );
  }
}