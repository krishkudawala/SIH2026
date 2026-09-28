import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';

const Color _bgGray = Color(0xFFF4F5F7);
const Color _surfaceWhite = Colors.white;
const Color _blue = Color(0xFF1565C0);
const Color _textPrimary = Color(0xFF1E293B);
const Color _textSecondary = Color(0xFF64748B);
const Color _statusGreen = Color(0xFF4CAF50);
const Color _statusAmber = Color(0xFFFFA000);
const Color _statusRed = Color(0xFFEF4444);

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
  int? _selectedIndex;

  Color _conditionColor(String condition) {
    switch (condition.toUpperCase()) {
      case 'HEALTHY':
        return _statusGreen;
      case 'DAMAGED':
      case 'SPROUTED':
        return _statusAmber;
      case 'ROTTEN':
      case 'CLASS_CONFLICT':
        return _statusRed;
      default:
        return const Color(0xFF757575);
    }
  }

  void _showObservationDetail(Map<String, dynamic> obs) {
    final condition = (obs['condition'] ?? 'UNKNOWN').toString();
    final conf = ((obs['confidence'] as num?)?.toDouble() ?? 0.0) * 100;
    final defectType = obs['dominant_defect_type']?.toString() ?? obs['defect_type']?.toString() ?? 'NONE';
    final viewAngle = obs['view_angle']?.toString() ?? obs['capture_role']?.toString() ?? 'UNKNOWN';
    final captureId = obs['capture_id']?.toString() ?? '—';
    final sampleUnitId = obs['sample_unit_id']?.toString() ?? '—';
    final obsId = obs['id']?.toString() ?? '—';
    final sizeMm = obs['size_mm']?.toString() ?? obs['diameter_mm']?.toString() ?? 'UNVALIDATED';
    final defectFrac = ((obs['visible_defect_fraction'] as num?)?.toDouble() ?? 0.0) * 100;

    final condColor = _conditionColor(condition);

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.55,
        maxChildSize: 0.9,
        minChildSize: 0.4,
        builder: (_, scrollCtrl) => Container(
          decoration: const BoxDecoration(
            color: _surfaceWhite,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: ListView(
            controller: scrollCtrl,
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
            children: [
              Center(
                child: Container(
                  width: 40, height: 4, margin: const EdgeInsets.symmetric(vertical: 12),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade300,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: condColor.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: condColor, width: 1.5),
                    ),
                    child: Text(
                      condition,
                      style: TextStyle(
                        color: condColor,
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Confidence: ${conf.toStringAsFixed(1)}%',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                        color: _blue,
                      ),
                    ),
                  ),
                ],
              ),
              const Divider(height: 24),
              _detailRow('Observation ID', obsId),
              _detailRow('Capture ID', captureId),
              _detailRow('Sample Unit ID', sampleUnitId),
              _detailRow('View / Orientation', viewAngle),
              _detailRow('Defect Type', defectType),
              if (defectFrac > 0)
                _detailRow('Visible Defect Area', '${defectFrac.toStringAsFixed(1)}%'),
              _detailRow('Estimated Diameter', sizeMm == 'UNVALIDATED' ? 'UNVALIDATED' : '$sizeMm mm'),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFF8E1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text(
                  'This result is derived from real ONNX model inference. '
                  'Confidence is temperature-scaled. '
                  'Internal quality is not observed by RGB camera alone.',
                  style: TextStyle(fontSize: 11, color: Color(0xFFE65100)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _detailRow(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              width: 140,
              child: Text(
                label,
                style: const TextStyle(fontSize: 12, color: _textSecondary),
              ),
            ),
            Expanded(
              child: Text(
                value,
                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: _textPrimary),
              ),
            ),
          ],
        ),
      );

  @override
  Widget build(BuildContext context) {
    final observations = widget.uiState.rawObservations;
    final totalCount = observations.length;
    final healthyCount = observations
        .where((o) => (o['condition'] ?? '').toString().toUpperCase() == 'HEALTHY')
        .length;
    final defectCount = totalCount - healthyCount;

    return Scaffold(
      backgroundColor: _bgGray,
      appBar: MandiTopAppBar(
        title: 'AI Detections',
        subtitle: 'Session: ${widget.uiState.sessionId.length > 12 ? '${widget.uiState.sessionId.substring(0, 12)}…' : widget.uiState.sessionId}',
        showBack: true,
        onBack: widget.onBack,
      ),
      body: Column(
        children: [
          // Image with real bounding boxes
          Container(
            height: 220,
            width: double.infinity,
            color: Colors.black,
            child: Stack(
              fit: StackFit.expand,
              children: [
                if (widget.uiState.lastCapturedBytes != null)
                  Image.memory(
                    widget.uiState.lastCapturedBytes!,
                    fit: BoxFit.contain,
                  )
                else if (widget.uiState.lastCapturedFile != null)
                  Image.file(
                    widget.uiState.lastCapturedFile!,
                    fit: BoxFit.contain,
                  )
                else
                  const Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.image_not_supported_outlined, color: Colors.white38, size: 36),
                        SizedBox(height: 6),
                        Text('Capture image not cached', style: TextStyle(color: Colors.white38, fontSize: 12)),
                      ],
                    ),
                  ),

                // Real bounding box overlay from ONNX observations
                CustomPaint(
                  painter: _BBoxPainter(
                    observations: observations,
                    selectedIndex: _selectedIndex,
                    conditionColor: _conditionColor,
                  ),
                ),

                // Detection summary bar
                Positioned(
                  bottom: 8, left: 8, right: 8,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xBF000000),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      totalCount == 0
                          ? 'No produce detected — retry capture or check lighting'
                          : 'ONNX: $totalCount detected  •  $healthyCount Healthy  •  $defectCount Defect',
                      style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Disclaimer
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            color: const Color(0xFFFFF8E1),
            child: const Row(
              children: [
                Icon(Icons.verified_outlined, size: 16, color: Color(0xFFF57C00)),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'External condition only — internal quality not detectable by RGB camera.',
                    style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Color(0xFFE65100)),
                  ),
                ),
              ],
            ),
          ),

          // Header
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 4),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'OBSERVATIONS ($totalCount)',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: _textSecondary),
                ),
                const Text(
                  'Tap for details',
                  style: TextStyle(fontSize: 11, color: _textSecondary),
                ),
              ],
            ),
          ),

          // Observation cards
          Expanded(
            child: observations.isEmpty
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.search_off, size: 44, color: _textSecondary),
                        const SizedBox(height: 8),
                        const Text(
                          'No observations returned.\nCapture a new image to run inference.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: _textSecondary, fontSize: 13),
                        ),
                        const SizedBox(height: 16),
                        OutlinedButton.icon(
                          onPressed: widget.onBack,
                          icon: const Icon(Icons.camera_alt_outlined),
                          label: const Text('Recapture'),
                        ),
                      ],
                    ),
                  )
                : ListView.separated(
                    padding: const EdgeInsets.fromLTRB(14, 4, 14, 8),
                    itemCount: observations.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 6),
                    itemBuilder: (_, index) {
                      final obs = observations[index];
                      final condition = (obs['condition'] ?? 'HEALTHY').toString();
                      final conf = ((obs['confidence'] as num?)?.toDouble() ?? 0.0) * 100;
                      final obsId = obs['id']?.toString() ?? 'obs_${index + 1}';
                      final defectType = obs['dominant_defect_type']?.toString()
                          ?? obs['defect_type']?.toString()
                          ?? '';
                      final defectFrac = ((obs['visible_defect_fraction'] as num?)?.toDouble() ?? 0.0) * 100;
                      final condColor = _conditionColor(condition);
                      final isSel = _selectedIndex == index;

                      return Card(
                        margin: EdgeInsets.zero,
                        elevation: isSel ? 3 : 1,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                          side: isSel
                              ? const BorderSide(color: _blue, width: 2)
                              : BorderSide.none,
                        ),
                        color: _surfaceWhite,
                        child: InkWell(
                          onTap: () {
                            setState(() => _selectedIndex = index);
                            _showObservationDetail(obs);
                          },
                          borderRadius: BorderRadius.circular(8),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                            child: Row(
                              children: [
                                // Condition badge
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: condColor.withOpacity(0.12),
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(color: condColor),
                                  ),
                                  child: Text(
                                    condition,
                                    style: TextStyle(
                                      color: condColor,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 11,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                // ID + defect info
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        obsId,
                                        style: const TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 12,
                                          color: _textPrimary,
                                        ),
                                      ),
                                      if (defectType.isNotEmpty && defectType != 'NONE')
                                        Text(
                                          defectType,
                                          style: const TextStyle(fontSize: 11, color: _textSecondary),
                                        ),
                                      if (defectFrac > 0)
                                        Text(
                                          'Defect: ${defectFrac.toStringAsFixed(1)}%',
                                          style: const TextStyle(fontSize: 11, color: _textSecondary),
                                        ),
                                    ],
                                  ),
                                ),
                                // Confidence
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Text(
                                      '${conf.toStringAsFixed(1)}%',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.bold,
                                        fontSize: 14,
                                        color: _blue,
                                      ),
                                    ),
                                    const Text('conf', style: TextStyle(fontSize: 10, color: _textSecondary)),
                                  ],
                                ),
                                const SizedBox(width: 4),
                                const Icon(Icons.chevron_right, size: 18, color: _textSecondary),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
          ),

          // Bottom action
          Container(
            padding: const EdgeInsets.all(14),
            color: _surfaceWhite,
            child: ElevatedButton(
              onPressed: widget.onProceed,
              style: ElevatedButton.styleFrom(
                backgroundColor: _blue,
                foregroundColor: Colors.white,
                minimumSize: const Size(double.infinity, 48),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: const Text(
                'PROCEED TO SAMPLING SUFFICIENCY',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Custom painter that draws real bounding boxes from ONNX observations.
class _BBoxPainter extends CustomPainter {
  final List<Map<String, dynamic>> observations;
  final int? selectedIndex;
  final Color Function(String) conditionColor;

  _BBoxPainter({
    required this.observations,
    required this.conditionColor,
    this.selectedIndex,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final labelPaint = Paint();

    for (int i = 0; i < observations.length; i++) {
      final obs = observations[i];
      final condition = (obs['condition'] ?? 'HEALTHY').toString();
      final conf = ((obs['confidence'] as num?)?.toDouble() ?? 0.0);

      // Try bbox in [ymin, xmin, ymax, xmax] normalized format
      final bbox = obs['bbox'] as List<dynamic>?
          ?? obs['bounding_box'] as List<dynamic>?;

      if (bbox == null || bbox.length < 4) continue;

      final ymin = (bbox[0] as num).toDouble();
      final xmin = (bbox[1] as num).toDouble();
      final ymax = (bbox[2] as num).toDouble();
      final xmax = (bbox[3] as num).toDouble();

      // Validate normalized coords
      if (xmin < 0 || xmax > 1 || ymin < 0 || ymax > 1) continue;

      final rect = Rect.fromLTRB(
        xmin * size.width,
        ymin * size.height,
        xmax * size.width,
        ymax * size.height,
      );

      final isSel = selectedIndex == i;
      final color = conditionColor(condition);
      final boxPaint = Paint()
        ..color = isSel ? Colors.yellow : color.withOpacity(0.85)
        ..style = PaintingStyle.stroke
        ..strokeWidth = isSel ? 3.0 : 1.8;

      canvas.drawRect(rect, boxPaint);

      // Fill slight tint
      if (isSel) {
        labelPaint
          ..color = Colors.yellow.withOpacity(0.12)
          ..style = PaintingStyle.fill;
        canvas.drawRect(rect, labelPaint);
      }

      // Label with condition + confidence
      final label = '${condition.substring(0, condition.length.clamp(0, 3))} ${(conf * 100).toStringAsFixed(0)}%';
      final tp = TextPainter(
        text: TextSpan(
          text: label,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 9,
            fontWeight: FontWeight.bold,
            backgroundColor: Color(0xBF000000),
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout(maxWidth: rect.width);

      tp.paint(canvas, rect.topLeft + const Offset(2, 2));
    }
  }

  @override
  bool shouldRepaint(covariant _BBoxPainter oldDelegate) =>
      oldDelegate.selectedIndex != selectedIndex ||
      oldDelegate.observations != observations;
}
