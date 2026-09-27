import 'package:flutter/material.dart';

// Note: Replace these with your actual theme colors
const Color textSecondary = Colors.black54;
const Color textPrimary = Colors.black87;
const Color progressTrack = Color(0xFFE0E0E0); // Placeholder for ProgressTrack
const Color institutionalBlue = Colors.blue;

class SamplingProgressBar extends StatelessWidget {
  final int completed;
  final int total;

  const SamplingProgressBar({
    super.key,
    required this.completed,
    required this.total,
  });

  @override
  Widget build(BuildContext context) {
    // Prevent division by zero and ensure the fraction stays between 0.0 and 1.0
    final double fraction = total == 0
        ? 0.0
        : (completed / total).clamp(0.0, 1.0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        // Header Texts
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween, // Arrangement.SpaceBetween
          crossAxisAlignment: CrossAxisAlignment.center, // Alignment.CenterVertically
          children: [
            Text(
              "Sampling Progress",
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: textSecondary,
              ),
            ),
            Text(
              "$completed / $total samples",
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.w500, // FontWeight.Medium
                color: textPrimary,
              ),
            ),
          ],
        ),

        const SizedBox(height: 4.0), // Spacer(modifier = Modifier.height(4.dp))

        // Custom Progress Bar Track
        Container(
          width: double.infinity, // fillMaxWidth()
          height: 6.0,
          alignment: Alignment.centerLeft, // Ensures the inner bar starts from the left
          decoration: BoxDecoration(
            color: progressTrack,
            borderRadius: BorderRadius.circular(3.0),
          ),

          // Inner Progress Indicator
          child: FractionallySizedBox(
            widthFactor: fraction, // fillMaxWidth(fraction)
            heightFactor: 1.0, // fillMaxHeight()
            child: Container(
              decoration: BoxDecoration(
                color: institutionalBlue,
                borderRadius: BorderRadius.circular(3.0),
              ),
            ),
          ),
        ),
      ],
    );
  }
}