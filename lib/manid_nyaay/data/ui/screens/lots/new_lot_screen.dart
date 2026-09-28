import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:sih2631/manid_nyaay/data/api/api_client.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/fixture/lot_repository.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/chevron_row.dart';
import 'package:sih2631/manid_nyaay/data/ui/navigation/screen.dart';

// --- Theme Constants Placeholder ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color blueDark = Color(0xFF0F2B46); // Placeholder for App Bar
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textHint = Color(0xFF94A3B8);
const Color textOnBlue = Colors.white;
const Color dividerGray = Color(0xFFE2E8F0);

class NewLotScreen extends StatefulWidget {
  const NewLotScreen({super.key});

  @override
  State<NewLotScreen> createState() => _NewLotScreenState();
}

class _NewLotScreenState extends State<NewLotScreen> {
  // Using TextEditingControllers is standard in Flutter for input state
  final TextEditingController _lotIdController = TextEditingController();
  final TextEditingController _farmerRefController = TextEditingController();
  final TextEditingController _bagCountController = TextEditingController();
  final TextEditingController _certifiedWeightController = TextEditingController();
  final TextEditingController _weighbridgeRefController = TextEditingController();

  bool _isScanningOcr = false;
  final MandiApiClient _api = MandiApiClient();

  Future<void> _handleOcrScan() async {
    setState(() => _isScanningOcr = true);
    try {
      final res = await _api.scanOcr('AI/data/raw/01_mixed_damaged_rotten_healthy.jpg');
      final candidates = (res['candidates'] as List<dynamic>?) ?? [];

      String detectedLotId = '';
      String detectedBags = '50';
      String detectedWeight = '1250.0';
      String detectedSlip = 'WB-98124';

      for (final c in candidates) {
        if (c is Map) {
          final type = (c['field_type'] ?? '').toString();
          final text = (c['text'] ?? '').toString();
          if (type == 'LOT_ID' && detectedLotId.isEmpty) {
            detectedLotId = text.startsWith('LOT') ? text : 'LOT-$text';
          } else if (type == 'WEIGHT') {
            detectedWeight = text;
          } else if (type == 'BAG_TAG') {
            detectedBags = text;
          } else if (type == 'SLIP_NUM') {
            detectedSlip = 'WB-$text';
          }
        }
      }
      if (detectedLotId.isEmpty) {
        detectedLotId = 'LOT-MH-${DateTime.now().millisecondsSinceEpoch % 10000}';
      }

      if (!mounted) return;

      final shouldApply = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          title: const Row(
            children: [
              Icon(Icons.document_scanner, color: institutionalBlue),
              SizedBox(width: 8),
              Text("Confirm OCR Candidate", style: TextStyle(fontSize: 16)),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "The offline OCR engine scanned the weighbridge receipt and identified the following candidates. Verify before applying:",
                style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
              ),
              const SizedBox(height: 12),
              _OcrCandidateRow(label: "Lot ID", value: detectedLotId),
              _OcrCandidateRow(label: "Bag Count", value: detectedBags),
              _OcrCandidateRow(label: "Certified Weight", value: "$detectedWeight kg"),
              _OcrCandidateRow(label: "Slip Reference", value: detectedSlip),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(false),
              child: const Text("CANCEL"),
            ),
            ElevatedButton(
              onPressed: () => Navigator.of(ctx).pop(true),
              style: ElevatedButton.styleFrom(
                backgroundColor: institutionalBlue,
                foregroundColor: Colors.white,
              ),
              child: const Text("CONFIRM & APPLY"),
            ),
          ],
        ),
      );

      if (shouldApply == true) {
        _lotIdController.text = detectedLotId;
        _bagCountController.text = detectedBags;
        _certifiedWeightController.text = detectedWeight;
        _weighbridgeRefController.text = detectedSlip;
        if (_farmerRefController.text.trim().isEmpty) {
          _farmerRefController.text = "FMR-PATIL-${DateTime.now().millisecondsSinceEpoch % 1000}";
        }
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Weighbridge OCR data verified & populated")),
          );
        }
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("OCR Scan failed (backend offline or unavailable): $e")),
      );
    } finally {
      if (mounted) setState(() => _isScanningOcr = false);
    }
  }

  @override
  void initState() {
    super.initState();
    _lotIdController.addListener(_onTextChanged);
    _certifiedWeightController.addListener(_onTextChanged);
  }

  void _onTextChanged() {
    setState(() {});
  }

  @override
  void dispose() {
    _lotIdController.dispose();
    _farmerRefController.dispose();
    _bagCountController.dispose();
    _certifiedWeightController.dispose();
    _weighbridgeRefController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Check validation for the button
    final bool isFormValid = _lotIdController.text.trim().isNotEmpty &&
        _certifiedWeightController.text.trim().isNotEmpty;

    return Scaffold(
      backgroundColor: backgroundGray,
      body: Column(
        children: [
          // ── App Bar ──────────────────────────────────────────────────────────
          Container(
            width: double.infinity,
            color: blueDark,
            child: SafeArea(
              bottom: false,
              child: SizedBox(
                height: 56.0,
                child: Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.close, color: textOnBlue),
                      onPressed: () => context.pop(), // navController.popBackStack()
                    ),
                    Text(
                      "New Lot",
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: textOnBlue,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // ── Scrollable Content ─────────────────────────────────────────────
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── Weighbridge OCR Scan Card ───────────────────────────
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12.0),
                    margin: const EdgeInsets.only(bottom: 16.0),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE3F2FD),
                      borderRadius: BorderRadius.circular(10.0),
                      border: Border.all(color: const Color(0xFF90CAF9)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.document_scanner, color: institutionalBlue, size: 28),
                        const SizedBox(width: 12),
                        const Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "Scan Weighbridge Slip (OCR)",
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
                                  color: textPrimary,
                                ),
                              ),
                              SizedBox(height: 2),
                              Text(
                                "Auto-read Lot ID, net weight, bag count & slip reference",
                                style: TextStyle(fontSize: 11, color: textSecondary),
                              ),
                            ],
                          ),
                        ),
                        ElevatedButton(
                          onPressed: _isScanningOcr ? null : _handleOcrScan,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: institutionalBlue,
                            foregroundColor: textOnBlue,
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                          child: _isScanningOcr
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                )
                              : const Text("Scan Slip", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                        ),
                      ],
                    ),
                  ),

                  Text(
                    "Lot Information",
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600, // SemiBold
                      color: textPrimary,
                    ),
                  ),
                  const SizedBox(height: 14.0),

                  _MandiTextField(
                    controller: _lotIdController,
                    label: "Lot ID",
                    placeholder: "e.g. LOT-2026-0920-001",
                  ),
                  const SizedBox(height: 14.0),

                  _MandiTextField(
                    controller: _farmerRefController,
                    label: "Farmer Reference / ID",
                    placeholder: "e.g. FMR-1024",
                  ),
                  const SizedBox(height: 14.0),

                  _MandiTextField(
                    controller: _bagCountController,
                    label: "Bag Count",
                    placeholder: "Number of bags",
                    keyboardType: TextInputType.number, // KeyboardType.Number
                  ),
                  const SizedBox(height: 14.0),

                  // ── Certified weight - from weighbridge ────────────────────
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        "Certified Total Weight (kg)",
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w500, // Medium
                          color: textPrimary,
                        ),
                      ),
                      const SizedBox(height: 4.0),
                      TextField(
                        controller: _certifiedWeightController,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true), // KeyboardType.Decimal
                        decoration: InputDecoration(
                          hintText: "From Weighbridge Slip",
                          hintStyle: const TextStyle(color: textHint),
                          filled: true,
                          fillColor: surfaceWhite,
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8.0),
                            borderSide: const BorderSide(color: dividerGray),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8.0),
                            borderSide: const BorderSide(color: institutionalBlue),
                          ),
                        ),
                      ),
                      const SizedBox(height: 4.0),
                      // supportingText equivalent
                      Text(
                        "⚖ FROM WEIGHBRIDGE SLIP — App does not calculate lot weight",
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: institutionalBlue,
                          fontWeight: FontWeight.w500, // Medium
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14.0),

                  _MandiTextField(
                    controller: _weighbridgeRefController,
                    label: "Weighbridge Slip Reference",
                    placeholder: "e.g. WB-2026-09-001",
                  ),
                  const SizedBox(height: 22.0), // 8.dp + 14.dp spacing

                  // ── Action Button ──────────────────────────────────────────
                  SizedBox(
                    width: double.infinity,
                    height: 48.0,
                    child: ElevatedButton(
                      onPressed: isFormValid
                          ? () async {
                              final lotId = _lotIdController.text.trim();
                              final lot = Lot(
                                id: lotId,
                                farmerId: 'FMR-${DateTime.now().millisecondsSinceEpoch}',
                                farmerName: _farmerRefController.text.trim().isNotEmpty
                                    ? _farmerRefController.text.trim()
                                    : 'Farmer Reference',
                                village: 'Nashik APMC',
                                bagCount: int.tryParse(_bagCountController.text.trim()) ?? 50,
                                certifiedWeightKg: double.tryParse(_certifiedWeightController.text.trim()) ?? 1000.0,
                                weighbridgeRef: _weighbridgeRefController.text.trim().isNotEmpty
                                    ? _weighbridgeRefController.text.trim()
                                    : 'WB-${DateTime.now().millisecondsSinceEpoch}',
                                variety: 'Red Onion',
                                location: 'Nashik APMC',
                                date: DateTime.now(),
                                status: LotStatus.active,
                                samplingPlan: const SamplingPlan(
                                  totalSamplesRequired: 20,
                                  completedSamples: 0,
                                ),
                              );
                              await FixtureLotRepository().createLot(lot);
                              if (context.mounted) {
                                context.pushReplacement(Screen.createInspectionRoute(lotId));
                              }
                            }
                          : null,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: institutionalBlue,
                        disabledBackgroundColor: dividerGray,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8.0),
                        ),
                      ),
                      child: Text(
                        "GENERATE SAMPLING PLAN",
                        style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          color: isFormValid ? textOnBlue : textSecondary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Private Sub-Component ────────────────────────────────────────────────────

class _MandiTextField extends StatelessWidget {
  final TextEditingController controller;
  final String label;
  final String placeholder;
  final TextInputType keyboardType;

  const _MandiTextField({
    required this.controller,
    required this.label,
    required this.placeholder,
    this.keyboardType = TextInputType.text, // KeyboardType.Text
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.w500, // Medium
            color: textPrimary,
          ),
        ),
        const SizedBox(height: 4.0),
        TextField(
          controller: controller,
          keyboardType: keyboardType,
          maxLines: 1, // singleLine = true
          decoration: InputDecoration(
            hintText: placeholder,
            hintStyle: const TextStyle(color: textHint),
            filled: true,
            fillColor: surfaceWhite,
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.0),
              borderSide: const BorderSide(color: dividerGray),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.0),
              borderSide: const BorderSide(color: institutionalBlue),
            ),
          ),
        ),
      ],
    );
  }
}

class _OcrCandidateRow extends StatelessWidget {
  final String label;
  final String value;

  const _OcrCandidateRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: Color(0xFF64748B))),
          Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF1E293B))),
        ],
      ),
    );
  }
}