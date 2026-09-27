import 'package:flutter/material.dart';

// Note: Replace these with your actual theme colors
// equivalent to your com.mandiNyaay.ui.theme colors
const Color institutionalBlue = Colors.blue;
const Color textPrimary = Colors.black87;
const Color textSecondary = Colors.black54;

class ChevronRow extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? subtitle;
  final String? trailingText;
  final VoidCallback onClick;

  const ChevronRow({
    super.key,
    required this.icon,
    required this.title,
    this.subtitle,
    this.trailingText,
    required this.onClick,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onClick, // Equivalent to Modifier.clickable
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center, // verticalAlignment = Alignment.CenterVertically
          children: [
            // Leading Icon
            Icon(
              icon,
              color: institutionalBlue,
              size: 22.0,
            ),
            const SizedBox(width: 14.0), // Spacer

            // Middle Text Column
            Expanded( // Equivalent to Modifier.weight(1f)
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    title,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: textPrimary,
                    ),
                  ),
                  if (subtitle != null)
                    Text(
                      subtitle!,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: textSecondary,
                      ),
                    ),
                ],
              ),
            ),

            // Optional Trailing Text
            if (trailingText != null) ...[
              Text(
                trailingText!,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: textSecondary,
                ),
              ),
              const SizedBox(width: 4.0),
            ],

            // Trailing Chevron Icon
            const Icon(
              Icons.chevron_right, // Equivalent to Icons.AutoMirrored.Filled.KeyboardArrowRight
              color: textSecondary,
              size: 18.0,
            ),
          ],
        ),
      ),
    );
  }
}