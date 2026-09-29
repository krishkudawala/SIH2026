import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/api/api_config.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/work_load_metrics.dart';
import 'package:sih2631/manid_nyaay/data/services/mandi_price_service.dart';
import 'package:sih2631/manid_nyaay/data/services/on_device_inference_service.dart';
import 'package:sih2631/manid_nyaay/data/services/thermal_printer_service.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';

// --- Theme Constants Placeholder ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color statusGreen = Color(0xFF4CAF50);
const Color statusOrange = Color(0xFFFF9800);

// --- ViewModel ---
class SyncViewModel extends ChangeNotifier {
  SyncStatus _syncStatus = SyncStatus(
    isOnline: ApiConfig.isConnectedNotifier.value,
    pendingRecords: 0,
    lastSyncedAt: ApiConfig.isConnectedNotifier.value ? "Live Synchronized" : "Local Air-Gap",
  );

  SyncStatus get syncStatus => _syncStatus;

  SyncViewModel() {
    _initObservers();
  }

  void _initObservers() {
    ApiConfig.isConnectedNotifier.addListener(() {
      final isOnline = ApiConfig.isConnectedNotifier.value;
      _syncStatus = _syncStatus.copyWith(
        isOnline: isOnline,
        lastSyncedAt: isOnline ? "Live Synchronized" : "Local Air-Gap",
      );
      notifyListeners();
    });
  }

  Future<void> triggerSync() async {
    final ok = await ApiConfig.checkConnection();
    _syncStatus = _syncStatus.copyWith(
      isOnline: ok,
      pendingRecords: 0,
      lastSyncedAt: ok ? "Synchronized just now" : "Offline / Unreachable",
    );
    notifyListeners();
  }
}

// --- Screen ---
class OfflineSyncScreen extends StatefulWidget {
  const OfflineSyncScreen({super.key});

  @override
  State<OfflineSyncScreen> createState() => _OfflineSyncScreenState();
}

class _OfflineSyncScreenState extends State<OfflineSyncScreen> {
  late final SyncViewModel _viewModel;
  late final TextEditingController _urlController;
  late final TextEditingController _apiKeyController;
  bool _preferOnDevice = OnDeviceInferenceService.instance.isPreferOnDevice;

  @override
  void initState() {
    super.initState();
    _viewModel = SyncViewModel();
    _urlController = TextEditingController(text: ApiConfig.baseUrl);
    _apiKeyController = TextEditingController(text: MandiPriceService.instance.customApiKey ?? '');
  }

