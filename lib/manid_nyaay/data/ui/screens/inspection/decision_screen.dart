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
    // ── MediaQuery values ────────────────────────────────────────────────
    final Size size = MediaQuery.sizeOf(context);
    final double safeBottom = MediaQuery.paddingOf(context).bottom;
    final double scale = (size.width / 375).clamp(0.85, 1.3);

    final double pagePadding = (size.width * 0.04).clamp(12.0, 24.0);
    final double maxContentWidth = 600.0;
    final double gradeCardPadding = 24.0 * scale;
    final double cardPadding = 16.0 * scale;
    final double gradeFontSize = 32.0 * scale;
    final double smallIconSize = 18.0 * scale;
    final double buttonHeight = (48.0 * scale).clamp(48.0, 60.0);
    final double outlinedButtonHeight = (44.0 * scale).clamp(44.0, 56.0);

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
      body: Align(
        alignment: Alignment.topCenter,
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: maxContentWidth),
          child: SingleChildScrollView(
            padding: EdgeInsets.fromLTRB(
              pagePadding,
              pagePadding,
              pagePadding,
              pagePadding + safeBottom,
            ),
            child: Column(
              children: [
                // Grade Card
                Card(
                  elevation: 3.0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  color: surfaceWhite,
                  child: SizedBox(
                    width: double.infinity,
                    child: Padding(
                      padding: EdgeInsets.all(gradeCardPadding),
                      child: Column(
                        children: [
                          Text(
                            "AUTHORITATIVE STATUTORY GRADE",
                            textAlign: TextAlign.center,
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12 * scale, color: textSecondary),
                          ),
                          const SizedBox(height: 16),
                          Container(
                            padding: EdgeInsets.symmetric(horizontal: 24 * scale, vertical: 12 * scale),
                            decoration: BoxDecoration(
                              color: gradeColor.withOpacity(0.12),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: gradeColor, width: 2),
                            ),
                            // FittedBox so long grades (e.g. MANUAL_REVIEW) shrink instead of overflowing
                            child: FittedBox(
                              fit: BoxFit.scaleDown,
                              child: Text(
                                grade,
                                style: TextStyle(
                                  fontSize: gradeFontSize,
                                  fontWeight: FontWeight.bold,
                                  color: gradeColor,
                                  letterSpacing: 1.2,
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 14),
                          Text(
                            "STATUS: $status",
                            textAlign: TextAlign.center,
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13 * scale, color: textPrimary),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            "RulePack: $rulePack  •  v${(decision['rule_pack_version'] ?? '1.0.0')}",
                            textAlign: TextAlign.center,
                            style: TextStyle(fontSize: 12 * scale, color: textSecondary),
                          ),
                        ],
                      ),
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
                    child: SizedBox(
                      width: double.infinity,
                      child: Padding(
                        padding: EdgeInsets.all(cardPadding),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(Icons.rule, color: institutionalBlue, size: smallIconSize),
                                const SizedBox(width: 8),
                                Text(
                                  "RULEPACK SIGNALS",
                                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13 * scale, color: textSecondary),
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
                                    Icon(Icons.arrow_right, size: 16 * scale, color: institutionalBlue),
                                    const SizedBox(width: 4),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            label,
                                            style: TextStyle(
                                              fontSize: 12 * scale,
                                              fontWeight: FontWeight.bold,
                                              color: textPrimary,
                                            ),
                                          ),
                                          if (desc.isNotEmpty)
                                            Text(
                                              desc,
                                              style: TextStyle(fontSize: 11 * scale, color: textSecondary),
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
                  ),
                  const SizedBox(height: 14),
                ],

                // Override Option Card
                Card(
                  elevation: 1.0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  color: surfaceWhite,
                  child: SizedBox(
                    width: double.infinity,
                    child: Padding(
                      padding: EdgeInsets.all(cardPadding),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "MANUAL INSPECTOR ADJUDICATION",
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13 * scale, color: textSecondary),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            "Inspectors may override rulepack classification with mandatory justification audit trail.",
                            style: TextStyle(fontSize: 12 * scale, color: textSecondary),
                          ),
                          const SizedBox(height: 12),
                          OutlinedButton.icon(
                            onPressed: () => _openOverrideDialog(context),
                            icon: const Icon(Icons.edit_note, color: institutionalBlue),
                            label: const Text("APPLY MANUAL OVERRIDE"),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: institutionalBlue,
                              minimumSize: Size(double.infinity, outlinedButtonHeight),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 24),

                ElevatedButton(
                  onPressed: widget.onProceed,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: institutionalBlue,
                    foregroundColor: textOnBlue,
                    minimumSize: Size(double.infinity, buttonHeight),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  child: const Text("VIEW TAMPER-EVIDENT EVIDENCE & REPLAY", style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _openOverrideDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) {
        // ── MediaQuery values for the dialog ────────────────────────────
        final double dialogWidth = MediaQuery.sizeOf(ctx).width;
        final double dialogSideInset = (dialogWidth * 0.06).clamp(16.0, 40.0);

        return StatefulBuilder(
          builder: (ctx, setDialogState) => AlertDialog(
            insetPadding: EdgeInsets.symmetric(
              horizontal: dialogSideInset,
              vertical: 24.0,
            ),
            scrollable: true, // usable with keyboard open / landscape
            title: const Text("Manual Inspector Override"),
            content: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  DropdownButtonFormField<String>(
                    value: _selectedOverride,
                    isExpanded: true, // long item labels never overflow
                    decoration: const InputDecoration(labelText: "Adjudicated Grade"),
                    items: const [
                      DropdownMenuItem(value: "GRADE_A", child: Text("GRADE_A (Procurement Approved)", overflow: TextOverflow.ellipsis)),
                      DropdownMenuItem(value: "URS", child: Text("URS (Under Recommended Standard)", overflow: TextOverflow.ellipsis)),
                      DropdownMenuItem(value: "REJECT", child: Text("REJECT (Non-compliant)", overflow: TextOverflow.ellipsis)),
                      DropdownMenuItem(value: "MANUAL_REVIEW", child: Text("MANUAL_REVIEW (Referred to APMC)", overflow: TextOverflow.ellipsis)),
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
        );
      },
    );
  }
}