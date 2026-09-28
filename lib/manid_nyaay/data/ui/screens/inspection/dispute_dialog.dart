import 'package:flutter/material.dart';

class DisputeDialog {
  static void showOpenDisputeDialog({
    required BuildContext context,
    required String sessionId,
    required Function(String reason, String openedBy) onSubmit,
  }) {
    final reasonCtrl = TextEditingController();
    String selectedRole = 'LOT_OWNER';

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setState) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.gavel, color: Color(0xFFE65100)),
              SizedBox(width: 8),
              Text("Open Lot Dispute"),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "Initiate formal APMC arbitration challenge for this inspection lot:",
                style: TextStyle(fontSize: 13, color: Color(0xFF64748B)),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: selectedRole,
                decoration: const InputDecoration(labelText: "Challenger Entity"),
                items: const [
                  DropdownMenuItem(value: "LOT_OWNER", child: Text("Farmer / Lot Owner")),
                  DropdownMenuItem(value: "TRADER", child: Text("APMC Commission Agent / Trader")),
                  DropdownMenuItem(value: "SUPERVISOR", child: Text("Mandi Quality Supervisor")),
                ],
                onChanged: (val) => setState(() => selectedRole = val ?? 'LOT_OWNER'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: reasonCtrl,
                decoration: const InputDecoration(
                  labelText: "Statement of Grievance",
                  hintText: "e.g., Grade dispute on defect percentage",
                  border: OutlineInputBorder(),
                ),
                maxLines: 3,
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
                if (reasonCtrl.text.trim().isEmpty) return;
                onSubmit(reasonCtrl.text.trim(), selectedRole);
                Navigator.of(ctx).pop();
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFE65100),
                foregroundColor: Colors.white,
              ),
              child: const Text("SUBMIT DISPUTE"),
            ),
          ],
        ),
      ),
    );
  }

  static void showResolveDisputeDialog({
    required BuildContext context,
    required String sessionId,
    required Function(String finalGrade, String arbitratorId, String notes) onSubmit,
  }) {
    final arbIdCtrl = TextEditingController(text: "APMC_ARBITRATOR_01");
    final notesCtrl = TextEditingController();
    String selectedGrade = 'GRADE_A';

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setState) => AlertDialog(
          title: const Text("APMC Arbitrator Ruling"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: arbIdCtrl,
                decoration: const InputDecoration(labelText: "Arbitrator ID"),
              ),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                value: selectedGrade,
                decoration: const InputDecoration(labelText: "Final Binding Procurement Grade"),
                items: const [
                  DropdownMenuItem(value: "GRADE_A", child: Text("GRADE_A (Procurement Approved)")),
                  DropdownMenuItem(value: "URS", child: Text("URS (Under Recommended Standard)")),
                  DropdownMenuItem(value: "REJECT", child: Text("REJECT (Non-compliant)")),
                ],
                onChanged: (val) => setState(() => selectedGrade = val ?? 'GRADE_A'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: notesCtrl,
                decoration: const InputDecoration(
                  labelText: "Arbitration Ruling Notes",
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
                onSubmit(selectedGrade, arbIdCtrl.text.trim(), notesCtrl.text.trim());
                Navigator.of(ctx).pop();
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF1565C0),
                foregroundColor: Colors.white,
              ),
              child: const Text("RECORD BINDING RULING"),
            ),
          ],
        ),
      ),
    );
  }
}
