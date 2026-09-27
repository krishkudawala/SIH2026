import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';

// --- Assumed Imports (Replace with actual paths) ---
// import 'package:mandi_nyaay/ui/components/mandi_top_app_bar.dart';
// import 'package:mandi_nyaay/domain/model/sync_status.dart';
// import 'package:mandi_nyaay/data/fixture/fixture_sync_repository.dart';

// --- Theme Constants Placeholder ---
const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color statusGreen = Color(0xFF4CAF50);
const Color statusOrange = Color(0xFFFF9800);

// --- Mock Data Class (Remove if importing real SyncStatus) ---
class SyncStatus {
  final bool isOnline;
  final int pendingRecords;
  final String? lastSyncedAt;

  const SyncStatus({
    required this.isOnline,
    required this.pendingRecords,
    this.lastSyncedAt,
  });

  SyncStatus copyWith({
    bool? isOnline,
    int? pendingRecords,
    String? lastSyncedAt,
  }) {
    return SyncStatus(
      isOnline: isOnline ?? this.isOnline,
      pendingRecords: pendingRecords ?? this.pendingRecords,
      lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
    );
  }
}

// --- ViewModel ---
class SyncViewModel extends ChangeNotifier {
  // final FixtureSyncRepository _repository = FixtureSyncRepository();

  SyncStatus _syncStatus = const SyncStatus(
    isOnline: true,
    pendingRecords: 3,
    lastSyncedAt: "Sep 21, 2026, 09:42 AM",
  );

  SyncStatus get syncStatus => _syncStatus;

  SyncViewModel() {
    _initObservers();
  }

  void _initObservers() {
    // Mimic the flow observation from FixtureSyncRepository
    // _repository.observeSyncStatus().listen((status) {
    //   _syncStatus = status;
    //   notifyListeners();
    // });
  }

  void triggerSync() {
    // _repository.triggerSync();

    // Mocking the sync update for the UI visualization
    _syncStatus = _syncStatus.copyWith(
      pendingRecords: 0,
      lastSyncedAt: "Just now",
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

  @override
  void initState() {
    super.initState();
    _viewModel = SyncViewModel();
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
        final status = _viewModel.syncStatus;

        return Scaffold(
          backgroundColor: backgroundGray,
          appBar: const MandiTopAppBar(
            title: "Offline Sync",
            showBack: false,
          ),
          body: Padding(
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
              ],
            ),
          ),
        );
      },
    );
  }
}