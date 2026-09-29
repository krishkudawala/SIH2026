import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/ui/utils/responsive.dart';

// Assuming your domain models are imported
// import 'package:mandi_nyaay/domain/model/lot.dart';
// import 'package:mandi_nyaay/domain/model/lot_status.dart';

// --- Theme Constants Placeholder ---
const Color surfaceWhite = Colors.white;
const Color dividerGray = Color(0xFFE0E0E0);
const Color textPrimary = Colors.black87;
const Color textSecondary = Colors.black54;
const Color institutionalBlue = Colors.blue;
const Color statusOrange = Colors.orange;
const Color textOnBlue = Colors.white;

final BorderRadius mandiShapesMedium = BorderRadius.circular(12.0);
final BorderRadius mandiShapesSmall = BorderRadius.circular(8.0);

// --- LotCard ---

class LotCard extends StatelessWidget {
  final Lot lot;
  final VoidCallback onContinue;
  final VoidCallback onOpenCase;

  const LotCard({
    super.key,
    required this.lot,
    required this.onContinue,
    this.onOpenCase = _defaultOnOpenCase,
  });

  static void _defaultOnOpenCase() {}

  @override
  Widget build(BuildContext context) {
    final isDisputed = lot.status == LotStatus.disputed;

    return Card(
      color: surfaceWhite,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: mandiShapesMedium,
        side: const BorderSide(color: dividerGray, width: 1.0),
      ),
      child: Padding(
        padding: EdgeInsets.all(context.responsivePadding(16.0)),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header row
            Row(
              crossAxisAlignment: CrossAxisAlignment.start, // Alignment.Top
              children: [
                Expanded( // Modifier.weight(1f)
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        lot.id,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: textPrimary,
                        ),
                      ),
                      Text(
                        "${lot.certifiedWeightKg.toInt()} kg · ${lot.bagCount} bags",
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: textSecondary,
                          fontWeight: FontWeight.w500, // FontWeight.Medium
                        ),
                      ),
                    ],
                  ),
                ),
                StatusBadge(status: lot.status),
              ],
            ),

            // Sampling progress
            if (lot.samplingPlan != null) ...[
              const SizedBox(height: 12.0),
              SamplingProgressBar(
                completed: lot.samplingPlan!.completedSamples,
                total: lot.samplingPlan!.totalSamplesRequired,
              ),
            ],

            const SizedBox(height: 16.0),

            // Action button
            SizedBox(
              width: double.infinity, // Modifier.fillMaxWidth()
              height: 44.0,
              child: FilledButton(
                onPressed: isDisputed ? onOpenCase : onContinue,
                style: FilledButton.styleFrom(
                  backgroundColor: isDisputed ? statusOrange : institutionalBlue,
                  shape: RoundedRectangleBorder(
                    borderRadius: mandiShapesSmall,
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 16.0),
                ),
                child: Text(
                  isDisputed ? "OPEN CASE" : "CONTINUE INSPECTION",
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: textOnBlue,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// --- LotListRow ---

class LotListRow extends StatelessWidget {
  final Lot lot;
  final VoidCallback onClick;

  const LotListRow({
    super.key,
    required this.lot,
    required this.onClick,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onClick, // Modifier.clickable
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 10.0),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center, // Alignment.CenterVertically
          children: [
            Expanded( // Modifier.weight(1f)
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    lot.id,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w600, // FontWeight.SemiBold
                      color: textPrimary,
                    ),
                  ),
                  Text(
                    "${lot.farmerName} · ${lot.village}",
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: textSecondary,
                    ),
                  ),
                  Text(
                    "${lot.certifiedWeightKg.toInt()} kg",
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: textSecondary,
                    ),
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                StatusBadge(status: lot.status),
                if (lot.samplingPlan != null) ...[
                  const SizedBox(height: 4.0),
                  Text(
                    "${lot.samplingPlan!.completedSamples}/${lot.samplingPlan!.totalSamplesRequired}",
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: textSecondary,
                    ),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// --- Assumed Missing Widgets Placeholder ---
// You likely already have these built, but providing stubs so the code compiles.

class StatusBadge extends StatelessWidget {
  final LotStatus status;
  const StatusBadge({super.key, required this.status});
  @override
  Widget build(BuildContext context) => Container();
}

class SamplingProgressBar extends StatelessWidget {
  final int completed;
  final int total;
  const SamplingProgressBar({super.key, required this.completed, required this.total});
  @override
  Widget build(BuildContext context) => Container();
}