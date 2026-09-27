import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/chevron_row.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/navigation/screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/more/more_view_model.dart';

// --- Assumed Imports (Replace with actual paths) ---
// import 'package:mandi_nyaay/ui/components/mandi_top_app_bar.dart';
// import 'package:mandi_nyaay/ui/components/chevron_row.dart';
// import 'package:mandi_nyaay/ui/navigation/screen.dart';
// import 'package:mandi_nyaay/ui/screens/more/more_view_model.dart';

// --- Theme Constants Placeholder ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color dividerGray = Color(0xFFE2E8F0);
const Color statusRed = Color(0xFFEF4444);

const Color statusGreenLight = Color(0xFFE8F5E9);
const Color statusGreen = Color(0xFF4CAF50);
const Color statusAmberLight = Color(0xFFFFF8E1);
const Color statusAmber = Color(0xFFFFA000);

class MoreScreen extends StatefulWidget {
  const MoreScreen({super.key});

  @override
  State<MoreScreen> createState() => _MoreScreenState();
}

class _MoreScreenState extends State<MoreScreen> {
  late final MoreViewModel _viewModel;

  @override
  void initState() {
    super.initState();
    _viewModel = MoreViewModel();
  }

  @override
  void dispose() {
    _viewModel.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _viewModel,
      builder: (context, _) {
        final state = _viewModel.uiState;

        return Scaffold(
          backgroundColor: backgroundGray,
          appBar: const MandiTopAppBar(
            title: "More",
          ),
          body: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 12.0),

                // ── Calibration Health ───────────────────────────────────────
                if (state.calibration != null) ...[
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 6.0),
                    child: Text(
                      "Calibration Health",
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: textSecondary,
                      ),
                    ),
                  ),
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
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  "Calibration Status",
                                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    fontWeight: FontWeight.w500, // Medium
                                    color: textPrimary,
                                  ),
                                ),
                                _buildCalibrationBadge(state.calibration!.currentState),
                              ],
                            ),
                            const Divider(color: dividerGray, thickness: 0.5, height: 16.0),
                            _buildInfoRow(context, "Last checked", state.calibration!.lastChecked),
                            const SizedBox(height: 4.0),
                            _buildInfoRow(context, "Reference marker", state.calibration!.referenceMarkerUsed),
                          ],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12.0),
                ],

                // ── Active Rule Pack ─────────────────────────────────────────
                if (state.rulePack != null) ...[
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 6.0),
                    child: Text(
                      "Active Rule Pack",
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: textSecondary,
                      ),
                    ),
                  ),
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
                              state.rulePack!.commodity,
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: textPrimary,
                              ),
                            ),
                            const SizedBox(height: 4.0),
                            _buildInfoRow(context, "Version", "v${state.rulePack!.version}"),
                            const SizedBox(height: 2.0),
                            _buildInfoRow(context, "Effective date", state.rulePack!.effectiveDate),
                          ],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12.0),
                ],

                // ── General settings ─────────────────────────────────────────
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 6.0),
                  child: Text(
                    "Settings",
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: textSecondary,
                    ),
                  ),
                ),
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
                        ChevronRow(icon: Icons.notifications, title: "Notifications", onClick: () {}),
                        const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                        ChevronRow(icon: Icons.settings, title: "App Settings", onClick: () {}),
                        const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                        ChevronRow(
                          icon: Icons.cloud_download,
                          title: "Offline Data",
                          onClick: () => context.push(Screen.offlineSync),
                        ),
                        const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                        ChevronRow(icon: Icons.help, title: "Help & Support", onClick: () {}),
                        const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                        ChevronRow(icon: Icons.info, title: "About MANDI NYAAY", onClick: () {}),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 12.0),

                // ── Profile / logout ─────────────────────────────────────────
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
                          icon: Icons.person,
                          title: "Profile",
                          onClick: () => context.push(Screen.profile),
                        ),
                        const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                        InkWell(
                          onTap: () {
                            // Logout action
                          },
                          borderRadius: const BorderRadius.only(
                            bottomLeft: Radius.circular(8.0),
                            bottomRight: Radius.circular(8.0),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 14.0),
                            child: Row(
                              children: [
                                const Icon(Icons.logout, color: statusRed, size: 22.0),
                                const SizedBox(width: 14.0),
                                Text(
                                  "Logout",
                                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                    color: statusRed,
                                    fontWeight: FontWeight.w500, // Medium
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 16.0),
              ],
            ),
          ),
        );
      },
    );
  }

  // ── Helper UI Methods ──────────────────────────────────────────────────────

  Widget _buildCalibrationBadge(CalibrationState state) {
    final (Color bg, Color fg) = switch (state) {
      CalibrationState.good => (statusGreenLight, statusGreen),
      CalibrationState.driftDetected => (statusAmberLight, statusAmber),
      _ => (backgroundGray, textSecondary),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 3.0),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(4.0),
      ),
      child: Text(
        state.displayLabel,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: fg,
          fontWeight: FontWeight.w600, // SemiBold
        ),
      ),
    );
  }

  Widget _buildInfoRow(BuildContext context, String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: textSecondary,
          ),
        ),
        Text(
          value,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: textPrimary,
            fontWeight: FontWeight.w500, // Medium
          ),
        ),
      ],
    );
  }
}