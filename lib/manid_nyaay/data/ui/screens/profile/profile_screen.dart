import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/chevron_row.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/utils/responsive.dart';

// --- Assumed Imports (Replace with actual paths) ---
// import 'package:mandi_nyaay/domain/model/inspector.dart';
// import 'package:mandi_nyaay/data/fixture/fixture_data.dart';
// import 'package:mandi_nyaay/ui/components/mandi_top_app_bar.dart';
// import 'package:mandi_nyaay/ui/components/chevron_row.dart';

// --- Theme Constants Placeholder ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color dividerGray = Color(0xFFE2E8F0);

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Replace with your actual fixture/state call:
    // final inspector = FixtureData.inspector;

    // Mocking variables here for compilability
    const inspectorInitials = "RS";
    const inspectorName = "Rajesh Sharma";
    const inspectorApmc = "Karnal Mandi";

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Profile",
        showBack: true,
        onBack: () => context.pop(), // navController.popBackStack()
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // ── Profile Header ───────────────────────────────────────────────
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
                  padding: const EdgeInsets.all(16.0),
                  child: Row(
                    children: [
                      Container(
                        width: 52.0,
                        height: 52.0,
                        decoration: const BoxDecoration(
                          color: institutionalBlue,
                          shape: BoxShape.circle,
                        ),
                        alignment: Alignment.center,
                        child: Text(
                          inspectorInitials,
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: textOnBlue,
                          ),
                        ),
                      ),
                      const SizedBox(width: 14.0),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              inspectorName,
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: textPrimary,
                              ),
                            ),
                            Text(
                              "Quality Inspector",
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: textSecondary,
                              ),
                            ),
                            Text(
                              inspectorApmc,
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: institutionalBlue,
                                fontWeight: FontWeight.w500, // Medium
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

            // ── Settings Rows ────────────────────────────────────────────────
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
                      title: "My Profile",
                      subtitle: "View and edit profile",
                      onClick: () {},
                    ),
                    const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                    ChevronRow(
                      icon: Icons.lock,
                      title: "Change Password",
                      onClick: () {},
                    ),
                    const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                    ChevronRow(
                      icon: Icons.language,
                      title: "Language",
                      // mapped trailingText to subtitle; if you added trailingText
                      // to your Dart ChevronRow class, use trailingText: "English" instead.
                      subtitle: "English",
                      onClick: () {},
                    ),
                    const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                    ChevronRow(
                      icon: Icons.privacy_tip,
                      title: "Privacy Policy",
                      onClick: () {},
                    ),
                    const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                    ChevronRow(
                      icon: Icons.article,
                      title: "Terms & Conditions",
                      onClick: () {},
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
  }
}