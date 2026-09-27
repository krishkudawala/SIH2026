import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/work_load_metrics.dart';

// Assuming your domain models are imported
// import 'package:mandi_nyaay/domain/model/lot_status.dart';
// import 'package:mandi_nyaay/domain/model/review_status.dart';

// --- Theme Colors Placeholder ---
const Color statusBlueLight = Color(0xFFE3F2FD);
const Color statusBlue = Color(0xFF1976D2);
const Color statusGreenLight = Color(0xFFE8F5E9);
const Color statusGreen = Color(0xFF388E3C);
const Color statusAmberLight = Color(0xFFFFF8E1);
const Color statusAmber = Color(0xFFFFA000);
const Color statusOrangeLight = Color(0xFFFFF3E0);
const Color statusOrange = Color(0xFFF57C00);
const Color statusRedLight = Color(0xFFFFEBEE);
const Color statusRed = Color(0xFFD32F2F);
const Color backgroundGray = Color(0xFFF5F5F5);
const Color textSecondary = Colors.black54;
const Color blueLight = Color(0xFFE1F5FE);
const Color institutionalBlue = Colors.blue;


// --- Status Badge ---
class StatusBadge extends StatelessWidget {
  final LotStatus status;

  const StatusBadge({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    // Dart 3 switch expression and Record destructuring (Equivalent to Kotlin's `when` and `Triple`)
    final (Color bg, Color fg, String label) = switch (status) {
      LotStatus.active      => (statusBlueLight, statusBlue, "In Progress"),
      LotStatus.completed   => (statusGreenLight, statusGreen, "Completed"),
      LotStatus.needsReview => (statusAmberLight, statusAmber, "Review"),
      LotStatus.disputed    => (statusOrangeLight, statusOrange, "Disputed"),
    };

    return _BadgeBox(text: label, background: bg, textColor: fg);
  }
}


// --- Grade Badge ---
class GradeBadge extends StatelessWidget {
  final String gradeLabel;

  const GradeBadge({super.key, required this.gradeLabel});

  @override
  Widget build(BuildContext context) {
    // Handling String matching using an inline function or switch
    final (Color bg, Color fg) = () {
      switch (gradeLabel.toUpperCase()) {
        case "GRADE A":
        case "GRADE_A":
          return (statusGreenLight, statusGreen);
        case "URS":
          return (statusAmberLight, statusAmber);
        case "REJECT":
          return (statusRedLight, statusRed);
        default:
          return (backgroundGray, textSecondary);
      }
    }();

    return _BadgeBox(text: gradeLabel, background: bg, textColor: fg);
  }
}


// --- Review Status Badge ---
class ReviewStatusBadge extends StatelessWidget {
  final ReviewStatus status;

  const ReviewStatusBadge({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    final (Color bg, Color fg, String label) = switch (status) {
      ReviewStatus.pending            => (statusAmberLight, statusAmber, "Review"),
      ReviewStatus.disputed           => (statusOrangeLight, statusOrange, "Disputed"),
      ReviewStatus.accepted           => (statusGreenLight, statusGreen, "Accepted"),
      ReviewStatus.overridden         => (blueLight, institutionalBlue, "Overridden"),
      ReviewStatus.recaptureRequested => (statusRedLight, statusRed, "Recapture"),
    };

    return _BadgeBox(text: label, background: bg, textColor: fg);
  }
}


// --- Helper Badge Box ---
// Equivalent to private fun BadgeBox(...) in Compose
class _BadgeBox extends StatelessWidget {
  final String text;
  final Color background;
  final Color textColor;

  const _BadgeBox({
    required this.text,
    required this.background,
    required this.textColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6.0, vertical: 2.0),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(4.0),
      ),
      child: Text(
        text,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: textColor,
          fontWeight: FontWeight.w600, // FontWeight.SemiBold
        ),
      ),
    );
  }
}