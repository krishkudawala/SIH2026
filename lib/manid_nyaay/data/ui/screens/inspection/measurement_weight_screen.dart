import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';

const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color warnColor = Color(0xFFE65100);
const Color warnBg = Color(0xFFFFF3E0);
const Color warnBorder = Color(0xFFFFB74D);

/// Shared MediaQuery-based scale (1.0 at 375dp wide, clamped 0.85 - 1.3).
double _mqScale(BuildContext context) =>
    (MediaQuery.sizeOf(context).width / 375).clamp(0.85, 1.3);

class MeasurementWeightScreen extends StatelessWidget {
  final InspectionUiState uiState;
  final VoidCallback onProceed;
  final VoidCallback onBack;

  const MeasurementWeightScreen({
    super.key,
    required this.uiState,
    required this.onProceed,
    required this.onBack,
  });

  @override
  Widget build(BuildContext context) {
    // ── MediaQuery values ────────────────────────────────────────────────
    final Size size = MediaQuery.sizeOf(context);
    final double safeBottom = MediaQuery.paddingOf(context).bottom;
    final double scale = _mqScale(context);

    final double pagePadding = (size.width * 0.04).clamp(12.0, 24.0);
    final double cardPadding = 14.0 * scale;
    final double maxContentWidth = 600.0;
    final double buttonHeight = (48.0 * scale).clamp(48.0, 60.0);

    final double headFont = 12.0 * scale; // card headings
    final double tableFont = 11.0 * scale; // table + small notes
    final double footFont = 10.0 * scale; // footnote
    final double bigFont = 20.0 * scale; // prediction interval value
    final double shieldSize = 20.0 * scale;

    final meas = uiState.measurementData ?? {};
    final weight = uiState.weightData ?? {};
    final obs = uiState.rawObservations;

    final sizeStatus = (meas['size_status'] ?? 'ONION_DIAMETER_UNVALIDATED').toString();
    final massStatus = (weight['mass_status'] ?? 'UNVALIDATED').toString();
    final isCalibrated = massStatus == 'CALIBRATED';

    final declaredWeightKg = uiState.certifiedLotWeightKg;
    final weighbridgeVarianceKg = (weight['weighbridge_variance_kg'] as num?)?.toDouble();
    final hasVariance = declaredWeightKg > 0 && weighbridgeVarianceKg != null;

    final piLow = (weight['prediction_interval_low_g'] as num?)?.toDouble();
    final piHigh = (weight['prediction_interval_high_g'] as num?)?.toDouble();

    final TextStyle tableHeadStyle =
    TextStyle(fontSize: tableFont, fontWeight: FontWeight.bold, color: textSecondary);

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Measurement & Weight",
        subtitle: "Dimensional & Gravimetric Status",
        showBack: true,
        onBack: onBack,
      ),
      body: Align(
        alignment: Alignment.topCenter,
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: maxContentWidth),
          child: SingleChildScrollView(
            padding: EdgeInsets.fromLTRB(
              pagePadding,
              pagePadding,
              pagePadding,
              pagePadding + safeBottom,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Size status
                _SectionStatusCard(
                  label: "PHYSICAL DIAMETER",
                  status: sizeStatus,
                  description:
                  "Tri-axial dimensions (Major L, Minor W, Polar T) from segmentation contours. "
                      "Physical millimetric values are UNVALIDATED without an active ArUco "
                      "fiducial reference mat in frame.",
                  icon: Icons.straighten,
                ),
                const SizedBox(height: 14),

                // Per-observation dimension table from REAL backend data
                if (obs.isNotEmpty) ...[
                  Card(
                    elevation: 1.0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    color: surfaceWhite,
                    child: Padding(
                      padding: EdgeInsets.all(cardPadding),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "PER-OBSERVATION DIMENSIONAL REPORT",
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: headFont, color: textSecondary),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            "All values UNVALIDATED — no fiducial calibration detected.",
                            style: TextStyle(fontSize: tableFont, color: warnColor, fontWeight: FontWeight.w600),
                          ),
                          const SizedBox(height: 10),
                          Row(
                            children: [
                              Expanded(flex: 3, child: Text("Obs ID", style: tableHeadStyle)),
                              Expanded(flex: 2, child: Text("Class", style: tableHeadStyle)),
                              Expanded(flex: 2, child: Text("Size(mm)", style: tableHeadStyle)),
                              Expanded(flex: 2, child: Text("Wt(g)*", style: tableHeadStyle)),
                            ],
                          ),
                          const Divider(height: 8),
                          ...obs.take(12).map((o) {
                            final id = (o['id'] ?? '???').toString();
                            final shortId = id.length > 8 ? id.substring(0, 8) : id;
                            final cond = (o['condition'] ?? '?').toString();
                            final sizeMm = (o['size_mm'] as num?)?.toStringAsFixed(1) ?? '—';
                            final weightG = (o['weight_g'] as num?)?.toStringAsFixed(1) ?? '—';
                            return Padding(
                              padding: const EdgeInsets.symmetric(vertical: 3),
                              child: Row(
                                children: [
                                  Expanded(flex: 3, child: Text(shortId, style: TextStyle(fontSize: tableFont, fontFamily: 'monospace', color: institutionalBlue))),
                                  Expanded(flex: 2, child: Text(cond, style: TextStyle(fontSize: tableFont))),
                                  Expanded(flex: 2, child: Text(sizeMm, style: TextStyle(fontSize: tableFont))),
                                  Expanded(flex: 2, child: Text(weightG, style: TextStyle(fontSize: tableFont))),
                                ],
                              ),
                            );
                          }),
                          if (obs.length > 12)
                            Text("… and ${obs.length - 12} more",
                                style: TextStyle(fontSize: tableFont, color: textSecondary)),
                          const SizedBox(height: 4),
                          Text(
                            "* Weight is UNVALIDATED model estimate, not physical scale reading.",
                            style: TextStyle(fontSize: footFont, color: warnColor),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                ],

                // Weighbridge variance card — only if declared weight exists
                if (declaredWeightKg > 0) ...[
                  Card(
                    elevation: 1.0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    color: surfaceWhite,
                    child: Padding(
                      padding: EdgeInsets.all(cardPadding),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "WEIGHBRIDGE RECORD — REVIEW SIGNAL",
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: headFont, color: textSecondary),
                          ),
                          const SizedBox(height: 6),
                          _DataRow(label: "Declared/Certified Weight", value: "${declaredWeightKg.toStringAsFixed(1)} kg"),
                          if (hasVariance)
                            _DataRow(
                              label: "Weighbridge Variance",
                              value: "${weighbridgeVarianceKg.toStringAsFixed(1)} kg",
                              highlight: weighbridgeVarianceKg.abs() > 50,
                            ),
                          const SizedBox(height: 6),
                          Text(
                            "Variance is a REVIEW SIGNAL only. Never labeled as fraud.",
                            style: TextStyle(fontSize: tableFont, color: warnColor, fontWeight: FontWeight.w600),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                ],

                // Mass status
                _SectionStatusCard(
                  label: "MASS & WEIGHT STATUS",
                  status: "MASS: $massStatus",
                  description: isCalibrated
                      ? "Weight model is calibrated with physical scale data."
                      : "Gravimetric mass estimation is UNVALIDATED. "
                      "No paired digital scale calibration exists. "
                      "Mandi Nyaay will never invent or fabricate mass estimates.",
                  icon: Icons.scale,
                  isWarning: !isCalibrated,
                ),
                const SizedBox(height: 14),

                // Prediction interval — only when calibrated
                if (isCalibrated && piLow != null && piHigh != null) ...[
                  Card(
                    color: const Color(0xFFE8F5E9),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                      side: const BorderSide(color: Color(0xFFA5D6A7)),
                    ),
                    child: Padding(
                      padding: EdgeInsets.all(cardPadding),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text("PREDICTION INTERVAL (CALIBRATED)",
                              style: TextStyle(fontSize: headFont, fontWeight: FontWeight.bold, color: const Color(0xFF2E7D32))),
                          const SizedBox(height: 6),
                          Text("${piLow.toStringAsFixed(1)} g — ${piHigh.toStringAsFixed(1)} g",
                              style: TextStyle(fontSize: bigFont, fontWeight: FontWeight.bold, color: const Color(0xFF1B5E20))),
                          Text("Conformal prediction interval at configured coverage target.",
                              style: TextStyle(fontSize: tableFont, color: const Color(0xFF388E3C))),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                ],

                // Statutory guarantee banner
                Container(
                  padding: EdgeInsets.all(cardPadding),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE8F5E9),
                    borderRadius: BorderRadius.circular(8.0),
                    border: Border.all(color: const Color(0xFFA5D6A7)),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.shield, color: const Color(0xFF2E7D32), size: shieldSize),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          "Mandi Nyaay Strict Truthfulness Policy: Uncalibrated dimensions and masses are never disguised as verified numbers.",
                          style: TextStyle(fontSize: tableFont, color: const Color(0xFF1B5E20), fontWeight: FontWeight.w600),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                ElevatedButton(
                  onPressed: onProceed,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: institutionalBlue,
                    foregroundColor: textOnBlue,
                    minimumSize: Size(double.infinity, buttonHeight),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  child: const Text("PROCEED TO REVIEW QUEUE", style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _SectionStatusCard extends StatelessWidget {
  final String label;
  final String status;
  final String description;
  final IconData icon;
  final bool isWarning;

  const _SectionStatusCard({
    required this.label,
    required this.status,
    required this.description,
    required this.icon,
    this.isWarning = true,
  });

  @override
  Widget build(BuildContext context) {
    final double scale = _mqScale(context);

    final bg = isWarning ? warnBg : const Color(0xFFE8F5E9);
    final border = isWarning ? warnBorder : const Color(0xFFA5D6A7);
    final textColor = isWarning ? warnColor : const Color(0xFF2E7D32);

    return Card(
      elevation: 2.0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      color: surfaceWhite,
      child: Padding(
        padding: EdgeInsets.all(16.0 * scale),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // Expanded/Flexible so long label + long status never overflow
                Expanded(
                  child: Row(children: [
                    Icon(icon, size: 18 * scale, color: textSecondary),
                    const SizedBox(width: 6),
                    Flexible(
                      child: Text(label,
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13 * scale, color: textSecondary)),
                    ),
                  ]),
                ),
                const SizedBox(width: 8),
                Flexible(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: bg,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: border),
                    ),
                    child: Text(status,
                        style: TextStyle(color: textColor, fontWeight: FontWeight.bold, fontSize: 11 * scale)),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(description, style: TextStyle(fontSize: 12 * scale, color: textSecondary)),
          ],
        ),
      ),
    );
  }
}

class _DataRow extends StatelessWidget {
  final String label;
  final String value;
  final bool highlight;
  const _DataRow({required this.label, required this.value, this.highlight = false});

  @override
  Widget build(BuildContext context) {
    final double scale = _mqScale(context);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Text(label, style: TextStyle(fontSize: 12 * scale, color: textSecondary)),
          ),
          const SizedBox(width: 8),
          Text(value,
              style: TextStyle(
                fontSize: 12 * scale,
                fontWeight: FontWeight.bold,
                color: highlight ? Colors.red : textPrimary,
              )),
        ],
      ),
    );
  }
}