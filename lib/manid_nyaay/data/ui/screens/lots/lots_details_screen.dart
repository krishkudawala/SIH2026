import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/chevron_row.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/lot_card.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/navigation/screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/lots/lot_details_view_model.dart';

// Import your components, models, theme, and router
// import 'package:mandi_nyaay/domain/model/lot_status.dart';
// import 'package:mandi_nyaay/ui/components/mandi_top_app_bar.dart';
// import 'package:mandi_nyaay/ui/components/status_badge.dart';
// import 'package:mandi_nyaay/ui/components/chevron_row.dart';
// import 'package:mandi_nyaay/ui/components/sampling_progress_bar.dart';
// import 'package:mandi_nyaay/ui/navigation/screen.dart';
// import 'package:mandi_nyaay/ui/screens/lots/lot_details_view_model.dart';

// --- Theme Constants Placeholder ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color dividerGray = Color(0xFFE2E8F0);

class LotDetailsScreen extends StatefulWidget {
  final String lotId;

  const LotDetailsScreen({
    super.key,
    required this.lotId,
  });

  @override
  State<LotDetailsScreen> createState() => _LotDetailsScreenState();
}

class _LotDetailsScreenState extends State<LotDetailsScreen> {
  late final LotDetailsViewModel _viewModel;

  @override
  void initState() {
    super.initState();
    _viewModel = LotDetailsViewModel(lotId: widget.lotId);
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
        title: "Lot Details",
        showBack: true,
        onBack: () => context.pop(),
      ),
      body: ListenableBuilder(
        listenable: _viewModel,
        builder: (context, _) {
          if (_viewModel.isLoading || _viewModel.lot == null) {
            return const Center(
              child: CircularProgressIndicator(color: institutionalBlue),
            );
          }

          final l = _viewModel.lot!;

          return SingleChildScrollView(
            child: Column(
              children: [
                // ── Header Card ──────────────────────────────────────────────
                Padding(
                  padding: const EdgeInsets.all(14.0),
                  child: Card(
                    color: surfaceWhite,
                    elevation: 1.0,
                    margin: EdgeInsets.zero,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8.0),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(14.0),
                      child: Column(
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            crossAxisAlignment: CrossAxisAlignment.center,
                            children: [
                              Text(
                                l.id,
                                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: textPrimary,
                                ),
                              ),
                              StatusBadge(status: l.status),
                            ],
                          ),
                          const SizedBox(height: 12.0),
                          const Divider(color: dividerGray, thickness: 0.5, height: 1.0),
                          const SizedBox(height: 12.0),

                          ...[
                            ("Date", l.date.toString()),
                            ("Farmer", l.farmerName),
                            ("Variety", l.variety),
                            ("Quantity", "${l.certifiedWeightKg.toInt()} kg (${l.bagCount} bags)"),
                            ("Location", l.location),
                            ("Status", l.status.displayLabel), // Assuming extension/getter
                            ("Weighbridge Ref", l.weighbridgeRef),
                          ].map((pair) {
                            return Padding(
                              padding: const EdgeInsets.symmetric(vertical: 3.0),
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    pair.$1,
                                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                      color: textSecondary,
                                    ),
                                  ),
                                  Text(
                                    pair.$2,
                                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                      fontWeight: FontWeight.w500, // Medium
                                      color: textPrimary,
                                    ),
                                  ),
                                ],
                              ),
                            );
                          }),
                        ],
                      ),
                    ),
                  ),
                ),

                // ── Action Rows Card ─────────────────────────────────────────
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 14.0),
                  child: Card(
                    color: surfaceWhite,
                    elevation: 1.0,
                    margin: EdgeInsets.zero,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8.0),
                    ),
                    child: Column(
                      children: [
                        ChevronRow(
                          icon: Icons.image,
                          title: "View Images",
                          subtitle: "${(l.samplingPlan?.completedSamples ?? 0) * 3} images",
                          onClick: () {},
                        ),
                        const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                        ChevronRow(
                          icon: Icons.analytics,
                          title: "Grading Result",
                          subtitle: l.status == LotStatus.active ? "Sampling in progress" : "View result",
                          onClick: () => context.push(Screen.createGradingResultRoute(l.id)),
                        ),
                        const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                        ChevronRow(
                          icon: Icons.edit,
                          title: "Edit Details",
                          subtitle: "Modify lot information",
                          onClick: () {},
                        ),
                        const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                        ChevronRow(
                          icon: Icons.note,
                          title: "Add Notes",
                          subtitle: "Inspection remarks",
                          onClick: () {},
                        ),
                        const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                        ChevronRow(
                          icon: Icons.person,
                          title: "Farmer Details",
                          subtitle: l.farmerName,
                          onClick: () => context.push(Screen.createFarmerDetailsRoute(l.farmerId)),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 14.0),

                // ── Sampling Progress ────────────────────────────────────────
                if (l.samplingPlan != null) ...[
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 14.0),
                    child: Card(
                      color: surfaceWhite,
                      elevation: 1.0,
                      margin: EdgeInsets.zero,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8.0),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(14.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "Sampling Progress",
                              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                                fontWeight: FontWeight.w600, // SemiBold
                                color: textPrimary,
                              ),
                            ),
                            const SizedBox(height: 10.0),
                            SamplingProgressBar(
                              completed: l.samplingPlan!.completedSamples,
                              total: l.samplingPlan!.totalSamplesRequired,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 14.0),
                ],

                // ── Primary Action Button ────────────────────────────────────
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 14.0),
                  child: SizedBox(
                    width: double.infinity,
                    height: 48.0,
                    child: ElevatedButton(
                      onPressed: () => context.push(Screen.createInspectionRoute(l.id)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: institutionalBlue,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8.0),
                        ),
                      ),
                      child: Text(
                        l.status == LotStatus.completed ? "VIEW RESULT" : "CONTINUE INSPECTION",
                        style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          color: textOnBlue,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 16.0),
              ],
            ),
          );
        },
      ),
    );
  }
}