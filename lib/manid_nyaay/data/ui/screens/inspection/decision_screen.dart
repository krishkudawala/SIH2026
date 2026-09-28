import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';

const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color gradeAColor = Color(0xFF4CAF50);
const Color ursColor = Color(0xFFFFA000);
const Color rejectColor = Color(0xFFEF4444);
const Color reviewColor = Color(0xFFE65100);

class DecisionScreen extends StatefulWidget {
  final InspectionUiState uiState;
  final VoidCallback onProceed;
  final VoidCallback onBack;
  final Function(String overrideGrade, String reason) onOverride;

  const DecisionScreen({
    super.key,
    required this.uiState,
    required this.onProceed,
    required this.onBack,
    required this.onOverride,
  });

  @override
  State<DecisionScreen> createState() => _DecisionScreenState();
}

class _DecisionScreenState extends State<DecisionScreen> {
  final TextEditingController _overrideReasonCtrl = TextEditingController();
  String _selectedOverride = 'GRADE_A';

  Color _getGradeColor(String grade) {
    switch (grade.toUpperCase()) {
      case 'GRADE_A':
        return gradeAColor;
      case 'URS':
        return ursColor;
      case 'REJECT':
        return rejectColor;
      default:
        return reviewColor;
    }
  }

  @override
  void dispose() {
    _overrideReasonCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final decision = widget.uiState.decisionData ?? {};
    final grade = (decision['procurement_grade'] ?? decision['final_grade'] ?? 'MANUAL_REVIEW').toString();
    final status = (decision['status'] ?? 'REFERRED_TO_MANUAL_REVIEW').toString();
    final rulePack = (decision['rule_pack_id'] ?? 'AGMARK_ONION_2024_V1').toString();
    final gradeColor = _getGradeColor(grade);

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Statutory RulePack Decision",
        subtitle: "RulePack: $rulePack",
        showBack: true,
        onBack: widget.onBack,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Grade Card
            Card(
              elevation: 3.0,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              color: surfaceWhite,
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  children: [
                    const Text(
                      "AUTHORITATIVE STATUTORY GRADE",
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: textSecondary),
                    ),
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                      decoration: BoxDecoration(
                        color: gradeColor.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: gradeColor, width: 2),
                      ),
                      child: Text(
                        grade,
                        style: TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                          color: gradeColor,
                          letterSpacing: 1.2,
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),
                    Text(
                      "STATUS: $status",
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textPrimary),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      "RulePack: $rulePack  •  v${(decision['rule_pack_version'] ?? '1.0.0')}",
                      style: const TextStyle(fontSize: 12, color: textSecondary),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Supporting Signals from RulePack evaluation
            if ((decision['signals'] as List?)?.isNotEmpty == true ||
                (decision['triggered_rules'] as List?)?.isNotEmpty == true) ...[
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
                          Icon(Icons.rule, color: institutionalBlue, size: 18),
                          SizedBox(width: 8),
                          Text(
                            "RULEPACK SIGNALS",
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textSecondary),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      ...((decision['signals'] as List?) ??
                              (decision['triggered_rules'] as List?) ??
                              [])
                          .map<Widget>((s) {
                        final signal = s is Map ? s : {'label': s.toString()};
                        final label = signal['label']?.toString() ??
                            signal['code']?.toString() ??
                            signal['rule']?.toString() ??
                            s.toString();
                        final desc = signal['description']?.toString() ??
                            signal['reason']?.toString() ??
                            '';
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(Icons.arrow_right, size: 16, color: institutionalBlue),
                              const SizedBox(width: 4),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      label,
                                      style: const TextStyle(
                                        fontSize: 12,
                                        fontWeight: FontWeight.bold,
                                        color: textPrimary,
                                      ),
                                    ),
                                    if (desc.isNotEmpty)
                                      Text(
                                        desc,
                                        style: const TextStyle(fontSize: 11, color: textSecondary),
                                      ),
                                  ],
                                ),
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
            ],

            // Override Option Card
            Card(
              elevation: 1.0,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              color: surfaceWhite,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "MANUAL INSPECTOR ADJUDICATION",
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textSecondary),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      "Inspectors may override rulepack classification with mandatory justification audit trail.",
                      style: TextStyle(fontSize: 12, color: textSecondary),
                    ),
                    const SizedBox(height: 12),
                    OutlinedButton.icon(
                      onPressed: () => _openOverrideDialog(context),
                      icon: const Icon(Icons.edit_note, color: institutionalBlue),
                      label: const Text("APPLY MANUAL OVERRIDE"),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: institutionalBlue,
                        minimumSize: const Size(double.infinity, 44),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            ElevatedButton(
              onPressed: widget.onProceed,
              style: ElevatedButton.styleFrom(
                backgroundColor: institutionalBlue,
                foregroundColor: textOnBlue,
                minimumSize: const Size(double.infinity, 48),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: const Text("VIEW TAMPER-EVIDENT EVIDENCE & REPLAY", style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      ),
    );
  }

  void _openOverrideDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: const Text("Manual Inspector Override"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                value: _selectedOverride,
                decoration: const InputDecoration(labelText: "Adjudicated Grade"),
                items: const [
                  DropdownMenuItem(value: "GRADE_A", child: Text("GRADE_A (Procurement Approved)")),
                  DropdownMenuItem(value: "URS", child: Text("URS (Under Recommended Standard)")),
                  DropdownMenuItem(value: "REJECT", child: Text("REJECT (Non-compliant)")),
                  DropdownMenuItem(value: "MANUAL_REVIEW", child: Text("MANUAL_REVIEW (Referred to APMC)")),
                ],
                onChanged: (val) => setDialogState(() => _selectedOverride = val ?? 'GRADE_A'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _overrideReasonCtrl,
                decoration: const InputDecoration(
                  labelText: "Mandatory Justification",
                  hintText: "Enter reason for classification change",
                  border: OutlineInputBorder(),
                ),
                maxLines: 2,
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text("CANCEL"),
            ),
            ElevatedButton(
              onPressed: () {
                if (_overrideReasonCtrl.text.trim().isEmpty) {
                  return;
                }
                widget.onOverride(_selectedOverride, _overrideReasonCtrl.text.trim());
                Navigator.of(ctx).pop();
              },
              style: ElevatedButton.styleFrom(backgroundColor: institutionalBlue, foregroundColor: Colors.white),
              child: const Text("COMMIT OVERRIDE"),
            ),
          ],
        ),
      ),
    );
  }
}