  @override
  void dispose() {
    _urlController.dispose();
    _apiKeyController.dispose();
    _viewModel.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _viewModel,
      builder: (context, _) {
        final status = _viewModel.syncStatus;

        return Scaffold(
          backgroundColor: backgroundGray,
          appBar: const MandiTopAppBar(
            title: "Offline Sync",
            showBack: false,
          ),
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                const SizedBox(height: 24.0),

                // ── Cloud icon ───────────────────────────────────────────────
                Icon(
                  status.isOnline ? Icons.cloud_done : Icons.cloud_off,
                  color: status.isOnline ? statusGreen : institutionalBlue,
                  size: 72.0,
                ),
                const SizedBox(height: 16.0),

                // ── Connectivity Text ────────────────────────────────────────
                Column(
                  children: [
                    Text(
                      status.isOnline ? "You are online" : "You are offline",
                      style: const TextStyle(
                        fontSize: 20.0,
                        fontWeight: FontWeight.bold,
                        color: textPrimary,
                      ),
                    ),
                    const SizedBox(height: 4.0),
                    Text(
                      status.isOnline
                          ? "Device is connected. Sync available."
                          : "Your data will sync when you are online.",
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: textSecondary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16.0),

                // ── Pending records ──────────────────────────────────────────
                Card(
                  margin: EdgeInsets.zero,
                  elevation: 1.0,
                  color: surfaceWhite,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8.0),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(14.0),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.pending,
                          color: status.pendingRecords > 0 ? statusOrange : statusGreen,
                          size: 22.0,
                        ),
                        const SizedBox(width: 12.0),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "Pending Records",
                                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  fontWeight: FontWeight.w500, // Medium
                                  color: textPrimary,
                                ),
                              ),
                              Text(
                                "${status.pendingRecords} inspections awaiting upload",
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: textSecondary,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Text(
                          status.pendingRecords.toString(),
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: status.pendingRecords > 0 ? statusOrange : statusGreen,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16.0),

                // ── Sync Now button ──────────────────────────────────────────
                SizedBox(
                  width: double.infinity,
                  height: 48.0,
                  child: ElevatedButton.icon(
                    onPressed: _viewModel.triggerSync,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: institutionalBlue,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8.0),
                      ),
                    ),
                    icon: const Icon(Icons.sync, color: textOnBlue),
                    label: Text(
                      "SYNC NOW",
                      style: Theme.of(context).textTheme.labelLarge?.copyWith(
                        color: textOnBlue,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16.0),

                // ── Last synced ──────────────────────────────────────────────
                if (status.lastSyncedAt != null)
                  Card(
                    margin: EdgeInsets.zero,
                    elevation: 1.0,
                    color: surfaceWhite,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8.0),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(12.0),
                      child: Row(
                        children: [
                          const Icon(Icons.history, color: textSecondary, size: 18.0),
                          const SizedBox(width: 8.0),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "Last synced",
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: textSecondary,
                                ),
                              ),
                              Text(
                                status.lastSyncedAt!,
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  fontWeight: FontWeight.w500, // Medium
                                  color: textPrimary,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),

                const SizedBox(height: 16.0),

                // ── Server URL Settings ───────────────────────────────────────
                Card(
                  margin: EdgeInsets.zero,
                  elevation: 1.0,
                  color: surfaceWhite,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8.0),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(14.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          "Backend Server URL",
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textPrimary),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          "Connects mobile client to FastAPI inference engine on your local network.",
                          style: TextStyle(fontSize: 11, color: textSecondary),
                        ),
                        const SizedBox(height: 10),
                        Row(
                          children: [
                            Expanded(
                              child: TextField(
                                controller: _urlController,
                                decoration: const InputDecoration(
                                  isDense: true,
                                  border: OutlineInputBorder(),
                                  hintText: "http://<PC_IP>:8000",
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            ElevatedButton(
                              onPressed: () {
                                ApiConfig.setBaseUrl(_urlController.text.trim());
                                _viewModel.triggerSync();
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(content: Text("Server URL updated")),
                                );
                              },
                              style: ElevatedButton.styleFrom(
                                backgroundColor: institutionalBlue,
                                foregroundColor: Colors.white,
                              ),
                              child: const Text("SAVE"),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 16.0),

                // ── On-Device Inference Settings ──────────────────────────────
                Card(
                  margin: EdgeInsets.zero,
                  elevation: 1.0,
                  color: surfaceWhite,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8.0),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(14.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Row(
                              children: [
                                Icon(Icons.bolt, color: Colors.orange, size: 20),
                                SizedBox(width: 8),
                                Text(
                                  "On-Device AI Engine",
                                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textPrimary),
                                ),
                              ],
                            ),
                            Switch(
                              value: _preferOnDevice,
                              activeColor: Colors.orange,
                              onChanged: (val) {
                                setState(() {
                                  _preferOnDevice = val;
                                  OnDeviceInferenceService.instance.isPreferOnDevice = val;
                                });
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text(val ? "Inference set to 100% On-Device (Offline Mobile CPU/NPU)" : "Inference set to Auto (Server with On-Device Fallback)")),
                                );
                              },
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          _preferOnDevice
                              ? "Mobile Native Mode: Runs produce grading directly on phone CPU/NPU without needing a local Wi-Fi PC server."
                              : "Auto Mode: Uses FastAPI ONNX inference when connected, and falls back to On-Device CPU/NPU when offline.",
                          style: const TextStyle(fontSize: 11, color: textSecondary),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 16.0),

                // ── Data.gov.in Agmarknet Settings ───────────────────────────
                Card(
                  margin: EdgeInsets.zero,
                  elevation: 1.0,
                  color: surfaceWhite,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8.0),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(14.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.public, color: institutionalBlue, size: 20),
                            SizedBox(width: 8),
                            Text(
                              "Data.gov.in Agmarknet API",
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textPrimary),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          "Optional Government of India Open Data API key for direct daily APMC modal rates queries.",
                          style: TextStyle(fontSize: 11, color: textSecondary),
                        ),
                        const SizedBox(height: 10),
                        Row(
                          children: [
                            Expanded(
                              child: TextField(
                                controller: _apiKeyController,
                                decoration: const InputDecoration(
                                  isDense: true,
                                  border: OutlineInputBorder(),
                                  hintText: "Enter Data.gov.in API key",
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            ElevatedButton(
                              onPressed: () {
                                MandiPriceService.instance.customApiKey = _apiKeyController.text.trim();
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(content: Text("Data.gov.in API Key saved")),
                                );
                              },
                              style: ElevatedButton.styleFrom(
                                backgroundColor: institutionalBlue,
                                foregroundColor: Colors.white,
                              ),
                              child: const Text("SAVE"),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 16.0),

                // ── Bluetooth Thermal Printer Bridge ─────────────────────────
                Card(
                  margin: EdgeInsets.zero,
                  elevation: 1.0,
                  color: surfaceWhite,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8.0),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(14.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Row(
                              children: [
                                Icon(Icons.print, color: Color(0xFF2E7D32), size: 20),
                                SizedBox(width: 8),
                                Text(
                                  "Thermal Printer Bluetooth Bridge",
                                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textPrimary),
                                ),
                              ],
                            ),
                            Text(
                              ThermalPrinterService.instance.isConnected ? "CONNECTED" : "IDLE",
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: ThermalPrinterService.instance.isConnected ? const Color(0xFF2E7D32) : textSecondary,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          "Directly streams statutory ESC/POS 58mm & 80mm monospace receipts to gate printer.",
                          style: TextStyle(fontSize: 11, color: textSecondary),
                        ),
                        const SizedBox(height: 10),
                        ElevatedButton.icon(
                          onPressed: () async {
                            final ok = await ThermalPrinterService.instance.printAuditSlip(
                              sessionId: 'sess_diag_${DateTime.now().millisecondsSinceEpoch % 1000}',
                              lotId: 'LOT-DIAG-01',
                              farmerName: 'Diagnostics Terminal',
                              grade: 'EXTRA_CLASS',
                              sampleCount: 20,
                              defectRate: 3.2,
                              ciLower: 1.2,
                              ciUpper: 6.8,
                              merkleRoot: 'audit_diagnostic_verification_hash',
                            );
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text(ok ? "ESC/POS test audit slip transmitted successfully" : "Printer transmission failed")),
                              );
                            }
                          },
                          icon: const Icon(Icons.receipt, size: 16),
                          label: const Text("PRINT ESC/POS TEST SLIP"),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF2E7D32),
                            foregroundColor: Colors.white,
                            minimumSize: const Size(double.infinity, 42),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24.0),
              ],
            ),
          ),
        );
      },
    );
  }
}