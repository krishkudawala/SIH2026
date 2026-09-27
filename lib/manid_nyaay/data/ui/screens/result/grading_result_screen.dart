import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/result/result_view_model.dart';

// --- Assumed Imports (Replace with actual paths) ---
// import 'package:mandi_nyaay/domain/model/grade.dart';
// import 'package:mandi_nyaay/domain/model/weighbridge_check.dart';
// import 'package:mandi_nyaay/domain/model/defect.dart';
// import 'package:mandi_nyaay/ui/components/mandi_top_app_bar.dart';
// import 'package:mandi_nyaay/ui/screens/result/result_view_model.dart';
// import 'package:mandi_nyaay/data/fixture/fixture_data.dart'; // Temporarily used for mocks

// --- Theme Constants Placeholder ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color blueLight = Color(0xFFE1F5FE);
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color dividerGray = Color(0xFFE2E8F0);
const Color progressTrack = Color(0xFFE2E8F0);

const Color gradeAColor = Color(0xFF4CAF50); // StatusGreen
const Color ursColor = Color(0xFFFFA000);    // StatusAmber
const Color rejectColor = Color(0xFFEF4444); // StatusRed

const Color statusGreenLight = Color(0xFFE8F5E9);
const Color statusGreen = Color(0xFF4CAF50);
const Color statusAmberLight = Color(0xFFFFF8E1);
const Color statusAmber = Color(0xFFFFA000);

// --- Placeholder Enums (Remove when importing real ones) ---
enum Grade { gradeA, urs, reject }

class GradingResultScreen extends StatefulWidget {
  final String lotId;

  const GradingResultScreen({
    super.key,
    required this.lotId,
  });

  @override
  State<GradingResultScreen> createState() => _GradingResultScreenState();
}

class _GradingResultScreenState extends State<GradingResultScreen> {
  late final ResultViewModel _viewModel;

  @override
  void initState() {
    super.initState();
    _viewModel = ResultViewModel(lotId: widget.lotId);
  }

