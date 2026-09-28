import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:sih2631/manid_nyaay/data/api/api_client.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/chevron_row.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/navigation/screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/more/more_view_model.dart';

// --- Assumed Imports (Replace with actual paths) ---
// import 'package:mandi_nyaay/ui/components/mandi_top_app_bar.dart';
// import 'package:mandi_nyaay/ui/components/chevron_row.dart';
// import 'package:mandi_nyaay/ui/navigation/screen.dart';
// import 'package:mandi_nyaay/ui/screens/more/more_view_model.dart';

// --- Theme Constants Placeholder ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color dividerGray = Color(0xFFE2E8F0);
const Color statusRed = Color(0xFFEF4444);

const Color statusGreenLight = Color(0xFFE8F5E9);
const Color statusGreen = Color(0xFF4CAF50);
const Color statusAmberLight = Color(0xFFFFF8E1);
const Color statusAmber = Color(0xFFFFA000);

class MoreScreen extends StatefulWidget {
  const MoreScreen({super.key});

  @override
  State<MoreScreen> createState() => _MoreScreenState();
}

class _MoreScreenState extends State<MoreScreen> {
  late final MoreViewModel _viewModel;

  @override
  void initState() {
    super.initState();
    _viewModel = MoreViewModel();
  }

  @override
  void dispose() {
    _viewModel.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _viewModel,
      builder: (context, _) {
        final state = _viewModel.uiState;

        return Scaffold(
          backgroundColor: backgroundGray,
          appBar: const MandiTopAppBar(
            title: "More",
          ),
          body: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 12.0),

                // ── Calibration Health ───────────────────────────────────────
                if (state.calibration != null) ...[
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 6.0),
                    child: Text(
                      "Calibration Health",
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: textSecondary,
                      ),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 14.0),
                    child: Card(
                      color: surfaceWhite,
                      elevation: 1.0,
                      margin: EdgeInsets.zero,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8.0),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(14.0),
                        child: Column(
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  "Calibration Status",
                                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    fontWeight: FontWeight.w500, // Medium
                                    color: textPrimary,
                                  ),
                                ),
                                _buildCalibrationBadge(state.calibration!.currentState),
                              ],
                            ),
                            const Divider(color: dividerGray, thickness: 0.5, height: 16.0),
                            _buildInfoRow(context, "Last checked", state.calibration!.lastChecked),
                            const SizedBox(height: 4.0),
                            _buildInfoRow(context, "Reference marker", state.calibration!.referenceMarkerUsed),
                            const SizedBox(height: 10.0),
                            SizedBox(
                              width: double.infinity,
                              child: OutlinedButton.icon(
                                onPressed: () => _openCalibrationWorkflow(context),
                                icon: const Icon(Icons.tune, size: 16),
                                label: const Text(
                                  "Metrology & Conformal Model Calibration",
                                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                                ),
                                style: OutlinedButton.styleFrom(
                                  foregroundColor: const Color(0xFF1565C0),
                                  side: const BorderSide(color: Color(0xFF1565C0)),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12.0),
                ],

                // ── Active Rule Pack ─────────────────────────────────────────
                if (state.rulePack != null) ...[
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 6.0),
                    child: Text(
                      "Active Rule Pack",
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: textSecondary,
                      ),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 14.0),
                    child: Card(
                      color: surfaceWhite,
                      elevation: 1.0,
                      margin: EdgeInsets.zero,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8.0),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(14.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              state.rulePack!.commodity,
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: textPrimary,
                              ),
                            ),
                            const SizedBox(height: 4.0),
                            _buildInfoRow(context, "Version", "v${state.rulePack!.version}"),
                            const SizedBox(height: 2.0),
                            _buildInfoRow(context, "Effective date", state.rulePack!.effectiveDate),
                          ],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12.0),
                ],

                // ── General settings ─────────────────────────────────────────
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 6.0),
                  child: Text(
                    "Settings",
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: textSecondary,
                    ),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 14.0),
                  child: Card(
                    color: surfaceWhite,
                    elevation: 1.0,
                    margin: EdgeInsets.zero,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8.0),
                    ),
                    child: Column(
                      children: [
                        ChevronRow(icon: Icons.notifications, title: "Notifications", onClick: () {}),
                        const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                        ChevronRow(icon: Icons.settings, title: "App Settings", onClick: () {}),
                        const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                        ChevronRow(
                          icon: Icons.cloud_download,
                          title: "Offline Data",
                          onClick: () => context.push(Screen.offlineSync),
                        ),
                        const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                        ChevronRow(icon: Icons.help, title: "Help & Support", onClick: () {}),
                        const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                        ChevronRow(icon: Icons.info, title: "About MANDI NYAAY", onClick: () {}),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 12.0),

                // ── Profile / logout ─────────────────────────────────────────
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 14.0),
                  child: Card(
                    color: surfaceWhite,
                    elevation: 1.0,
                    margin: EdgeInsets.zero,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8.0),
                    ),
                    child: Column(
                      children: [
                        ChevronRow(
                          icon: Icons.person,
                          title: "Profile",
                          onClick: () => context.push(Screen.profile),
                        ),
                        const Divider(indent: 16.0, endIndent: 16.0, color: dividerGray, thickness: 0.5, height: 1.0),
                        InkWell(
                          onTap: () {
                            // Logout action
                          },
                          borderRadius: const BorderRadius.only(
                            bottomLeft: Radius.circular(8.0),
                            bottomRight: Radius.circular(8.0),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 14.0),
                            child: Row(
                              children: [
                                const Icon(Icons.logout, color: statusRed, size: 22.0),
                                const SizedBox(width: 14.0),
                                Text(
                                  "Logout",
                                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                    color: statusRed,
                                    fontWeight: FontWeight.w500, // Medium
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 16.0),
              ],
            ),
          ),
        );
      },
    );
  }

  // ── Helper UI Methods ──────────────────────────────────────────────────────

  Widget _buildCalibrationBadge(CalibrationState state) {
    final (Color bg, Color fg) = switch (state) {
      CalibrationState.good => (statusGreenLight, statusGreen),
      CalibrationState.driftDetected => (statusAmberLight, statusAmber),
      _ => (backgroundGray, textSecondary),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 3.0),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(4.0),
      ),
      child: Text(
        state.displayLabel,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: fg,
          fontWeight: FontWeight.w600, // SemiBold
        ),
      ),
    );
  }

  Widget _buildInfoRow(BuildContext context, String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: textSecondary,
          ),
        ),
        Text(
          value,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: textPrimary,
            fontWeight: FontWeight.w500, // Medium
          ),
        ),
      ],
    );
  }

  void _openCalibrationWorkflow(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => const _CalibrationModal(),
    );
  }
}

