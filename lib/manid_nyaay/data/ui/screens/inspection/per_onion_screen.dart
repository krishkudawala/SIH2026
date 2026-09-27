import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/inspection_session.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/onion_record.dart';
import 'package:sih2631/manid_nyaay/data/fixture/fixture_data.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';

// --- Theme Constants Placeholder ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color blueLight = Color(0xFFE1F5FE);
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color statusRed = Color(0xFFEF4444);

const Color gradeAColor = Color(0xFF4CAF50); // StatusGreen
const Color ursColor = Color(0xFFFFA000);    // StatusAmber
const Color rejectColor = Color(0xFFF44336); // StatusRed

class PerOnionResultScreen extends StatefulWidget {
  final InspectionUiState uiState;
  final VoidCallback onProceed;
  final VoidCallback onBack;

  const PerOnionResultScreen({
    super.key,
    required this.uiState,
    required this.onProceed,
    required this.onBack,
  });

  @override
  State<PerOnionResultScreen> createState() => _PerOnionResultScreenState();
}

class _PerOnionResultScreenState extends State<PerOnionResultScreen> {
  String? selectedOnionId;

  String _takeLast(String text, int n) {
    if (text.length <= n) return text;
    return text.substring(text.length - n);
  }

  Color _getGradeColor(Grade grade) {
    switch (grade) {
      case Grade.gradeA: return gradeAColor;
      case Grade.urs: return ursColor;
      case Grade.reject: return rejectColor;
    }
  }

  @override
  Widget build(BuildContext context) {
    final onions = widget.uiState.onionRecords.isNotEmpty
        ? widget.uiState.onionRecords
        : FixtureData.sampleOnionRecords;

    final subtitle = widget.uiState.selectedBag != null
        ? "BAG ${widget.uiState.selectedBag!.bagNumber} · ${widget.uiState.selectedBag!.tier.displayLabel}"
        : "";

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Per-Onion Results",
        subtitle: subtitle,
        showBack: true,
        onBack: widget.onBack,
      ),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            height: 180.0,
            color: const Color(0xFF1A1A1A),
            padding: const EdgeInsets.all(8.0),
            alignment: Alignment.center,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  "Tray top-view capture",
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Colors.white.withOpacity(0.4),
                  ),
                ),
                const SizedBox(height: 8.0),

                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: onions.take(4).map((onion) => _buildGridDot(onion)).toList(),
                ),
                const SizedBox(height: 8.0),

                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: onions.skip(4).map((onion) => _buildGridDot(onion)).toList(),
                ),
              ],
            ),
          ),

          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(horizontal: 14.0, vertical: 8.0),
              itemCount: onions.length + 1,
              separatorBuilder: (context, index) => const SizedBox(height: 6.0),
              itemBuilder: (context, index) {
                if (index == onions.length) {
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8.0),
                    child: Text(
                      Defect.externalOnlyStatement,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: textSecondary,
                      ),
                    ),
                  );
                }

                final onion = onions[index];
                final isSelected = selectedOnionId == onion.id;

                return OnionRecordRow(
                  onion: onion,
                  isSelected: isSelected,
                  onClick: () {
                    setState(() {
                      selectedOnionId = isSelected ? null : onion.id;
                    });
                  },
                );
              },
            ),
          ),

          Padding(
            padding: const EdgeInsets.all(14.0),
            child: SizedBox(
              width: double.infinity,
              height: 48.0,
              child: ElevatedButton(
                onPressed: widget.onProceed,
                style: ElevatedButton.styleFrom(
                  backgroundColor: institutionalBlue,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8.0),
                  ),
                ),
                child: Text(
                  "CHECK SAMPLING SUFFICIENCY",
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: textOnBlue,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGridDot(OnionRecord onion) {
    final isSelected = selectedOnionId == onion.id;
    final gradeColor = _getGradeColor(onion.grade);

    return GestureDetector(
      onTap: () {
        setState(() {
          selectedOnionId = isSelected ? null : onion.id;
        });
      },
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 4.0),
        width: 40.0,
        height: 40.0,
        decoration: BoxDecoration(
          color: isSelected ? gradeColor : gradeColor.withOpacity(0.5),
          shape: BoxShape.circle,
          border: Border.all(
            color: isSelected ? Colors.white : gradeColor,
            width: 2.0,
          ),
        ),
        alignment: Alignment.center,
        child: Text(
          _takeLast(onion.id, 2),
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}

class OnionRecordRow extends StatelessWidget {
  final OnionRecord onion;
  final bool isSelected;
  final VoidCallback onClick;

  const OnionRecordRow({
    super.key,
    required this.onion,
    required this.isSelected,
    required this.onClick,
  });

  Color _getGradeColor(Grade grade) {
    switch (grade) {
      case Grade.gradeA: return gradeAColor;
      case Grade.urs: return ursColor;
      case Grade.reject: return rejectColor;
    }
  }

  @override
  Widget build(BuildContext context) {
    final gradeColor = _getGradeColor(onion.grade);

    return Card(
      margin: EdgeInsets.zero,
      elevation: isSelected ? 2.0 : 1.0,
      color: isSelected ? blueLight : surfaceWhite,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
      child: InkWell(
        onTap: onClick,
        borderRadius: BorderRadius.circular(8.0),
        child: Padding(
          padding: const EdgeInsets.all(10.0),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Container(
                width: 10.0,
                height: 10.0,
                decoration: BoxDecoration(
                  color: gradeColor,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 10.0),

              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          onion.id,
                          style: Theme.of(context).textTheme.labelLarge?.copyWith(
                            fontWeight: FontWeight.w600,
                            color: textPrimary,
                          ),
                        ),
                        const SizedBox(width: 8.0),
                        Text(
                          onion.grade.displayLabel,
                          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                            color: gradeColor,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                    Text(
                      "⌀ ${onion.diameterMm.toInt()} mm · ~${onion.estimatedWeightGrams.toInt()} g",
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: textSecondary,
                      ),
                    ),
                    if (onion.defects.isNotEmpty)
                      Text(
                        onion.defects.map((d) => d.type.displayLabel).join(", "),
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: statusRed,
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
