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

// ── MediaQuery helper ────────────────────────────────────────────────────────

/// Screen size se responsive values. Fonts ko scale NAHI karta
/// (system text scale pehle se hota hai) — sirf spacing/icons/layout ke liye.
class _Responsive {
  final double width;
  final double scale; // spacing & icon scale (0.9 – 1.15)
  final bool isTablet;
  final double hPad; // page horizontal padding
  final double maxContentWidth;

  const _Responsive._({
    required this.width,
    required this.scale,
    required this.isTablet,
    required this.hPad,
    required this.maxContentWidth,
  });

  factory _Responsive.of(BuildContext context) {
    final double width = MediaQuery.sizeOf(context).width;
    final bool isTablet = width >= 600;
    return _Responsive._(
      width: width,
      scale: (width / 390).clamp(0.9, 1.15).toDouble(),
      isTablet: isTablet,
      hPad: (width * 0.04).clamp(12.0, 24.0).toDouble(),
      maxContentWidth: isTablet ? 720 : double.infinity,
    );
  }
}

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
    final mq = MediaQuery.of(context);

    // System text size ko 1.0x – 1.3x tak limit karo taaki layout na toote
    return MediaQuery(
      data: mq.copyWith(
        textScaler: mq.textScaler.clamp(minScaleFactor: 1.0, maxScaleFactor: 1.3),
      ),
      child: ListenableBuilder(
        listenable: _viewModel,
        builder: (context, _) {
          final r = _Responsive.of(context);
          final double keyboard = MediaQuery.viewInsetsOf(context).bottom;

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
                    // ── Tab row ────────────────────────────────────────────
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
                                    SizedBox(width: 4.0 * r.scale),
                                    Container(
                                      padding: EdgeInsets.symmetric(
                                        horizontal: 6.0 * r.scale,
                                        vertical: 1.0,
                                      ),
                                      decoration: BoxDecoration(
                                        color: institutionalBlue,
                                        borderRadius: BorderRadius.circular(8.0),
                                      ),
                                      child: Text(
                                        "${state.pendingItems.length}",
                                        style: Theme.of(context)
                                            .textTheme
                                            .labelSmall
                                            ?.copyWith(color: textOnBlue),
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
                                    SizedBox(width: 4.0 * r.scale),
                                    Container(
                                      padding: EdgeInsets.symmetric(
                                        horizontal: 6.0 * r.scale,
                                        vertical: 1.0,
                                      ),
                                      decoration: BoxDecoration(
                                        color: statusOrange,
                                        borderRadius: BorderRadius.circular(8.0),
                                      ),
                                      child: Text(
                                        "${state.disputedItems.length}",
                                        style: Theme.of(context)
                                            .textTheme
                                            .labelSmall
                                            ?.copyWith(color: textOnBlue),
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

                    // ── Content ────────────────────────────────────────────
                    Expanded(
                      child: items.isEmpty
                          ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.check_circle,
                                color: statusGreen, size: 48.0 * r.scale),
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
                          : Align(
                        alignment: Alignment.topCenter,
                        child: ConstrainedBox(
                          constraints: BoxConstraints(maxWidth: r.maxContentWidth),
                          child: ListView.separated(
                            padding: EdgeInsets.all(r.hPad),
                            itemCount: items.length,
                            separatorBuilder: (context, index) =>
                            const SizedBox(height: 8.0),
                            itemBuilder: (context, index) {
                              final item = items[index];
                              return _ReviewItemCard(
                                item: item,
                                onAccept: () => _viewModel.acceptReview(item.sampleId),
                                onOverride: () =>
                                    _viewModel.openOverrideDialog(item.sampleId),
                                onRecapture: () =>
                                    _viewModel.requestRecapture(item.sampleId),
                              );
                            },
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              // ── Override Dialog (Declarative modal overlay) ──────────────
              if (state.showOverrideDialog)
                Container(
                  color: Colors.black54, // Dim background
                  alignment: Alignment.center,
                  // Keyboard khulne par dialog upar uth jaye
                  padding: EdgeInsets.only(bottom: keyboard),
                  child: SingleChildScrollView(
                    child: AlertDialog(
                      backgroundColor: surfaceWhite,
                      insetPadding: EdgeInsets.symmetric(
                        horizontal: r.hPad + 8,
                        vertical: 24.0,
                      ),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12.0)),
                      title: Text(
                        "Override Grade",
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      content: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 480),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "Original system result is preserved. Override reason is mandatory.",
                              style: Theme.of(context)
                                  .textTheme
                                  .bodySmall
                                  ?.copyWith(color: textSecondary),
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
                              color: state.overrideReason.trim().isNotEmpty
                                  ? institutionalBlue
                                  : textSecondary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          );
        },
      ),
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

  // Button label: chhoti screen / bade font par bhi ek line me fit ho
  Widget _buttonLabel(BuildContext context, String text) {
    return FittedBox(
      fit: BoxFit.scaleDown,
      child: Text(
        text,
        maxLines: 1,
        style: Theme.of(context).textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w600),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final r = _Responsive.of(context);
    final double buttonHeight = 40.0 * r.scale;

    return Card(
      margin: EdgeInsets.zero,
      elevation: 1.0,
      color: surfaceWhite,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
      child: Padding(
        padding: EdgeInsets.all(12.0 * r.scale),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.sampleId,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: textPrimary,
                        ),
                      ),
                      Text(
                        item.farmerName,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(color: textSecondary),
                      ),
                      Text(
                        "${item.weightKg} kg",
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(color: textSecondary),
                      ),
                    ],
                  ),
                ),
                SizedBox(width: 8.0 * r.scale),
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
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(color: textSecondary),
                      ),
                    ],
                  ],
                ),
              ],
            ),
            const SizedBox(height: 6.0),

            // Reason Box
            Container(
              width: double.infinity,
              padding: EdgeInsets.all(6.0 * r.scale),
              decoration: BoxDecoration(
                color: backgroundGray,
                borderRadius: BorderRadius.circular(4.0),
              ),
              child: Text(
                item.reason.displayLabel, // Assuming displayLabel exists
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(color: textSecondary),
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
                    height: buttonHeight,
                    child: OutlinedButton(
                      onPressed: onAccept,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: statusGreen,
                        side: const BorderSide(color: statusGreen),
                        padding: const EdgeInsets.symmetric(horizontal: 4.0),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6.0)),
                      ),
                      child: _buttonLabel(context, "Accept"),
                    ),
                  ),
                ),
                SizedBox(width: 8.0 * r.scale),
                Expanded(
                  child: SizedBox(
                    height: buttonHeight,
                    child: OutlinedButton(
                      onPressed: onOverride,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: statusAmber,
                        side: const BorderSide(color: statusAmber),
                        padding: const EdgeInsets.symmetric(horizontal: 4.0),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6.0)),
                      ),
                      child: _buttonLabel(context, "Override"),
                    ),
                  ),
                ),
                SizedBox(width: 8.0 * r.scale),
                Expanded(
                  child: SizedBox(
                    height: buttonHeight,
                    child: OutlinedButton(
                      onPressed: onRecapture,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: statusOrange,
                        side: const BorderSide(color: statusOrange),
                        padding: const EdgeInsets.symmetric(horizontal: 4.0),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6.0)),
                      ),
                      child: _buttonLabel(context, "Recapture"),
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