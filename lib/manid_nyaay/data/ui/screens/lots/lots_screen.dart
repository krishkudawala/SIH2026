import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/lot_card.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/navigation/screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/lots/lots_view_model.dart';

// Import your components, theme, and router
// import 'package:mandi_nyaay/ui/components/mandi_top_app_bar.dart';
// import 'package:mandi_nyaay/ui/components/lot_list_row.dart';
// import 'package:mandi_nyaay/ui/navigation/screen.dart';
// import 'package:mandi_nyaay/ui/screens/lots/lots_view_model.dart';

// --- Theme Constants Placeholder ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textHint = Color(0xFF94A3B8);
const Color textOnBlue = Colors.white;
const Color dividerGray = Color(0xFFE2E8F0);

class LotsScreen extends StatefulWidget {
  const LotsScreen({super.key});

  @override
  State<LotsScreen> createState() => _LotsScreenState();
}

class _LotsScreenState extends State<LotsScreen> {
  late final LotsViewModel _viewModel;
  late final TextEditingController _searchController;

  @override
  void initState() {
    super.initState();
    _viewModel = LotsViewModel();
    // Using a controller allows the text field to maintain cursor position smoothly
    _searchController = TextEditingController(text: _viewModel.uiState.searchQuery);
  }

  @override
  void dispose() {
    _searchController.dispose();
    _viewModel.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _viewModel,
      builder: (context, _) {
        final state = _viewModel.uiState;

        // If the ViewModel updates the search query programmatically, keep the controller in sync
        if (_searchController.text != state.searchQuery) {
          _searchController.text = state.searchQuery;
        }

        return Scaffold(
          backgroundColor: backgroundGray,
          appBar: const MandiTopAppBar(
            title: "Lots",
            showBack: false, // Explicitly false as per original Compose file
          ),
          body: Column(
            children: [
              // ── Search bar ─────────────────────────────────────────────────
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 14.0, vertical: 10.0),
                child: TextField(
                  controller: _searchController,
                  onChanged: _viewModel.onSearchQueryChanged,
                  maxLines: 1, // singleLine = true
                  decoration: InputDecoration(
                    hintText: "Search lot ID, farmer, or village",
                    hintStyle: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: textHint,
                    ),
                    prefixIcon: const Icon(Icons.search, color: textSecondary),
                    filled: true,
                    fillColor: surfaceWhite, // unfocusedContainerColor / focusedContainerColor
                    contentPadding: const EdgeInsets.symmetric(vertical: 0.0), // Keeps it compact
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8.0),
                      borderSide: const BorderSide(color: dividerGray), // unfocusedBorderColor
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8.0),
                      borderSide: const BorderSide(color: institutionalBlue), // focusedBorderColor
                    ),
                  ),
                ),
              ),

              // ── Filter chips ───────────────────────────────────────────────
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 14.0),
                child: Row(
                  children: [
                    ("All", LotFilter.all),
                    ("Active", LotFilter.active),
                    ("Completed", LotFilter.completed),
                    ("Needs Review", LotFilter.needsReview),
                  ].map((pair) {
                    final label = pair.$1;
                    final filter = pair.$2;
                    final isSelected = state.activeFilter == filter;

                    return Padding(
                      padding: const EdgeInsets.only(right: 8.0),
                      child: ChoiceChip(
                        label: Text(
                          label,
                          style: Theme.of(context).textTheme.labelMedium?.copyWith(
                            color: isSelected ? textOnBlue : textPrimary,
                          ),
                        ),
                        selected: isSelected,
                        onSelected: (selected) {
                          if (selected) {
                            _viewModel.onFilterChanged(filter);
                          }
                        },
                        selectedColor: institutionalBlue,
                        backgroundColor: surfaceWhite,
                        showCheckmark: false, // Ensures just the text shows, matching Compose FilterChip defaults
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8.0),
                          side: BorderSide(
                            color: isSelected ? institutionalBlue : Colors.transparent,
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ),

              const SizedBox(height: 8.0),

              // ── Lot list ───────────────────────────────────────────────────
              Expanded( // Modifier.weight(1f)
                child: ListView.separated(
                  itemCount: state.filteredLots.length,
                  separatorBuilder: (context, index) => const Divider(
                    indent: 16.0,
                    endIndent: 16.0,
                    height: 1.0,
                    thickness: 0.5,
                    color: dividerGray,
                  ),
                  itemBuilder: (context, index) {
                    final lot = state.filteredLots[index];

                    return Material(
                      color: surfaceWhite,
                      child: LotListRow(
                        lot: lot,
                        onClick: () => context.push(
                          Screen.createLotDetailsRoute(lot.id),
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}