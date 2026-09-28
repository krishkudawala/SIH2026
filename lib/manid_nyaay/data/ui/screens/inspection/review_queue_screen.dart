import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';

const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color statusAmber = Color(0xFFFFA000);

class ReviewQueueScreen extends StatelessWidget {
  final InspectionUiState uiState;
  final VoidCallback onProceed;
  final VoidCallback onBack;

  const ReviewQueueScreen({
    super.key,
    required this.uiState,
    required this.onProceed,
    required this.onBack,
  });

  @override
  Widget build(BuildContext context) {
    final review = uiState.reviewData ?? {};
    final queue = (review['review_queue'] as List<dynamic>?) ?? [];
    final queueStatus = (review['status'] ?? 'REVIEW_PENDING').toString();

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Review Center",
        subtitle: "APMC Inspection Audit Queue",
        showBack: true,
        onBack: onBack,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Mandatory non-fraud banner
            Container(
              padding: const EdgeInsets.all(12.0),
              decoration: BoxDecoration(
                color: const Color(0xFFFFF8E1),
                borderRadius: BorderRadius.circular(8.0),
                border: Border.all(color: const Color(0xFFFFE082)),
              ),
              child: const Row(
                children: [
                  Icon(Icons.info, color: Color(0xFFF57C00), size: 20),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      "Review signals represent items flagged for human verification prior to statutory commitment. They are never labeled as fraud.",
                      style: TextStyle(fontSize: 12, color: Color(0xFFE65100), fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Queue Status Card
            Card(
              elevation: 2.0,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              color: surfaceWhite,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          "AUDIT QUEUE STATE",
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: textSecondary),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          queueStatus,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: institutionalBlue),
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: statusAmber.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        "${queue.length} Signals",
                        style: const TextStyle(color: statusAmber, fontWeight: FontWeight.bold, fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            const Text(
              "FLAGGED REVIEW SIGNALS",
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textSecondary),
            ),
            const SizedBox(height: 8),

            if (queue.isEmpty)
              Card(
                color: surfaceWhite,
                child: Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Center(
                    child: Column(
                      children: [
                        const Icon(Icons.check_circle_outline, color: Color(0xFF4CAF50), size: 40),
                        const SizedBox(height: 8),
                        const Text("No critical review signals detected.", style: TextStyle(fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Text("Session meets statutory auto-clearance guidelines.", style: TextStyle(fontSize: 12, color: textSecondary)),
                      ],
                    ),
                  ),
                ),
              )
            else
              ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: queue.length,
                separatorBuilder: (context, index) => const SizedBox(height: 8),
                itemBuilder: (context, index) {
                  final item = queue[index];
                  final signalType = (item['signal_type'] ?? item['type'] ?? 'QUALITY_SIGNAL').toString();
                  final explanation = (item['explanation'] ?? item['description'] ?? 'Signal pending review').toString();
                  final priority = (item['priority'] ?? item['severity'] ?? 'MEDIUM').toString();

                  return Card(
                    margin: EdgeInsets.zero,
                    color: surfaceWhite,
                    elevation: 1.0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    child: Padding(
                      padding: const EdgeInsets.all(12.0),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.flag_outlined, color: statusAmber, size: 20),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      signalType,
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textPrimary),
                                    ),
                                    Text(
                                      priority,
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: statusAmber),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  explanation,
                                  style: const TextStyle(fontSize: 12, color: textSecondary),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            const SizedBox(height: 24),

            ElevatedButton(
              onPressed: onProceed,
              style: ElevatedButton.styleFrom(
                backgroundColor: institutionalBlue,
                foregroundColor: textOnBlue,
                minimumSize: const Size(double.infinity, 48),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: const Text("PROCEED TO STATUTORY DECISION", style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      ),
    );
  }
}
