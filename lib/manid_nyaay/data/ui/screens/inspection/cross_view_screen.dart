import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/inspection_session.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';

const Color backgroundGray = Color(0xFFF4F5F7);
const Color blueLight = Color(0xFFE1F5FE);
const Color institutionalBlue = Color(0xFF1565C0);
const Color textSecondary = Color(0xFF64748B);
const Color textPrimary = Color(0xFF1E293B);
const Color surfaceWhite = Colors.white;
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
    // ── MediaQuery values ────────────────────────────────────────────────
    final Size size = MediaQuery.sizeOf(context);
    final double safeBottom = MediaQuery.paddingOf(context).bottom;
    final double scale = (size.width / 375).clamp(0.85, 1.3);

    final double pagePadding = (size.width * 0.04).clamp(12.0, 24.0);
    final double cardPadding = 14.0 * scale;
    final double infoIconSize = 18.0 * scale;
    final double statusIconSize = 24.0 * scale;
    final double badgeFontSize = 10.0 * scale;
    final double descFontSize = 11.5 * scale;
    final double buttonHeight = (48.0 * scale).clamp(48.0, 60.0);
    final double maxContentWidth = 600.0;

    final completed = uiState.completedOrientations;
    final bag = uiState.selectedBag;
    final subtitle = bag != null ? "BAG ${bag.bagNumber} · ${bag.tier.displayLabel}" : "";

    final views = [
      (
      CaptureOrientation.top,
      "Top View (Primary Sample Mat)",
      "Planar detection for produce counting, diameter measurement & major surface defect segmentation.",
      completed.contains(CaptureOrientation.top),
      ),
      (
      CaptureOrientation.side,
      "Side View (Equatorial Profile)",
      "Profile view for equatorial thickness and lateral defect observation.",
      completed.contains(CaptureOrientation.side),
      ),
      (
      CaptureOrientation.underside,
      "Underside View (Basal Plate & Root)",
      "Basal view for root rot, sprouting initiation and basal decay detection.",
      completed.contains(CaptureOrientation.underside),
      ),
    ];

    final hasPrimary = completed.contains(CaptureOrientation.top) || completed.isNotEmpty;

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Multi-Angle Correspondence",
        subtitle: subtitle,
        showBack: true,
        onBack: onBack,
      ),
      body: Align(
        alignment: Alignment.topCenter,
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: maxContentWidth),
          child: Padding(
            padding: EdgeInsets.fromLTRB(
              pagePadding,
              pagePadding,
              pagePadding,
              pagePadding + safeBottom,
            ),
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
                      Icon(Icons.info, color: institutionalBlue, size: infoIconSize),
                      const SizedBox(width: 8.0),
                      Expanded(
                        child: Text(
                          "Review captured angles before triggering ONNX neural inference. All multi-angle captures are hashed and linked to this active session.",
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
                    itemCount: views.length,
                    separatorBuilder: (context, index) => const SizedBox(height: 8.0),
                    itemBuilder: (context, index) {
                      final (orientation, title, desc, isCaptured) = views[index];

                      return Card(
                        margin: EdgeInsets.zero,
                        elevation: 1.0,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
                        color: surfaceWhite,
                        child: Padding(
                          padding: EdgeInsets.all(cardPadding),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(
                                isCaptured ? Icons.check_circle : Icons.radio_button_unchecked,
                                color: isCaptured ? statusGreen : textHint,
                                size: statusIconSize,
                              ),
                              const SizedBox(width: 12.0),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        // Expanded so a long title wraps instead of overflowing
                                        Expanded(
                                          child: Text(
                                            title,
                                            style: Theme.of(context).textTheme.labelLarge?.copyWith(
                                              fontWeight: FontWeight.bold,
                                              color: textPrimary,
                                            ),
                                          ),
                                        ),
                                        const SizedBox(width: 8.0),
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 2.0),
                                          decoration: BoxDecoration(
                                            color: isCaptured ? const Color(0xFFE8F5E9) : const Color(0xFFF1F5F9),
                                            borderRadius: BorderRadius.circular(4.0),
                                          ),
                                          child: Text(
                                            isCaptured ? "UPLOADED" : "PENDING",
                                            style: TextStyle(
                                              fontSize: badgeFontSize,
                                              fontWeight: FontWeight.bold,
                                              color: isCaptured ? statusGreen : textSecondary,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 4.0),
                                    Text(
                                      desc,
                                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                        color: textSecondary,
                                        fontSize: descFontSize,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
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
                  height: buttonHeight,
                  child: ElevatedButton.icon(
                    onPressed: hasPrimary ? onConfirm : null,
                    icon: const Icon(Icons.analytics_outlined),
                    label: const Text(
                      "EXECUTE REAL ONNX INFERENCE",
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: institutionalBlue,
                      foregroundColor: textOnBlue,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8.0),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}