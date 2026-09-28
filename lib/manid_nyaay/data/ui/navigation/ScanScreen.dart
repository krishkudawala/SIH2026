import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/fixture/lot_repository.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/navigation/screen.dart';

const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;

class ScanScreen extends StatelessWidget {
  const ScanScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final repo = FixtureLotRepository();

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: const MandiTopAppBar(
        title: "Camera & Scan Inspection",
        showBack: false,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(14.0),
              decoration: BoxDecoration(
                color: const Color(0xFFE1F5FE),
                borderRadius: BorderRadius.circular(8.0),
              ),
              child: Row(
                children: [
                  const Icon(Icons.camera_alt, color: institutionalBlue, size: 24.0),
                  const SizedBox(width: 12.0),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "Start Camera Inspection",
                          style: Theme.of(context).textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: institutionalBlue,
                          ),
                        ),
                        const SizedBox(height: 2.0),
                        Text(
                          "Select an active lot below or register a new lot to launch real camera capture.",
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16.0),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  "Active Lots for Inspection",
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: textPrimary,
                  ),
                ),
                TextButton.icon(
                  onPressed: () => context.push(Screen.newLot),
                  icon: const Icon(Icons.add, size: 16),
                  label: const Text("New Lot"),
                ),
              ],
            ),
            const SizedBox(height: 8.0),
            Expanded(
              child: StreamBuilder<List<Lot>>(
                stream: repo.observeActiveLots(),
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting && !snapshot.hasData) {
                    return const Center(child: CircularProgressIndicator());
                  }

                  final activeLots = snapshot.data ?? [];
                  if (activeLots.isEmpty) {
                    return Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.inbox_outlined, size: 48, color: textSecondary),
                          const SizedBox(height: 8),
                          const Text(
                            "No active lots in progress",
                            style: TextStyle(fontWeight: FontWeight.bold, color: textPrimary),
                          ),
                          const SizedBox(height: 4),
                          const Text(
                            "Create a new lot to begin camera capture & AI inspection",
                            style: TextStyle(fontSize: 12, color: textSecondary),
                          ),
                          const SizedBox(height: 16),
                          ElevatedButton.icon(
                            onPressed: () => context.push(Screen.newLot),
                            icon: const Icon(Icons.add_a_photo),
                            label: const Text("Create Lot & Open Camera"),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: institutionalBlue,
                              foregroundColor: Colors.white,
                            ),
                          ),
                        ],
                      ),
                    );
                  }

                  return ListView.separated(
                    itemCount: activeLots.length,
                    separatorBuilder: (context, index) => const SizedBox(height: 8.0),
                    itemBuilder: (context, index) {
                      final lot = activeLots[index];
                      return Card(
                        margin: EdgeInsets.zero,
                        elevation: 1.0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8.0),
                        ),
                        color: surfaceWhite,
                        child: ListTile(
                          contentPadding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                          title: Text(
                            lot.id,
                            style: const TextStyle(fontWeight: FontWeight.bold, color: textPrimary),
                          ),
                          subtitle: Text(
                            "${lot.farmerName} • ${lot.village} (${lot.bagCount} bags)",
                            style: const TextStyle(color: textSecondary),
                          ),
                          trailing: ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: institutionalBlue,
                              foregroundColor: textOnBlue,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(6.0),
                              ),
                            ),
                            onPressed: () {
                              context.push(Screen.createInspectionRoute(lot.id));
                            },
                            child: const Text("OPEN CAMERA"),
                          ),
                        ),
                      );
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
