import 'package:flutter/material.dart';

// Note: Replace these with your actual theme colors
// equivalent to your com.mandiNyaay.ui.theme colors
const Color institutionalBlue = Colors.blue;
const Color surfaceWhite = Colors.white;
const Color textOnBlue = Colors.white;
const Color textSecondary = Colors.black54;

class FilterChipRow extends StatelessWidget {
  final List<String> chips;
  final String selectedChip;
  // ValueChanged<String> is Flutter's equivalent to (String) -> Unit
  final ValueChanged<String> onChipSelected;

  const FilterChipRow({
    super.key,
    required this.chips,
    required this.selectedChip,
    required this.onChipSelected,
  });

  @override
  Widget build(BuildContext context) {
    // Wrap automatically handles horizontal spacing and line breaks if the screen is too narrow.
    // (If you specifically want a horizontally scrolling list instead, use a SingleChildScrollView)
    return Wrap(
      spacing: 8.0, // Equivalent to Arrangement.spacedBy(8.dp)
      children: chips.map((chip) {
        final isSelected = chip == selectedChip;

        // Material + InkWell perfectly replicates Compose's Box + Modifier.clickable
        // with the proper Android ripple effect.
        return Material(
          color: isSelected ? institutionalBlue : surfaceWhite,
          borderRadius: BorderRadius.circular(16.0), // RoundedCornerShape(16.dp)
          child: InkWell(
            onTap: () => onChipSelected(chip),
            borderRadius: BorderRadius.circular(16.0), // Keeps ripple inside the border
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 6.0),
              child: Text(
                chip,
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                  color: isSelected ? textOnBlue : textSecondary,
                ),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}