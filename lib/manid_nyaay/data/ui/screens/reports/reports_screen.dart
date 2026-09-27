import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';

// --- Assumed Imports (Replace with actual paths) ---
// import 'package:mandi_nyaay/ui/components/mandi_top_app_bar.dart';
// import 'package:mandi_nyaay/data/fixture/fixture_data.dart';

// --- Theme Constants Placeholder ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color dividerGray = Color(0xFFE2E8F0);

const Color gradeAColor = Color(0xFF4CAF50); // StatusGreen
const Color ursColor = Color(0xFFFFA000);    // StatusAmber
const Color rejectColor = Color(0xFFEF4444); // StatusRed

// --- Mock Data Class (Remove if importing real FixtureData) ---
class ReportSummary {
  final String date;
  final int totalLots;
  final int gradeACount;
  final int ursCount;
  final int rejectCount;
  final int otherCount;

  const ReportSummary(this.date, this.totalLots, this.gradeACount, this.ursCount, this.rejectCount, this.otherCount);
}

class MockReportData {
  static const reportSummary = ReportSummary("Sep 20, 2026", 42, 28, 10, 3, 1);
}

class ReportsScreen extends StatefulWidget {
  const ReportsScreen({super.key});

  @override
  State<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends State<ReportsScreen> {
  int _selectedTab = 0;

  @override
  Widget build(BuildContext context) {
    // Replace with your actual fixture call:
    final summary = MockReportData.reportSummary;

    final stats = [
      ("Total Lots", summary.totalLots, institutionalBlue),
      ("Grade A", summary.gradeACount, gradeAColor),
      ("Grade B / URS", summary.ursCount, ursColor),
      ("Grade C / Reject", summary.rejectCount, rejectColor),
      ("Other", summary.otherCount, textSecondary),
    ];

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: const MandiTopAppBar(
        title: "Reports",
        showBack: false,
      ),
      body: Column(
        children: [
          // ── Daily / Weekly / Monthly tabs ──────────────────────────────────
          Container(
            color: surfaceWhite,
            child: DefaultTabController(
              length: 3,
              initialIndex: _selectedTab,
              child: TabBar(
                onTap: (index) {
                  setState(() {
                    _selectedTab = index;
                  });
                },
                indicatorColor: institutionalBlue,
                labelColor: institutionalBlue,
                unselectedLabelColor: textSecondary,
                labelStyle: Theme.of(context).textTheme.labelMedium,
                tabs: const [
                  Tab(text: "Daily"),
                  Tab(text: "Weekly"),
                  Tab(text: "Monthly"),
                ],
              ),
            ),
          ),

          // ── Scrollable Content ─────────────────────────────────────────────
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(14.0),
              child: Column(
                children: [
                  // ── Date Row ───────────────────────────────────────────────
                  Card(
                    margin: EdgeInsets.zero,
                    elevation: 1.0,
                    color: surfaceWhite,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8.0),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(12.0),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              const Icon(
                                Icons.date_range,
                                color: institutionalBlue,
                                size: 18.0,
                              ),
                              const SizedBox(width: 8.0),
                              Text(
                                summary.date,
                                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                                  fontWeight: FontWeight.w600, // SemiBold
                                  color: textPrimary,
                                ),
                              ),
                            ],
                          ),
                          const Icon(
                            Icons.chevron_right,
                            color: textSecondary,
                            size: 18.0,
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 12.0),

                  // ── Summary Stats ──────────────────────────────────────────
                  Card(
                    margin: EdgeInsets.zero,
                    elevation: 1.0,
                    color: surfaceWhite,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8.0),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(14.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "Summary",
                            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                              fontWeight: FontWeight.w600, // SemiBold
                              color: textPrimary,
                            ),
                          ),
                          const SizedBox(height: 10.0),

                          for (var i = 0; i < stats.length; i++) ...[
                            Padding(
                              padding: const EdgeInsets.symmetric(vertical: 5.0),
                              child: Row(
                                children: [
                                  // Color Dot
                                  Container(
                                    width: 10.0,
                                    height: 10.0,
                                    decoration: BoxDecoration(
                                      color: stats[i].$3,
                                      shape: BoxShape.circle,
                                    ),
                                  ),
                                  const SizedBox(width: 10.0),
                                  // Label
                                  Expanded(
                                    child: Text(
                                      stats[i].$1,
                                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                        color: textPrimary,
                                      ),
                                    ),
                                  ),
                                  // Count
                                  Text(
                                    stats[i].$2.toString(),
                                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                      fontWeight: FontWeight.bold,
                                      color: stats[i].$3,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            if (stats[i].$1 != "Other")
                              const Divider(
                                color: dividerGray,
                                thickness: 0.5,
                                height: 1.0,
                              ),
                          ],
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 16.0), // 4.dp + 12.dp from spacedBy

                  // ── Export Buttons ─────────────────────────────────────────
                  SizedBox(
                    width: double.infinity,
                    height: 46.0,
                    child: ElevatedButton.icon(
                      onPressed: () {},
                      style: ElevatedButton.styleFrom(
                        backgroundColor: institutionalBlue,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8.0),
                        ),
                      ),
                      icon: const Icon(Icons.picture_as_pdf, color: textOnBlue),
                      label: Text(
                        "Export PDF",
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
                    child: OutlinedButton.icon(
                      onPressed: () {},
                      style: OutlinedButton.styleFrom(
                        foregroundColor: institutionalBlue, // contentColor
                        side: const BorderSide(color: institutionalBlue),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8.0),
                        ),
                      ),
                      icon: const Icon(Icons.description),
                      label: Text(
                        "View Detailed Report",
                        style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          fontWeight: FontWeight.w600, // SemiBold
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}