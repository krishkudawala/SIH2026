import 'dart:math';
import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/inspection_session.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';

// --- Theme Constants Placeholder ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color blueLight = Color(0xFFE1F5FE);
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color dividerGray = Color(0xFFE2E8F0);
const Color statusGreenLight = Color(0xFFE8F5E9);
const Color statusGreen = Color(0xFF4CAF50);

class SourceSelectionScreen extends StatefulWidget {
  final InspectionUiState uiState;
  final void Function(int, BagTier) onBagSelected;
  final VoidCallback onBack;

  const SourceSelectionScreen({
    super.key,
    required this.uiState,
    required this.onBagSelected,
    required this.onBack,
  });

  @override
  State<SourceSelectionScreen> createState() => _SourceSelectionScreenState();
}

class _SourceSelectionScreenState extends State<SourceSelectionScreen> {
  int? _selectedBagNum;
  BagTier _selectedTier = BagTier.middle;

  // Returns how many bags to sample from a lot of size n
  int _computeSampleBagCount(int n) {
    final sq = sqrt(n.toDouble()).ceil();
    return sq.clamp(4, 10);
  }

  // Generate spread-out bag numbers across the lot
  List<int> _generateSpreadBags(int n, int k) {
    final rng = Random();
    final step = n ~/ k;
    return List.generate(k, (i) {
      final base = i * step + 1;
      final jitter = rng.nextInt(step.clamp(1, step));
      return (base + jitter).clamp(1, n);
    });
  }

  @override
  Widget build(BuildContext context) {
    // ── MediaQuery values ────────────────────────────────────────────────
    final Size size = MediaQuery.sizeOf(context);
    final double safeBottom = MediaQuery.paddingOf(context).bottom;
    final double scale = (size.width / 375).clamp(0.85, 1.3);

    final double pagePadding = (size.width * 0.04).clamp(12.0, 24.0);
    final double tileSize = (size.width * 0.115).clamp(44.0, 64.0);
    final double buttonHeight = (48.0 * scale).clamp(48.0, 60.0);
    final double iconSize = 18.0 * scale;
    final double checkIconSize = 20.0 * scale;
    final double maxContentWidth = 600.0;

    // Compute suggested bag numbers from the real declared bag count.
    // AGMARK guidance: inspect ≥5 bags or sqrt(N) bags, min 4, max 10.
    final n = widget.uiState.declaredBagCount;
    final List<int> bagNumbers;
    if (n > 0) {
      final sampleSize = _computeSampleBagCount(n);
      final rng = n > 10 ? _generateSpreadBags(n, sampleSize) : List.generate(n, (i) => i + 1);
      bagNumbers = rng.take(sampleSize).toList()..sort();
    } else {
      bagNumbers = [1, 2, 3, 4]; // fallback if bag count unknown
    }

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Select Source Bag",
        subtitle: widget.uiState.lotId,
        showBack: true,
        onBack: widget.onBack,
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
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Card(
                  margin: EdgeInsets.zero,
                  elevation: 0.0,
                  color: blueLight,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8.0),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.info, color: institutionalBlue, size: iconSize),
                        const SizedBox(width: 8.0),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "SELECT SOURCE BAG",
                                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: institutionalBlue,
                                ),
                              ),
                              Text(
                                "Physically locate the bag and select its position below. The inspector selects the bag — the app does not choose automatically.",
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: textSecondary,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12.0),

                Text(
                  "Bag Number",
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w500,
                    color: textPrimary,
                  ),
                ),
                const SizedBox(height: 12.0),
                // Wrap instead of Row so up to 10 tiles never overflow
                Wrap(
                  spacing: 8.0,
                  runSpacing: 8.0,
                  children: bagNumbers.map((bag) {
                    final isSelected = _selectedBagNum == bag;
                    return GestureDetector(
                      onTap: () {
                        setState(() {
                          _selectedBagNum = bag;
                        });
                      },
                      child: Container(
                        width: tileSize,
                        height: tileSize,
                        decoration: BoxDecoration(
                          color: isSelected ? institutionalBlue : surfaceWhite,
                          borderRadius: BorderRadius.circular(8.0),
                          border: Border.all(
                            color: isSelected ? institutionalBlue : dividerGray,
                            width: 1.0,
                          ),
                        ),
                        alignment: Alignment.center,
                        child: Text(
                          bag.toString(),
                          style: Theme.of(context).textTheme.labelLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: isSelected ? textOnBlue : textPrimary,
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 12.0),

                Text(
                  "Bag Tier",
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w500,
                    color: textPrimary,
                  ),
                ),
                const SizedBox(height: 12.0),
                Wrap(
                  spacing: 8.0,
                  children: BagTier.values.map((tier) {
                    final isSelected = _selectedTier == tier;
                    return ChoiceChip(
                      label: Text(
                        tier.displayLabel,
                        style: Theme.of(context).textTheme.labelMedium?.copyWith(
                          color: isSelected ? textOnBlue : textPrimary,
                        ),
                      ),
                      selected: isSelected,
                      onSelected: (selected) {
                        if (selected) {
                          setState(() {
                            _selectedTier = tier;
                          });
                        }
                      },
                      selectedColor: institutionalBlue,
                      backgroundColor: surfaceWhite,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8.0),
                        side: BorderSide(
                          color: isSelected ? institutionalBlue : dividerGray,
                        ),
                      ),
                      showCheckmark: false,
                    );
                  }).toList(),
                ),
                const SizedBox(height: 12.0),

                if (_selectedBagNum != null)
                  Card(
                    margin: EdgeInsets.zero,
                    elevation: 0.0,
                    color: statusGreenLight,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8.0),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(12.0),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Icon(Icons.check_circle, color: statusGreen, size: checkIconSize),
                          const SizedBox(width: 8.0),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "BAG $_selectedBagNum · ${_selectedTier.displayLabel}",
                                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: statusGreen,
                                ),
                              ),
                              Text(
                                "Selected by inspector",
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

                const Spacer(),

                SizedBox(
                  width: double.infinity,
                  height: buttonHeight,
                  child: ElevatedButton(
                    onPressed: _selectedBagNum != null
                        ? () => widget.onBagSelected(_selectedBagNum!, _selectedTier)
                        : null,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: institutionalBlue,
                      disabledBackgroundColor: dividerGray,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8.0),
                      ),
                    ),
                    child: Text(
                      "PROCEED TO CAPTURE",
                      style: Theme.of(context).textTheme.labelLarge?.copyWith(
                        color: _selectedBagNum != null ? textOnBlue : textSecondary,
                        fontWeight: FontWeight.bold,
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