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
const Color statusAmber = Color(0xFFFFA000);

class SamplingSufficiencyScreen extends StatelessWidget {
  final InspectionUiState uiState;
  final VoidCallback onSampleNextBag;
  final VoidCallback onProceed;
  final VoidCallback onBack;

  const SamplingSufficiencyScreen({
    super.key,
    required this.uiState,
    required this.onSampleNextBag,
    required this.onProceed,
    required this.onBack,
  });

  @override
  Widget build(BuildContext context) {
    final sampling = uiState.samplingData ?? {};
    final observed = (sampling['observed_sample_size'] as num?)?.toInt() ?? uiState.rawObservations.length;
    final target = (sampling['target_sample_size'] as num?)?.toInt() ?? 15;
    final status = (sampling['status'] ?? 'CONTINUE').toString();
    final reason = (sampling['stopping_reason'] ?? sampling['reason'] ?? 'Statistical threshold evaluation').toString();

    // ---------- FIX: wilson_intervals can be a Map OR a List ----------
    final rawWilson = sampling['wilson_intervals'];
    final Map<String, dynamic> wilson = {};

    if (rawWilson is Map) {
      // Format: { "Grade A": {...}, "Grade B": {...} }
      rawWilson.forEach((k, v) => wilson[k.toString()] = v);
    } else if (rawWilson is List) {
      // Format: [ {"label": "Grade A", "lower_ci": ...}, ... ]
      for (int i = 0; i < rawWilson.length; i++) {
        final item = rawWilson[i];
        if (item is Map) {
          final label = (item['label'] ??
              item['name'] ??
              item['grade'] ??
              item['category'] ??
              item['class'] ??
              'Item ${i + 1}')
              .toString();
          wilson[label] = item;
        }
      }
    }
    // -------------------------------------------------------------------

    final isStop = status == 'STOP';

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Sampling Sufficiency",
        subtitle: "Sequential Statistical Sampling",
        showBack: true,
        onBack: onBack,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Status Banner Card
            Card(
              elevation: 2.0,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              color: surfaceWhite,
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                      decoration: BoxDecoration(
                        color: (isStop ? statusGreen : statusAmber).withOpacity(0.15),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: isStop ? statusGreen : statusAmber),
                      ),
                      child: Text(
                        "SEQUENTIAL STATUS: $status",
                        style: TextStyle(
                          color: isStop ? statusGreen : statusAmber,
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      "$observed / $target",
                      style: const TextStyle(
                        fontSize: 44,
                        fontWeight: FontWeight.bold,
                        color: institutionalBlue,
                      ),
                    ),
                    const Text(
                      "Produce Samples Evaluated vs RulePack Target",
                      style: TextStyle(fontSize: 13, color: textSecondary),
                    ),
                    const SizedBox(height: 12),
                    LinearProgressIndicator(
                      value: (observed / target).clamp(0.0, 1.0),
                      backgroundColor: const Color(0xFFE2E8F0),
                      valueColor: AlwaysStoppedAnimation<Color>(isStop ? statusGreen : institutionalBlue),
                      minHeight: 8,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    const SizedBox(height: 14),
                    Text(
                      reason,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 12, color: textSecondary, fontStyle: FontStyle.italic),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Wilson 95% Confidence Intervals Card
            Card(
              elevation: 1.0,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              color: surfaceWhite,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.analytics_outlined, color: institutionalBlue, size: 20),
                        SizedBox(width: 8),
                        Text(
                          "Wilson 95% Score Intervals",
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: textPrimary),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    if (wilson.isEmpty)
                      const Text(
                        'Sampling in progress — Wilson 95% CI computed once first observations exist.',
                        style: TextStyle(fontSize: 12, color: textSecondary),
                      )
                    else
                      ...wilson.entries.map((entry) {
                        final label = entry.key;
                        final val = entry.value;
                        double lo = 0, hi = 0, point = 0;
                        if (val is Map) {
                          lo = ((val['lower_ci'] ?? val['low'] ?? 0.0) as num).toDouble();
                          hi = ((val['upper_ci'] ?? val['high'] ?? 0.0) as num).toDouble();
                          point = ((val['point_estimate'] ?? val['estimate'] ?? 0.0) as num).toDouble();
                        }
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 5.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    label,
                                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: textPrimary),
                                  ),
                                  Text(
                                    '${(point * 100).toStringAsFixed(1)}%',
                                    style: const TextStyle(fontSize: 13, color: institutionalBlue, fontWeight: FontWeight.bold),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 4),
                              LinearProgressIndicator(
                                value: point.clamp(0.0, 1.0),
                                backgroundColor: const Color(0xFFE2E8F0),
                                valueColor: const AlwaysStoppedAnimation<Color>(institutionalBlue),
                                minHeight: 5,
                                borderRadius: BorderRadius.circular(3),
                              ),
                              Text(
                                '95% CI: ${(lo * 100).toStringAsFixed(1)}% – ${(hi * 100).toStringAsFixed(1)}%',
                                style: const TextStyle(fontSize: 10, color: textSecondary),
                              ),
                            ],
                          ),
                        );
                      }),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Disclaimers Card
            Container(
              padding: const EdgeInsets.all(14.0),
              decoration: BoxDecoration(
                color: const Color(0xFFE8F5E9),
                borderRadius: BorderRadius.circular(8.0),
                border: Border.all(color: const Color(0xFFA5D6A7)),
              ),
              child: const Row(
                children: [
                  Icon(Icons.gavel, color: Color(0xFF2E7D32), size: 20),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      "Statistical stopping rules are governed authoritatively by the AGMARK RulePack. No estimated values are fabricated.",
                      style: TextStyle(fontSize: 11, color: Color(0xFF1B5E20), fontWeight: FontWeight.w500),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Next Actions
            ElevatedButton(
              onPressed: onProceed,
              style: ElevatedButton.styleFrom(
                backgroundColor: institutionalBlue,
                foregroundColor: textOnBlue,
                minimumSize: const Size(double.infinity, 48),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: const Text("PROCEED TO MEASUREMENT & WEIGHT", style: TextStyle(fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              onPressed: onSampleNextBag,
              icon: const Icon(Icons.add_a_photo),
              label: const Text("CAPTURE ANOTHER SAMPLE BAG"),
              style: OutlinedButton.styleFrom(
                foregroundColor: institutionalBlue,
                minimumSize: const Size(double.infinity, 44),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}