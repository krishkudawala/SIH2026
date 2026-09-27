import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/review/review_view_model.dart';

// --- Assumed Imports (Replace with actual paths) ---
// import 'package:mandi_nyaay/ui/components/mandi_top_app_bar.dart';
// import 'package:mandi_nyaay/ui/screens/review/review_view_model.dart';
// import 'package:mandi_nyaay/domain/model/grade.dart';

// --- Theme Constants Placeholder ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color dividerGray = Color(0xFFE2E8F0);

const Color statusGreen = Color(0xFF4CAF50);
const Color statusAmber = Color(0xFFFFA000);
const Color statusOrange = Color(0xFFFF9800);

class ReviewScreen extends StatefulWidget {
  const ReviewScreen({super.key});

  @override
  State<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends State<ReviewScreen> {
  late final ReviewViewModel _viewModel;

  @override
  void initState() {
    super.initState();
    _viewModel = ReviewViewModel();
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
        final items = state.selectedTab == 0 ? state.pendingItems : state.disputedItems;

        return Stack(
          children: [
            Scaffold(
              backgroundColor: backgroundGray,
              appBar: const MandiTopAppBar(
                title: "Review",
                showBack: false,
              ),
              body: Column(
                children: [
                  // ── Tab row ────────────────────────────────────────────────
                  Container(
                    color: surfaceWhite,
                    child: DefaultTabController(
                      length: 2,
                      initialIndex: state.selectedTab,
                      child: TabBar(
                        onTap: _viewModel.onTabSelected,
                        indicatorColor: institutionalBlue,
                        labelColor: institutionalBlue,
                        unselectedLabelColor: textSecondary,
                        tabs: [
                          Tab(
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Text(
                                  "Pending",
                                  style: Theme.of(context).textTheme.labelMedium,
                                ),
                                if (state.pendingItems.isNotEmpty) ...[
                                  const SizedBox(width: 4.0),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 6.0, vertical: 1.0),
                                    decoration: BoxDecoration(
                                      color: institutionalBlue,
                                      borderRadius: BorderRadius.circular(8.0),
                                    ),
                                    child: Text(
                                      "${state.pendingItems.length}",
                                      style: Theme.of(context).textTheme.labelSmall?.copyWith(color: textOnBlue),
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ),
                          Tab(
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Text(
                                  "Disputed",
                                  style: Theme.of(context).textTheme.labelMedium,
                                ),
                                if (state.disputedItems.isNotEmpty) ...[
                                  const SizedBox(width: 4.0),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 6.0, vertical: 1.0),
                                    decoration: BoxDecoration(
                                      color: statusOrange,
                                      borderRadius: BorderRadius.circular(8.0),
                                    ),
                                    child: Text(
                                      "${state.disputedItems.length}",
                                      style: Theme.of(context).textTheme.labelSmall?.copyWith(color: textOnBlue),
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  // ── Content ────────────────────────────────────────────────
                  Expanded(
                    child: items.isEmpty
                        ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.check_circle, color: statusGreen, size: 48.0),
                          const SizedBox(height: 8.0),
                          Text(
                            "No items in queue",
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: textSecondary,
                            ),
                          ),
                        ],
                      ),
                    )
                        : ListView.separated(
                      padding: const EdgeInsets.all(14.0),
                      itemCount: items.length,
                      separatorBuilder: (context, index) => const SizedBox(height: 8.0),
                      itemBuilder: (context, index) {
                        final item = items[index];
                        return _ReviewItemCard(
                          item: item,
                          onAccept: () => _viewModel.acceptReview(item.sampleId),
                          onOverride: () => _viewModel.openOverrideDialog(item.sampleId),
                          onRecapture: () => _viewModel.requestRecapture(item.sampleId),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),

            // ── Override Dialog (Declarative modal overlay) ──────────────────
            if (state.showOverrideDialog)
              Container(
                color: Colors.black54, // Dim background
                alignment: Alignment.center,
                child: AlertDialog(
                  backgroundColor: surfaceWhite,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12.0)),
                  title: Text(
                    "Override Grade",
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  content: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        "Original system result is preserved. Override reason is mandatory.",
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(color: textSecondary),
                      ),
                      const SizedBox(height: 12.0),
                      TextField(
                        onChanged: _viewModel.onOverrideReasonChanged,
                        minLines: 2,
                        maxLines: 4,
                        decoration: InputDecoration(
                          labelText: "Reason for override (required)",
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8.0),
                          ),
                        ),
                      ),
                    ],
                  ),
                  actions: [
                    TextButton(
                      onPressed: _viewModel.dismissOverrideDialog,
                      child: const Text("CANCEL", style: TextStyle(color: textSecondary)),
                    ),
                    TextButton(
                      onPressed: state.overrideReason.trim().isNotEmpty
                          ? () => _viewModel.confirmOverride(null) // Pass Grade.GRADE_A here
                          : null,
                      child: Text(
                        "CONFIRM OVERRIDE",
                        style: TextStyle(
                          color: state.overrideReason.trim().isNotEmpty ? institutionalBlue : textSecondary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
          ],
        );
      },
    );
  }
}

// ── Private Sub-Component ────────────────────────────────────────────────────

class _ReviewItemCard extends StatelessWidget {
  final dynamic item; // Replace dynamic with ReviewItem
  final VoidCallback onAccept;
  final VoidCallback onOverride;
  final VoidCallback onRecapture;

  const _ReviewItemCard({
    required this.item,
    required this.onAccept,
    required this.onOverride,
    required this.onRecapture,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      elevation: 1.0,
      color: surfaceWhite,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.sampleId,
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: textPrimary,
                      ),
                    ),
                    Text(
                      item.farmerName,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(color: textSecondary),
                    ),
                    Text(
                      "${item.weightKg} kg",
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(color: textSecondary),
                    ),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    const Text("ReviewStatusBadge"), // ReviewStatusBadge(item.status)
                    const SizedBox(height: 4.0),
                    const Text("GradeBadge"), // GradeBadge(item.tentativeGrade.displayLabel)
                    if (item.confidence != null) ...[
                      const SizedBox(height: 2.0),
                      Text(
                        "CI: ${(item.confidence! * 100).toInt()}%",
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(color: textSecondary),
                      ),
                    ],
                  ],
                ),
              ],
            ),
            const SizedBox(height: 6.0),

            // Reason Box
            Container(
              padding: const EdgeInsets.all(6.0),
              decoration: BoxDecoration(
                color: backgroundGray,
                borderRadius: BorderRadius.circular(4.0),
              ),
              child: Text(
                item.reason.displayLabel, // Assuming displayLabel exists
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: textSecondary),
              ),
            ),

            const SizedBox(height: 10.0),
            const Divider(color: dividerGray, thickness: 0.5, height: 1.0),
            const SizedBox(height: 10.0),

            // Action buttons
            Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 34.0,
                    child: OutlinedButton(
                      onPressed: onAccept,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: statusGreen,
                        side: const BorderSide(color: statusGreen),
                        padding: EdgeInsets.zero,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6.0)),
                      ),
                      child: Text(
                        "Accept",
                        style: Theme.of(context).textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w600), // SemiBold
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8.0),
                Expanded(
                  child: SizedBox(
                    height: 34.0,
                    child: OutlinedButton(
                      onPressed: onOverride,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: statusAmber,
                        side: const BorderSide(color: statusAmber),
                        padding: EdgeInsets.zero,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6.0)),
                      ),
                      child: Text(
                        "Override",
                        style: Theme.of(context).textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w600), // SemiBold
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8.0),
                Expanded(
                  child: SizedBox(
                    height: 34.0,
                    child: OutlinedButton(
                      onPressed: onRecapture,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: statusOrange,
                        side: const BorderSide(color: statusOrange),
                        padding: EdgeInsets.zero,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6.0)),
                      ),
                      child: Text(
                        "Recapture",
                        style: Theme.of(context).textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w600), // SemiBold
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}