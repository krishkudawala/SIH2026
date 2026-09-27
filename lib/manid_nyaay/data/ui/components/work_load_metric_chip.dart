import 'package:flutter/material.dart';

// --- Theme Constants Placeholder ---
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Colors.blue;
const Color textSecondary = Colors.black54;

final BorderRadius mandiShapesSmall = BorderRadius.circular(8.0);

class WorkloadMetricChip extends StatelessWidget {
  final int count;
  final String label;
  final Color accentColor;

  const WorkloadMetricChip({
    super.key,
    required this.count,
    required this.label,
    this.accentColor = institutionalBlue, // Default value
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12.0, horizontal: 8.0),
      decoration: BoxDecoration(
        color: surfaceWhite,
        borderRadius: mandiShapesSmall, // Equivalent to MandiShapes.small
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min, // Keeps the column from taking infinite vertical space
        mainAxisAlignment: MainAxisAlignment.center, // verticalArrangement
        crossAxisAlignment: CrossAxisAlignment.center, // horizontalAlignment
        children: [
          // Count Text
          Text(
            count.toString(),
            style: Theme.of(context).textTheme.displaySmall?.copyWith(
              color: accentColor,
              fontSize: 28.0, // Slightly smaller than displaySmall
            ),
          ),

          // Label Text
          Text(
            label.toUpperCase(), // Kotlin's .uppercase()
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: textSecondary,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.0, // letterSpacing = 1.sp
            ),
          ),
        ],
      ),
    );
  }
}