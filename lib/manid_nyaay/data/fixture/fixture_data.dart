// Converted from Kotlin: com.mandiNyaay.data.fixture.FixtureData
//
// NOTE: The original Kotlin file only shows how each model is *constructed*,
// not its class definition (those live in com.mandiNyaay.domain.model).
// Reconstructed here from the domain models.

import 'package:sih2631/manid_nyaay/data/domain/model/farmer.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/grading_result.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/onion_record.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/work_load_metrics.dart';

// ---------------------------------------------------------------------------
// Fixture data (equivalent of the Kotlin `object FixtureData`)
// ---------------------------------------------------------------------------

class FixtureData {
  FixtureData._();

  static final inspector = Inspector(
    id: 'INS-001',
    name: 'Rahul Sharma',
    apmc: 'Nashik APMC',
  );

  static const farmers = <Farmer>[
    Farmer(
      id: 'FMR-1024',
      name: 'Suresh Patil',
      phone: '+91 98765 43210',
      village: 'Lasalgaon',
      taluka: 'Nashik',
      district: 'Nashik',
      totalSupplies: 28,
      lastSupply: '16 Sep 2026',
    ),
    Farmer(
      id: 'FMR-1025',
      name: 'Ramesh Jadhav',
      phone: '+91 90123 45678',
      village: 'Pimpalgaon',
      taluka: 'Nashik',
      district: 'Nashik',
      totalSupplies: 14,
      lastSupply: '15 Sep 2026',
    ),
    Farmer(
      id: 'FMR-1026',
      name: 'Vilas Shinde',
      phone: '+91 99887 65432',
      village: 'Yeola',
      taluka: 'Nashik',
      district: 'Nashik',
      totalSupplies: 22,
      lastSupply: '14 Sep 2026',
    ),
    Farmer(
      id: 'FMR-1027',
      name: 'Anil Pawar',
      phone: '+91 88776 65544',
      village: 'Manchar',
      taluka: 'Pune',
      district: 'Pune',
      totalSupplies: 9,
      lastSupply: '12 Sep 2026',
    ),
    Farmer(
      id: 'FMR-1028',
      name: 'Kiran Mote',
      phone: '+91 77665 54433',
      village: 'Rahuri',
      taluka: 'Ahmednagar',
      district: 'Ahmednagar',
      totalSupplies: 6,
      lastSupply: '11 Sep 2026',
    ),
  ];

  static final lots = <Lot>[
    Lot(
      id: 'LOT-2026-0917-001',
      farmerId: 'FMR-1024',
      farmerName: 'Suresh Patil',
      village: 'Lasalgaon',
      bagCount: 60,
      certifiedWeightKg: 1000.0,
      weighbridgeRef: 'WB-2026-09-001',
      variety: 'Red Onion',
      location: 'Lasalgaon APMC',
      date: DateTime(2026, 9, 17),
      status: LotStatus.active,
      samplingPlan: const SamplingPlan(totalSamplesRequired: 72, completedSamples: 44),
    ),
    Lot(
      id: 'LOT-2026-0916-009',
      farmerId: 'FMR-1025',
      farmerName: 'Ramesh Jadhav',
      village: 'Pimpalgaon',
      bagCount: 48,
      certifiedWeightKg: 780.0,
      weighbridgeRef: 'WB-2026-09-002',
      variety: 'Red Onion',
      location: 'Pimpalgaon APMC',
      date: DateTime(2026, 9, 16),
      status: LotStatus.disputed,
      samplingPlan: const SamplingPlan(totalSamplesRequired: 72, completedSamples: 72),
    ),
    Lot(
      id: 'LOT-2026-0915-005',
      farmerId: 'FMR-1026',
      farmerName: 'Vilas Shinde',
      village: 'Yeola',
      bagCount: 35,
      certifiedWeightKg: 583.0,
      weighbridgeRef: 'WB-2026-09-003',
      variety: 'Red Onion',
      location: 'Yeola APMC',
      date: DateTime(2026, 9, 15),
      status: LotStatus.needsReview,
      samplingPlan: const SamplingPlan(totalSamplesRequired: 60, completedSamples: 48),
    ),
    Lot(
      id: 'LOT-2026-0914-003',
      farmerId: 'FMR-1027',
      farmerName: 'Anil Pawar',
      village: 'Manchar',
      bagCount: 42,
      certifiedWeightKg: 720.0,
      weighbridgeRef: 'WB-2026-09-004',
      variety: 'Red Onion',
      location: 'Manchar APMC',
      date: DateTime(2026, 9, 14),
      status: LotStatus.completed,
      samplingPlan: const SamplingPlan(totalSamplesRequired: 66, completedSamples: 66),
    ),
    Lot(
      id: 'LOT-2026-0913-007',
      farmerId: 'FMR-1028',
      farmerName: 'Kiran Mote',
      village: 'Rahuri',
      bagCount: 20,
      certifiedWeightKg: 340.0,
      weighbridgeRef: 'WB-2026-09-005',
      variety: 'Red Onion',
      location: 'Rahuri APMC',
      date: DateTime(2026, 9, 13),
      status: LotStatus.completed,
      samplingPlan: const SamplingPlan(totalSamplesRequired: 48, completedSamples: 48),
    ),
  ];

