import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/fixture/fixture_data.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/batch_capture_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';

// --- Assumed Imports ---
// import 'package:mandi_nyaay/domain/model/inspection_ui_state.dart';
// import 'package:mandi_nyaay/data/fixture/fixture_data.dart';
// import 'package:mandi_nyaay/ui/components/mandi_top_app_bar.dart';

// --- Theme Constants Placeholder ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color blueLight = Color(0xFFE1F5FE);
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color dividerGray = Color(0xFFE2E8F0);

const Color statusGreenLight = Color(0xFFE8F5E9);
const Color statusGreen = Color(0xFF4CAF50);
const Color statusAmberLight = Color(0xFFFFF8E1);
const Color statusAmber = Color(0xFFFFA000);

class SamplingSufficiencyScreen extends StatelessWidget {
  final InspectionUiState uiState;
  final VoidCallback onSampleNextBag;
  final VoidCallback onFinish;
  final VoidCallback onBack;

  const SamplingSufficiencyScreen({
    super.key,
    required this.uiState,
    required this.onSampleNextBag,
    required this.onFinish,
    required this.onBack,
  });

  @override
  Widget build(BuildContext context) {
    // Assuming FixtureData.sampleGradingResult is accessible.
    // If not, replace this with your actual state/mock data.
    final result = FixtureData.sampleGradingResult;
    final plan = uiState.samplingPlan;

    final isSufficient = result.isSufficient;
    final int gradeAPct = (result.gradeAByWeight * 100).toInt();
    final int ciLow = (result.ci95Low * 100).toInt();
    final int ciHigh = (result.ci95High * 100).toInt();
    final int ciWidthTotal = ((result.ci95High - result.ci95Low) * 100).toInt();
    final int ciWidthHalf = (ciWidthTotal / 2).toInt();

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Sampling Sufficiency",
        showBack: true,
        onBack: onBack,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // ── Current Estimate Card ───────────────────────────────────────
            Card(
              margin: EdgeInsets.zero,
              elevation: 1.0,
              color: surfaceWhite,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8.0),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Text(
                      "Current Estimate",
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: textSecondary,
                      ),
                    ),
                    const SizedBox(height: 8.0),
                    Text(
                      "$gradeAPct%",
                      style: const TextStyle(
                        fontSize: 40.0,
                        fontWeight: FontWeight.bold,
                        color: institutionalBlue,
                      ),
                    ),
                    Text(
                      "Grade-A by weight",
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: textSecondary,
                      ),
                    ),
                    const SizedBox(height: 12.0),

                    // CI display
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                      decoration: BoxDecoration(
                        color: blueLight,
                        borderRadius: BorderRadius.circular(6.0),
                      ),
                      child: Text(
                        "95% CI: $ciLow–$ciHigh%",
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w600, // SemiBold
                          color: institutionalBlue,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),

                    const SizedBox(height: 12.0),
                    const Divider(color: dividerGray, thickness: 0.5, height: 1.0),
                    const SizedBox(height: 12.0),

                    // Stats Row
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly, // Arrangement.SpaceEvenly
                      children: [
                        _StatColumn(
                          value: "${result.sampleCount}",
                          label: "Samples",
                        ),
                        _StatColumn(
                          value: "${plan?.totalSamplesRequired ?? 72}",
                          label: "Required",
                        ),
                        _StatColumn(
                          value: "±${ciWidthHalf}pp",
                          label: "CI Width",
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 12.0),

            // ── Sufficiency Status Card ─────────────────────────────────────
            Card(
              margin: EdgeInsets.zero,
              elevation: 0.0,
              color: isSufficient ? statusGreenLight : statusAmberLight,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8.0),
              ),
              child: Padding(
                padding: const EdgeInsets.all(14.0),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Icon(
                      isSufficient ? Icons.check_circle : Icons.warning,
                      color: isSufficient ? statusGreen : statusAmber,
                      size: 24.0,
                    ),
                    const SizedBox(width: 12.0),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            isSufficient ? "SUFFICIENT" : "MORE SAMPLES REQUIRED",
                            style: Theme.of(context).textTheme.labelLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: isSufficient ? statusGreen : statusAmber,
                            ),
                          ),
                          Text(
                            isSufficient
                                ? "Confidence interval is within acceptable range."
                                : "CI width is ${ciWidthTotal}pp. Sample more bags to narrow the estimate.",
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // Pushes everything below it to the bottom of the screen
            const Spacer(), // Spacer(modifier = Modifier.weight(1f))

            // ── Primary Action: Sample Next Bag ──────────────────────────────
            SizedBox(
              width: double.infinity,
              height: 48.0,
              child: ElevatedButton.icon(
                onPressed: onSampleNextBag,
                style: ElevatedButton.styleFrom(
                  backgroundColor: institutionalBlue,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8.0),
                  ),
                ),
                icon: const Icon(Icons.add, color: textOnBlue),
                label: Text(
                  "SAMPLE NEXT BAG",
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: textOnBlue,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 12.0),

            // ── Secondary Action: Finish Anyway ──────────────────────────────
            SizedBox(
              width: double.infinity,
              height: 44.0,
              child: OutlinedButton(
                onPressed: onFinish,
                style: OutlinedButton.styleFrom(
                  foregroundColor: institutionalBlue, // contentColor
                  side: const BorderSide(color: institutionalBlue),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8.0),
                  ),
                ),
                child: Text(
                  "FINISH & VIEW RESULT",
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    fontWeight: FontWeight.w600, // SemiBold
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Private Sub-Component ────────────────────────────────────────────────────

class _StatColumn extends StatelessWidget {
  final String value;
  final String label;

  const _StatColumn({
    required this.value,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Text(
          value,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: textPrimary,
          ),
        ),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: textSecondary,
          ),
        ),
      ],
    );
  }
}