  @override
  void dispose() {
    _viewModel.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Grading Result",
        showBack: true,
        onBack: () => context.pop(), // navController.popBackStack()
      ),
      body: ListenableBuilder(
        listenable: _viewModel,
        builder: (context, _) {
          final state = _viewModel.uiState;

          // Note: using a mock result here since the VM currently mocks null.
          // Replace `mockResult` with `state.result` once hooked up.
          final result = state.result ?? _getMockResult();
          final lot = state.lot;

          if (state.isLoading) {
            return const Center(
              child: CircularProgressIndicator(color: institutionalBlue),
            );
          }

          // ── Calculate Primary Grade ────────────────────────────────────────
          final Grade primaryGrade;
          if (result.gradeAByWeight >= result.ursByWeight && result.gradeAByWeight >= result.rejectByWeight) {
            primaryGrade = Grade.gradeA;
          } else if (result.ursByWeight >= result.rejectByWeight) {
            primaryGrade = Grade.urs;
          } else {
            primaryGrade = Grade.reject;
          }

          final (Color gradeColor, String gradeText) = switch (primaryGrade) {
            Grade.gradeA => (gradeAColor, "Grade A"),
            Grade.urs => (ursColor, "URS"),
            Grade.reject => (rejectColor, "Reject"),
          };

          return SingleChildScrollView(
            padding: const EdgeInsets.all(14.0),
            child: Column(
              children: [
                // ── Image placeholder ────────────────────────────────────────
                Container(
                  width: double.infinity,
                  height: 160.0,
                  decoration: BoxDecoration(
                    color: const Color(0xFF1A1A1A),
                    borderRadius: BorderRadius.circular(8.0),
                  ),
                  alignment: Alignment.center,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.image, color: Colors.white.withOpacity(0.3), size: 40.0),
                      const SizedBox(height: 4.0),
                      Text(
                        "Sample capture",
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.white.withOpacity(0.3),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12.0),

                // ── Grade result badge ───────────────────────────────────────
                Card(
                  margin: EdgeInsets.zero,
                  elevation: 1.0,
                  color: surfaceWhite,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.check_circle, color: gradeColor, size: 28.0),
                            const SizedBox(width: 10.0),
                            Text(
                              gradeText,
                              style: TextStyle(
                                fontSize: 22.0,
                                fontWeight: FontWeight.bold,
                                color: gradeColor,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4.0),
                        Text(
                          "Dominant grade by weight",
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12.0),

                // ── Three-way mass distribution ──────────────────────────────
                Card(
                  margin: EdgeInsets.zero,
                  elevation: 1.0,
                  color: surfaceWhite,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
                  child: Padding(
                    padding: const EdgeInsets.all(14.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "Mass Distribution by Weight",
                          style: Theme.of(context).textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.w600, // SemiBold
                            color: textPrimary,
                          ),
                        ),
                        const SizedBox(height: 12.0),

                        ...[
                          ("GRADE_A", result.gradeAByWeight, gradeAColor),
                          ("URS", result.ursByWeight, ursColor),
                          ("REJECT", result.rejectByWeight, rejectColor),
                        ].map((tuple) {
                          final label = tuple.$1;
                          final fraction = tuple.$2;
                          final color = tuple.$3;

                          return Padding(
                            padding: const EdgeInsets.symmetric(vertical: 4.0),
                            child: Row(
                              children: [
                                SizedBox(
                                  width: 72.0,
                                  child: Text(
                                    label,
                                    style: Theme.of(context).textTheme.labelMedium?.copyWith(color: textSecondary),
                                  ),
                                ),
                                Expanded(
                                  child: Container(
                                    height: 14.0,
                                    decoration: BoxDecoration(
                                      color: progressTrack,
                                      borderRadius: BorderRadius.circular(7.0),
                                    ),
                                    alignment: Alignment.centerLeft, // Aligns inner box to the left
                                    child: FractionallySizedBox(
                                      widthFactor: fraction,
                                      child: Container(
                                        decoration: BoxDecoration(
                                          color: color,
                                          borderRadius: BorderRadius.circular(7.0),
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                                SizedBox(
                                  width: 42.0,
                                  child: Text(
                                    "${(fraction * 100).toInt()}%",
                                    textAlign: TextAlign.end,
                                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                                      fontWeight: FontWeight.bold,
                                      color: color,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          );
                        }).toList(),

                        const SizedBox(height: 8.0),
                        const Divider(color: dividerGray, thickness: 0.5, height: 1.0),
                        const SizedBox(height: 8.0),

                        // Grade-A by count comparison
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text("Grade-A by Weight", style: Theme.of(context).textTheme.bodySmall?.copyWith(color: textSecondary)),
                                Text(
                                  "${(result.gradeAByWeight * 100).toInt()}%",
                                  style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold, color: gradeAColor),
                                ),
                              ],
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.center,
                              children: [
                                Text("Divergence", style: Theme.of(context).textTheme.bodySmall?.copyWith(color: textSecondary)),
                                Text(
                                  "+${result.countToWeightDivergencePp.toInt()}pp",
                                  style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold, color: statusAmber),
                                ),
                              ],
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text("Grade-A by Count", style: Theme.of(context).textTheme.bodySmall?.copyWith(color: textSecondary)),
                                Text(
                                  "${(result.gradeAByCount * 100).toInt()}%",
                                  style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold, color: gradeAColor),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12.0),

                // ── Confidence interval ──────────────────────────────────────
                Card(
                  margin: EdgeInsets.zero,
                  elevation: 0.0,
                  color: blueLight,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
                  child: Padding(
                    padding: const EdgeInsets.all(14.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "Confidence Interval",
                          style: Theme.of(context).textTheme.labelMedium?.copyWith(
                            fontWeight: FontWeight.w600,
                            color: institutionalBlue,
                          ),
                        ),
                        const SizedBox(height: 6.0),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              "95% CI: ${(result.ci95Low * 100).toInt()}–${(result.ci95High * 100).toInt()}%",
                              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: institutionalBlue,
                              ),
                            ),
                            Text(
                              "${result.sampleCount} samples",
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: textSecondary),
                            ),
                          ],
                        ),
                        if (!result.isSufficient) ...[
                          const SizedBox(height: 4.0),
                          Text(
                            "⚠ Estimate may be imprecise — additional sampling recommended",
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: statusAmber),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12.0),

                // ── Weighbridge Check ────────────────────────────────────────
                Card(
                  margin: EdgeInsets.zero,
                  elevation: 0.0,
                  color: result.wbFlagged ? statusAmberLight : statusGreenLight,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
                  child: Padding(
                    padding: const EdgeInsets.all(14.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(
                              result.wbFlagged ? Icons.warning : Icons.check_circle,
                              color: result.wbFlagged ? statusAmber : statusGreen,
                              size: 20.0,
                            ),
                            const SizedBox(width: 8.0),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text("Weighbridge Check", style: Theme.of(context).textTheme.labelSmall?.copyWith(color: textSecondary)),
                                Text(
                                  result.wbLabel.toUpperCase(),
                                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                                    fontWeight: FontWeight.bold,
                                    color: result.wbFlagged ? statusAmber : statusGreen,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                        if (result.wbFlagged) ...[
                          const SizedBox(height: 8.0),
                          Text(
                            "Weight divergence exceeds 5%. Manual review required.", // Replace with WeighbridgeCheck.REVIEW_SIGNAL_DISCLAIMER
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: textSecondary),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12.0),

                // ── Detail rows ──────────────────────────────────────────────
                Card(
                  margin: EdgeInsets.zero,
                  elevation: 1.0,
                  color: surfaceWhite,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
                  child: Padding(
                    padding: const EdgeInsets.all(14.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        ...[
                          ("Lot ID", lot?.id ?? widget.lotId),
                          ("Sample Count", result.sampleCount.toString()),
                          ("Rule Pack", "v${result.rulePackVersion}"),
                        ].map((tuple) {
                          return Padding(
                            padding: const EdgeInsets.symmetric(vertical: 4.0),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(tuple.$1, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: textSecondary)),
                                Text(
                                  tuple.$2,
                                  style: Theme.of(context).textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w500, color: textPrimary),
                                ),
                              ],
                            ),
                          );
                        }).toList(),

                        const SizedBox(height: 8.0),

                        // Limitation statement
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(8.0),
                          decoration: BoxDecoration(
                            color: backgroundGray,
                            borderRadius: BorderRadius.circular(4.0),
                          ),
                          child: Text(
                            "Report covers external visual defects only.", // Replace with Defect.EXTERNAL_ONLY_STATEMENT
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: textSecondary),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12.0),

                // ── Actions ──────────────────────────────────────────────────
                SizedBox(
                  width: double.infinity,
                  height: 48.0,
                  child: ElevatedButton(
                    onPressed: () => context.pop(),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: institutionalBlue,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
                    ),
                    child: Text(
                      "SAVE RESULT",
                      style: Theme.of(context).textTheme.labelLarge?.copyWith(
                        color: textOnBlue,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 12.0),

                SizedBox(
                  width: double.infinity,
                  height: 44.0,
                  child: OutlinedButton(
                    onPressed: () => context.pop(),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: institutionalBlue,
                      side: const BorderSide(color: institutionalBlue),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
                    ),
                    child: Text(
                      "RETAKE SAMPLE",
                      style: Theme.of(context).textTheme.labelLarge?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 8.0),
              ],
            ),
          );
        },
      ),
    );
  }

  // Temporary mock function - replace with actual GradingResult model data mapping
  dynamic _getMockResult() {
    return (
    gradeAByWeight: 0.68,
    ursByWeight: 0.22,
    rejectByWeight: 0.10,
    gradeAByCount: 0.65,
    countToWeightDivergencePp: 3.0,
    ci95Low: 0.62,
    ci95High: 0.74,
    sampleCount: 72,
    isSufficient: true,
    rulePackVersion: "1.4.2",
    wbFlagged: false,
    wbLabel: "Match",
    );
  }
}