  static const workloadMetrics = WorkloadMetrics(
    activeLots: 3,
    reviewNeeded: 2,
    syncPending: 1,
  );

  static const syncStatus = SyncStatus(
    isOnline: false,
    pendingRecords: 5,
    lastSyncedAt: '16 Sep 2026 • 10:24 AM',
  );

  static const calibrationHealth = CalibrationHealth(
    lastChecked: '16 Sep 2026, 09:15 AM',
    referenceMarkerUsed: 'MN-REF-A4-2026',
    currentState: CalibrationState.good,
  );

  static const activeRulePack = RulePack(
    id: 'RP-ONION-2026-V2',
    version: '2.1.3',
    effectiveDate: '01 Sep 2026',
    commodity: 'Red Onion (Nashik)',
    description: 'Maharashtra APMC Onion Grading Rules 2026',
  );

  static const sampleOnionRecords = <OnionRecord>[
    OnionRecord(
      id: 'ON-001',
      sessionId: 'SES-001',
      batchCaptureIds: ['BC-001', 'BC-002', 'BC-003'],
      estimatedWeightGrams: 52.3,
      diameterMm: 95.4,
      grade: Grade.gradeA,
      defects: [],
    ),
    OnionRecord(
      id: 'ON-002',
      sessionId: 'SES-001',
      batchCaptureIds: ['BC-001', 'BC-002', 'BC-003'],
      estimatedWeightGrams: 48.7,
      diameterMm: 88.1,
      grade: Grade.gradeA,
      defects: [],
    ),
    OnionRecord(
      id: 'ON-003',
      sessionId: 'SES-001',
      batchCaptureIds: ['BC-001', 'BC-002', 'BC-003'],
      estimatedWeightGrams: 41.2,
      diameterMm: 71.3,
      grade: Grade.urs,
      defects: [
        Defect(
          type: DefectType.sprouting,
          ruleVersion: 'RP-ONION-2026-V2',
        )
      ],
    ),
    OnionRecord(
      id: 'ON-004',
      sessionId: 'SES-001',
      batchCaptureIds: ['BC-001', 'BC-002', 'BC-003'],
      estimatedWeightGrams: 55.1,
      diameterMm: 108.2,
      grade: Grade.gradeA,
      defects: [],
    ),
    OnionRecord(
      id: 'ON-005',
      sessionId: 'SES-001',
      batchCaptureIds: ['BC-001', 'BC-002', 'BC-003'],
      estimatedWeightGrams: 38.4,
      diameterMm: 58.6,
      grade: Grade.reject,
      defects: [
        Defect(
          type: DefectType.rot,
          ruleVersion: 'RP-ONION-2026-V2',
        )
      ],
    ),
    OnionRecord(
      id: 'ON-006',
      sessionId: 'SES-001',
      batchCaptureIds: ['BC-001', 'BC-002', 'BC-003'],
      estimatedWeightGrams: 49.9,
      diameterMm: 90.7,
      grade: Grade.gradeA,
      defects: [],
    ),
    OnionRecord(
      id: 'ON-007',
      sessionId: 'SES-001',
      batchCaptureIds: ['BC-001', 'BC-002', 'BC-003'],
      estimatedWeightGrams: 53.6,
      diameterMm: 102.1,
      grade: Grade.gradeA,
      defects: [],
    ),
    OnionRecord(
      id: 'ON-008',
      sessionId: 'SES-001',
      batchCaptureIds: ['BC-001', 'BC-002', 'BC-003'],
      estimatedWeightGrams: 44.8,
      diameterMm: 79.3,
      grade: Grade.urs,
      defects: [
        Defect(
          type: DefectType.bruising,
          ruleVersion: 'RP-ONION-2026-V2',
        )
      ],
    ),
  ];

  static const sampleGradingResult = GradingResult(
    id: 'GR-001',
    lotId: 'LOT-2026-0917-001',
    sessionId: 'SES-001',
    gradeAByWeight: 0.384,
    ursByWeight: 0.372,
    rejectByWeight: 0.244,
    gradeAByCount: 0.625,
    countToWeightDivergencePp: 24.1,
    ci95Low: 0.246,
    ci95High: 0.566,
    sampleCount: 44,
    weighbridgeCheck: WeighbridgeCheck.withinExpectedRange,
    rulePackVersion: '2.1.3',
    isSufficient: false,
  );

  static final reviewItems = <ReviewItem>[
    ReviewItem(
      sampleId: 'MP-24016',
      lotId: 'LOT-2026-0916-009',
      farmerName: 'Ramesh Jadhav',
      weightKg: 30.0,
      reason: ReviewReason.weighbridgeSignal,
      tentativeGrade: Grade.urs,
      confidence: 0.71,
      status: ReviewStatus.pending,
    ),
    ReviewItem(
      sampleId: 'MP-24021',
      lotId: 'LOT-2026-0915-005',
      farmerName: 'Sunil Pawar',
      weightKg: 28.0,
      reason: ReviewReason.correspondenceUncertain,
      tentativeGrade: Grade.gradeA,
      confidence: 0.63,
      status: ReviewStatus.disputed,
    ),
  ];

  static const reportSummary = ReportSummary(
    date: '17 Sep 2026',
    totalLots: 24,
    gradeACount: 14,
    ursCount: 6,
    rejectCount: 2,
    otherCount: 2,
  );
}
