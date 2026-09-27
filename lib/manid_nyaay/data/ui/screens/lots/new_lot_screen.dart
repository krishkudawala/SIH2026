import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/chevron_row.dart';

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

  @override
  void initState() {
    super.initState();
    // Add listeners to trigger a rebuild when text changes, allowing the
    // "GENERATE SAMPLING PLAN" button to enable/disable dynamically.
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
                      onPressed: isFormValid ? () => context.pop() : null,
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