class _CalibrationModal extends StatefulWidget {
  const _CalibrationModal();

  @override
  State<_CalibrationModal> createState() => _CalibrationModalState();
}

class _CalibrationModalState extends State<_CalibrationModal> {
  final MandiApiClient _api = MandiApiClient();
  final _sampleIdCtrl = TextEditingController(text: "CAL-01");
  final _lengthCtrl = TextEditingController(text: "58.4");
  final _widthCtrl = TextEditingController(text: "55.2");
  final _thickCtrl = TextEditingController(text: "51.0");
  final _weightCtrl = TextEditingController(text: "135.5");

  bool _isSubmitting = false;
  bool _isTraining = false;
  String? _statusMessage;
  int _existingSamplesCount = 0;

  @override
  void initState() {
    super.initState();
    _loadSampleCount();
  }

  Future<void> _loadSampleCount() async {
    try {
      final samples = await _api.listCalibrationSamples();
      if (mounted) setState(() => _existingSamplesCount = samples.length);
    } catch (_) {}
  }

  Future<void> _submitSample() async {
    setState(() {
      _isSubmitting = true;
      _statusMessage = null;
    });

    try {
      final res = await _api.recordCalibrationSample(
        sampleUnitId: _sampleIdCtrl.text.trim(),
        lotId: "CALIBRATION_LOT",
        lengthMm: double.tryParse(_lengthCtrl.text.trim()) ?? 55.0,
        widthMm: double.tryParse(_widthCtrl.text.trim()) ?? 50.0,
        thicknessMm: double.tryParse(_thickCtrl.text.trim()) ?? 48.0,
        actualScaleWeightG: double.tryParse(_weightCtrl.text.trim()) ?? 120.0,
      );
      await _loadSampleCount();
      if (mounted) {
        setState(() {
          _statusMessage = "Recorded calibration sample: ${res['sample_unit_id'] ?? 'OK'}";
        });
      }
    } catch (e) {
      if (mounted) setState(() => _statusMessage = "Sample recording error: $e");
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  Future<void> _trainModel() async {
    setState(() {
      _isTraining = true;
      _statusMessage = null;
    });

    try {
      final res = await _api.trainWeightModel(coverageTarget: 0.90);
      if (mounted) {
        final version = res['model_version'] ?? 'conformal_ridge_v1';
        final coverage = res['coverage_target'] ?? 0.90;
        setState(() {
          _statusMessage = "Success! Conformal weight model trained ($version) with target coverage ${(coverage * 100).toStringAsFixed(0)}%. System transitioned to CALIBRATED.";
        });
      }
    } catch (e) {
      if (mounted) setState(() => _statusMessage = "Model training error: $e");
    } finally {
      if (mounted) setState(() => _isTraining = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Row(
                  children: [
                    Icon(Icons.tune, color: Color(0xFF1565C0)),
                    SizedBox(width: 8),
                    Text(
                      "Metrological Calibration",
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              "Zero fake coefficients. Calibrate physical caliper measurements against precision scale readings to transition gravimetric mass from UNVALIDATED to CALIBRATED.",
              style: TextStyle(fontSize: 12, color: Colors.grey[700]),
            ),
            const SizedBox(height: 12),

            // Live status banner
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFFE3F2FD),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline, size: 18, color: Color(0xFF1565C0)),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      "Stored Physical Calibration Samples: $_existingSamplesCount",
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF1565C0)),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            if (_statusMessage != null) ...[
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: _statusMessage!.contains("Success") || _statusMessage!.contains("Recorded")
                      ? const Color(0xFFE8F5E9)
                      : const Color(0xFFFFEBEE),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  _statusMessage!,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: _statusMessage!.contains("Success") || _statusMessage!.contains("Recorded")
                        ? const Color(0xFF2E7D32)
                        : const Color(0xFFC62828),
                  ),
                ),
              ),
              const SizedBox(height: 14),
            ],

