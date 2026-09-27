import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/inspection_session.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/onion_record.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';

// --- Theme Colors Placeholder ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color blueLight = Color(0xFFE1F5FE);
const Color institutionalBlue = Color(0xFF1565C0);
const Color textSecondary = Color(0xFF64748B);
const Color textPrimary = Color(0xFF1E293B);
const Color surfaceWhite = Colors.white;
const Color statusAmberLight = Color(0xFFFFF8E1);
const Color statusAmber = Color(0xFFFFA000);
const Color statusGreen = Color(0xFF4CAF50);
const Color textHint = Color(0xFF94A3B8);
const Color textOnBlue = Colors.white;

class CrossViewScreen extends StatelessWidget {
  final InspectionUiState uiState;
  final VoidCallback onConfirm;
  final VoidCallback onBack;

  const CrossViewScreen({
    super.key,
    required this.uiState,
    required this.onConfirm,
    required this.onBack,
  });

  @override
  Widget build(BuildContext context) {
    final fixtureOnions = List.generate(8, (index) {
      final idx = index + 1;
      final isUncertain = idx == 4;

      return (
      "Onion #${idx.toString().padLeft(2, '0')}",
      isUncertain ? CorrespondenceStatus.uncertain : CorrespondenceStatus.confirmed,
      [
        CaptureOrientation.top,
        CaptureOrientation.side,
        if (!isUncertain) CaptureOrientation.underside
      ],
      );
    });

    final subtitle = uiState.selectedBag != null
        ? "BAG ${uiState.selectedBag!.bagNumber} · ${uiState.selectedBag!.tier.displayLabel}"
        : "";

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Cross-View Correspondence",
        subtitle: subtitle,
        showBack: true,
        onBack: onBack,
      ),
      body: Padding(
        padding: const EdgeInsets.all(14.0),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(12.0),
              decoration: BoxDecoration(
                color: blueLight,
                borderRadius: BorderRadius.circular(8.0),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.info, color: institutionalBlue, size: 18.0),
                  const SizedBox(width: 8.0),
                  Expanded(
                    child: Text(
                      "Verify that each onion identity is consistent across Top, Side and Underside captures. If correspondence is uncertain, it will be routed to the Review queue.",
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: textSecondary,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12.0),

            Expanded(
              child: ListView.separated(
                itemCount: fixtureOnions.length,
                separatorBuilder: (context, index) => const SizedBox(height: 6.0),
                itemBuilder: (context, index) {
                  final (label, status, views) = fixtureOnions[index];
                  final isUncertain = status == CorrespondenceStatus.uncertain;

                  return Card(
                    margin: EdgeInsets.zero,
                    elevation: 1.0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
                    color: isUncertain ? statusAmberLight : surfaceWhite,
                    child: Padding(
                      padding: const EdgeInsets.all(12.0),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                label,
                                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                                  fontWeight: FontWeight.w600,
                                  color: textPrimary,
                                ),
                              ),
                              const SizedBox(height: 4.0),
                              Row(
                                children: CaptureOrientation.values.map((orientation) {
                                  final captured = views.contains(orientation);
                                  return Padding(
                                    padding: const EdgeInsets.only(right: 8.0),
                                    child: Text(
                                      "${orientation.displayLabel.substring(0, 3)} ${captured ? "✓" : "–"}",
                                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                        color: captured ? statusGreen : textHint,
                                      ),
                                    ),
                                  );
                                }).toList(),
                              ),
                            ],
                          ),
                          if (isUncertain)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6.0, vertical: 3.0),
                              decoration: BoxDecoration(
                                color: statusAmberLight,
                                borderRadius: BorderRadius.circular(4.0),
                              ),
                              child: Row(
                                children: [
                                  const Icon(Icons.warning, color: statusAmber, size: 12.0),
                                  const SizedBox(width: 4.0),
                                  Text(
                                    "Uncertain",
                                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                      color: statusAmber,
                                    ),
                                  ),
                                ],
                              ),
                            )
                          else
                            const Icon(Icons.check_circle, color: statusGreen, size: 22.0),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 12.0),

            SizedBox(
              width: double.infinity,
              height: 48.0,
              child: ElevatedButton(
                onPressed: onConfirm,
                style: ElevatedButton.styleFrom(
                  backgroundColor: institutionalBlue,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8.0),
                  ),
                ),
                child: Text(
                  "CONFIRM & VIEW PER-ONION RESULTS",
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: textOnBlue,
                    fontWeight: FontWeight.bold,
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
