import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/chevron_row.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/navigation/screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/farmer/farmer_view_model.dart';
import 'package:sih2631/manid_nyaay/data/ui/utils/responsive.dart';

// Import your components, theme, model, and ViewModel
// import 'package:mandi_nyaay/domain/model/farmer.dart';
// import 'package:mandi_nyaay/ui/components/chevron_row.dart';
// import 'package:mandi_nyaay/ui/components/mandi_top_app_bar.dart';
// import 'package:mandi_nyaay/ui/navigation/screen.dart';
// import 'package:mandi_nyaay/ui/screens/farmer/farmer_view_model.dart';

// --- Placeholder Colors & Theme ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textOnBlue = Colors.white;
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color dividerGray = Color(0xFFE2E8F0);

class FarmerDetailsScreen extends StatefulWidget {
  final String farmerId;

  const FarmerDetailsScreen({
    super.key,
    required this.farmerId,
  });

  @override
  State<FarmerDetailsScreen> createState() => _FarmerDetailsScreenState();
}

class _FarmerDetailsScreenState extends State<FarmerDetailsScreen> {
  late final FarmerViewModel _viewModel;

  @override
  void initState() {
    super.initState();
    _viewModel = FarmerViewModel(farmerId: widget.farmerId);
  }

  @override
  void dispose() {
    _viewModel.dispose();
    super.dispose();
  }

  // Helper method to extract up to 2 initial letters from the farmer's name
  String _getInitials(String name) {
    final parts = name.trim().split(RegExp(r'\s+')).where((e) => e.isNotEmpty);
    if (parts.isEmpty) return '';
    return parts.take(2).map((part) => part[0].toUpperCase()).join('');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Farmer Details",
        showBack: true,
        onBack: () => context.pop(),
      ),
      body: ListenableBuilder(
        listenable: _viewModel,
        builder: (context, _) {
          if (_viewModel.isLoading || _viewModel.farmer == null) {
            return const Center(
              child: CircularProgressIndicator(color: institutionalBlue),
            );
          }

          final farmer = _viewModel.farmer!;

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
                      child: Row(
                        children: [
                          // Initials Avatar
                          Container(
                            width: 48.0,
                            height: 48.0,
                            decoration: const BoxDecoration(
                              color: institutionalBlue,
                              shape: BoxShape.circle,
                            ),
                            alignment: Alignment.center,
                            child: Text(
                              _getInitials(farmer.name),
                              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: textOnBlue,
                              ),
                            ),
                          ),
                          const SizedBox(width: 14.0),
                          // Name & Phone
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                farmer.name,
                                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: textPrimary,
                                ),
                              ),
                              Text(
                                farmer.phone,
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: textSecondary,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

                // ── Detail Rows Card ─────────────────────────────────────────
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
                      child: Builder(
                        builder: (context) {
                          final details = [
                            ("Farmer ID", farmer.id),
                            ("Village", farmer.village),
                            ("Taluka", farmer.taluka),
                            ("Last Supply", farmer.lastSupply),
                            ("Total Supplies", "${farmer.totalSupplies} lots"),
                          ];

                          return Column(
                            children: List.generate(details.length, (idx) {
                              final (label, value) = details[idx];
                              return Column(
                                children: [
                                  Padding(
                                    padding: const EdgeInsets.symmetric(vertical: 5.0),
                                    child: Row(
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
                                            fontWeight: FontWeight.w500, // Medium
                                            color: textPrimary,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  if (idx < details.length - 1)
                                    const Divider(
                                      color: dividerGray,
                                      thickness: 0.5,
                                      height: 1.0,
                                    ),
                                ],
                              );
                            }),
                          );
                        },
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 12.0),

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
                          icon: Icons.history,
                          title: "View Supply History",
                          subtitle: "${farmer.totalSupplies} lots",
                          onClick: () {},
                        ),
                        const Divider(
                          indent: 16.0,
                          endIndent: 16.0,
                          thickness: 0.5,
                          height: 1.0,
                          color: dividerGray,
                        ),
                        ChevronRow(
                          icon: Icons.add_box,
                          title: "Add New Lot",
                          subtitle: "Create lot for this farmer",
                          onClick: () => context.push(Screen.newLot),
                        ),
                        const Divider(
                          indent: 16.0,
                          endIndent: 16.0,
                          thickness: 0.5,
                          height: 1.0,
                          color: dividerGray,
                        ),
                        ChevronRow(
                          icon: Icons.edit,
                          title: "Edit Farmer Details",
                          subtitle: "Modify information",
                          onClick: () {},
                        ),
                      ],
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