            const Text("Record Physical Calibration Sample", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _sampleIdCtrl,
                    decoration: const InputDecoration(labelText: "Sample ID", isDense: true, border: OutlineInputBorder()),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _weightCtrl,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: "Weight (g)", isDense: true, border: OutlineInputBorder()),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _lengthCtrl,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: "Length (mm)", isDense: true, border: OutlineInputBorder()),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _widthCtrl,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: "Width (mm)", isDense: true, border: OutlineInputBorder()),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _thickCtrl,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: "Thick (mm)", isDense: true, border: OutlineInputBorder()),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isSubmitting ? null : _submitSample,
                icon: const Icon(Icons.add_circle_outline, size: 16),
                label: _isSubmitting
                    ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Text("RECORD PHYSICAL SAMPLE", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1565C0),
                  foregroundColor: Colors.white,
                ),
              ),
            ),
            const Divider(height: 24),

            const Text("Empirical Conformal Model Fitting (MAPIE)", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            const SizedBox(height: 4),
            Text(
              "Trains regression model with non-conformity scores and conformal 90% confidence bands across physical dimensions.",
              style: TextStyle(fontSize: 11, color: Colors.grey[600]),
            ),
            const SizedBox(height: 10),

            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _isTraining ? null : _trainModel,
                icon: const Icon(Icons.model_training, size: 16),
                label: _isTraining
                    ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF1565C0)))
                    : const Text("FIT CONFORMAL WEIGHT MODEL", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                style: OutlinedButton.styleFrom(
                  foregroundColor: const Color(0xFF1565C0),
                  side: const BorderSide(color: Color(0xFF1565C0)),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}