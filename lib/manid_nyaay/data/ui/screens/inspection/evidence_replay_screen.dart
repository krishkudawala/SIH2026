import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';

const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color statusGreen = Color(0xFF4CAF50);

class EvidenceReplayScreen extends StatelessWidget {
  final InspectionUiState uiState;
  final VoidCallback onProceed;
  final VoidCallback onBack;
  final VoidCallback onOpenDispute;

  const EvidenceReplayScreen({
    super.key,
    required this.uiState,
    required this.onProceed,
    required this.onBack,
    required this.onOpenDispute,
  });

  @override
  Widget build(BuildContext context) {
    // ── MediaQuery values ────────────────────────────────────────────────
    final Size size = MediaQuery.sizeOf(context);
    final double safeBottom = MediaQuery.paddingOf(context).bottom;
    final double scale = (size.width / 375).clamp(0.85, 1.3);

    final double pagePadding = (size.width * 0.04).clamp(12.0, 24.0);
    final double cardPadding = 16.0 * scale;
    final double maxContentWidth = 600.0;
    final double iconSize = 28.0 * scale;
    final double smallIconSize = 20.0 * scale;
    final double buttonHeight = (48.0 * scale).clamp(48.0, 60.0);
    final double outlinedButtonHeight = (44.0 * scale).clamp(44.0, 56.0);

    final evidence = uiState.evidenceData ?? {};
    final replay = uiState.replayData ?? {};

    final rootHash = (evidence['evidence_root_hash'] ?? '0' * 64).toString();
    final events = (evidence['events'] as List<dynamic>?) ?? [];
    final isIdentical = replay['is_bit_for_bit_identical'] == true;
    final recomputedHash = (replay['recomputed_root_hash'] ?? rootHash).toString();

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Evidence & Replay Parity",
        subtitle: "SHA-256 Tamper-Evident Ledger",
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
                // Replay Verification Banner
                Card(
                  elevation: 2.0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  color: surfaceWhite,
                  child: SizedBox(
                    width: double.infinity,
                    child: Padding(
                      padding: EdgeInsets.all(cardPadding),
                      child: Column(
                        children: [
                          Row(
                            children: [
                              Icon(
                                isIdentical ? Icons.verified : Icons.warning_amber,
                                color: isIdentical ? statusGreen : Colors.red,
                                size: iconSize,
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      isIdentical ? "BIT-FOR-BIT REPLAY VERIFIED" : "REPLAY PARITY UNVERIFIED",
                                      style: TextStyle(
                                        fontWeight: FontWeight.bold,
                                        fontSize: 14 * scale,
                                        color: isIdentical ? statusGreen : Colors.red,
                                      ),
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      isIdentical
                                          ? "Deterministic replay matched stored SHA-256 evidence tree."
                                          : "Replay hash does not match original chain.",
                                      style: TextStyle(fontSize: 12 * scale, color: textSecondary),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 14),

                // Root Hash Card
                Card(
                  elevation: 1.0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  color: surfaceWhite,
                  child: SizedBox(
                    width: double.infinity,
                    child: Padding(
                      padding: EdgeInsets.all(cardPadding),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "EVIDENCE ROOT DIGEST",
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12 * scale, color: textSecondary),
                          ),
                          const SizedBox(height: 8),
                          Container(
                            width: double.infinity,
                            padding: EdgeInsets.all(10 * scale),
                            decoration: BoxDecoration(
                              color: const Color(0xFFF8FAFC),
                              borderRadius: BorderRadius.circular(6),
                              border: Border.all(color: const Color(0xFFE2E8F0)),
                            ),
                            child: SelectableText(
                              rootHash,
                              style: TextStyle(fontFamily: 'monospace', fontSize: 11 * scale, color: institutionalBlue),
                            ),
                          ),
                          const SizedBox(height: 8),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Flexible(
                                child: Text(
                                  "Ledger Events: ${events.length}",
                                  style: TextStyle(fontSize: 12 * scale, fontWeight: FontWeight.bold),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Flexible(
                                child: Text(
                                  "Algorithm: SHA-256",
                                  textAlign: TextAlign.end,
                                  style: TextStyle(fontSize: 12 * scale, color: textSecondary),
                                ),
                              ),
                            ],
                          ),
                          if (recomputedHash != rootHash)
                            Padding(
                              padding: const EdgeInsets.only(top: 6.0),
                              child: Text(
                                "Recomputed: $recomputedHash",
                                style: TextStyle(fontSize: 10 * scale, color: Colors.red),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 14),

                // Mandatory disclaimer
                Container(
                  padding: EdgeInsets.all(12.0 * scale),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFF8E1),
                    borderRadius: BorderRadius.circular(8.0),
                    border: Border.all(color: const Color(0xFFFFE082)),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.lock_clock, color: const Color(0xFFF57C00), size: smallIconSize),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          "Truthfulness Notice: Evidence chain is tamper-evident and replayable, not tamper-proof. Physical bag identity is not independently verified.",
                          style: TextStyle(fontSize: 11 * scale, color: const Color(0xFFE65100), fontWeight: FontWeight.w600),
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
                  child: const Text(
                    "GENERATE OFFICIAL MANDI REPORT & RECEIPT",
                    textAlign: TextAlign.center,
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
                const SizedBox(height: 10),

                OutlinedButton.icon(
                  onPressed: onOpenDispute,
                  icon: const Icon(Icons.gavel_outlined, color: Color(0xFFE65100)),
                  label: const Text(
                    "CHALLENGE LOT / OPEN DISPUTE",
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Color(0xFFE65100), fontWeight: FontWeight.bold),
                  ),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Color(0xFFFFA000)),
                    minimumSize: Size(double.infinity, outlinedButtonHeight),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
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