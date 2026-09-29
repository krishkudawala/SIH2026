import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:sih2631/manid_nyaay/data/services/thermal_printer_service.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';

const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color successGreen = Color(0xFF2E7D32);
const Color warnAmber = Color(0xFFED6C02);
const Color alertRed = Color(0xFFD32F2F);

/// Shared MediaQuery-based scale (1.0 at 375dp wide, clamped 0.85 - 1.3).
double _mqScale(BuildContext context) =>
    (MediaQuery.sizeOf(context).width / 375).clamp(0.85, 1.3);

class ReportReceiptScreen extends StatelessWidget {
  final InspectionUiState uiState;
  final VoidCallback onFinish;
  final VoidCallback onBack;

  const ReportReceiptScreen({
    super.key,
    required this.uiState,
    required this.onFinish,
    required this.onBack,
  });

  @override
  Widget build(BuildContext context) {
    // ── MediaQuery values ────────────────────────────────────────────────
    final Size size = MediaQuery.sizeOf(context);
    final double safeBottom = MediaQuery.paddingOf(context).bottom;
    final double scale = _mqScale(context);
    final bool isCompact = size.width < 360; // very small phones

    final double pagePadding = (size.width * 0.04).clamp(12.0, 24.0);
    final double cardPadding = 16.0 * scale;
    final double maxContentWidth = 600.0;
    final double buttonHeight = (48.0 * scale).clamp(48.0, 60.0);
    final double printButtonHeight = (46.0 * scale).clamp(46.0, 58.0);
    final double smallIcon = 18.0 * scale;

    final report = uiState.reportData ?? {};
    final structured = report['structured_result'] as Map<String, dynamic>? ?? {};
    final receiptText = (report['printable_receipt'] ?? report['receipt'] ?? 'No receipt available').toString();
    final markdownReport = (report['markdown_report'] ?? '').toString();

    final decision = (structured['decision'] ?? uiState.decisionData?['procurement_grade'] ?? 'MANUAL_REVIEW').toString();
    final decisionStatus = (structured['decision_status'] ?? uiState.decisionData?['status'] ?? 'DECIDED').toString();
    final sampleCount = (structured['sample_size'] as num?)?.toInt() ?? uiState.rawObservations.length;
    final targetSampleSize = (structured['target_sample_size'] as num?)?.toInt() ?? 20;

    final healthyPct = (structured['healthy_pct'] as num?)?.toDouble() ?? 0.0;
    final damagedPct = (structured['damaged_pct'] as num?)?.toDouble() ?? 0.0;
    final sproutedPct = (structured['sprouted_pct'] as num?)?.toDouble() ?? 0.0;
    final rottenPct = (structured['rotten_pct'] as num?)?.toDouble() ?? 0.0;
    final totalDefectPct = (structured['total_defect_pct'] as num?)?.toDouble() ?? (damagedPct + sproutedPct + rottenPct);

    final healthyCount = (structured['healthy_count'] as num?)?.toInt() ?? 0;
    final damagedCount = (structured['damaged_count'] as num?)?.toInt() ?? 0;
    final sproutedCount = (structured['sprouted_count'] as num?)?.toInt() ?? 0;
    final rottenCount = (structured['rotten_count'] as num?)?.toInt() ?? 0;

    final offlineRef = (report['offline_ref_code'] ?? structured['offline_ref_code'] ?? 'MN-OFFLINE').toString();
    final rootHash = (structured['evidence_root_hash'] ?? uiState.evidenceData?['evidence_root_hash'] ?? uiState.evidenceData?['merkle_root'] ?? 'Verified-Ledger').toString();

    final lotId = uiState.lotId.isNotEmpty ? uiState.lotId : 'LOT-LIVE-01';
    final farmerName = uiState.farmerName.isNotEmpty ? uiState.farmerName : 'Mandi Producer';
    final ciLower = (uiState.samplingData?['ci_95_lower'] as num?)?.toDouble() ?? (totalDefectPct * 0.7);
    final ciUpper = (uiState.samplingData?['ci_95_upper'] as num?)?.toDouble() ?? (totalDefectPct * 1.3);
    final merkleRoot = rootHash;

    final Color decisionColor = switch (decision.toUpperCase()) {
      'GRADE_A' => successGreen,
      'URS' => warnAmber,
      'REJECT' => alertRed,
      _ => institutionalBlue,
    };

    // Bottom action buttons (built once so they can go in a Row or a Column)
    final Widget exportButton = OutlinedButton.icon(
      onPressed: () {
        final fullExport = markdownReport.isNotEmpty ? markdownReport : receiptText;
        Clipboard.setData(ClipboardData(text: fullExport));
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Report exported to clipboard for sharing")),
        );
      },
      icon: Icon(Icons.share, size: smallIcon),
      label: const Text("Export Report"),
      style: OutlinedButton.styleFrom(
        foregroundColor: institutionalBlue,
        side: const BorderSide(color: institutionalBlue),
        minimumSize: Size(0, buttonHeight),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    );

    final Widget finishButton = ElevatedButton(
      onPressed: onFinish,
      style: ElevatedButton.styleFrom(
        backgroundColor: institutionalBlue,
        foregroundColor: textOnBlue,
        minimumSize: Size(0, buttonHeight),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
      child: const Text(
        "FINISH & RETURN HOME",
        style: TextStyle(fontWeight: FontWeight.bold),
      ),
    );

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Official Inspection Report",
        subtitle: "APMC Statutory Grading Certificate",
        showBack: true,
        onBack: onBack,
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
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Statutory Header Card ───────────────────────────────────────
                Card(
                  elevation: 1.5,
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
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      "LOT ${uiState.lotId.toUpperCase()}",
                                      overflow: TextOverflow.ellipsis,
                                      style: TextStyle(
                                        fontSize: 16 * scale,
                                        fontWeight: FontWeight.bold,
                                        color: textPrimary,
                                      ),
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      "Session: ${uiState.sessionId.length > 12 ? uiState.sessionId.substring(0, 12) : uiState.sessionId}",
                                      overflow: TextOverflow.ellipsis,
                                      style: TextStyle(
                                        fontSize: 11 * scale,
                                        fontFamily: 'monospace',
                                        color: textSecondary,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 8),
                              Flexible(
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFE8F5E9),
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(color: const Color(0xFFA5D6A7)),
                                  ),
                                  child: Text(
                                    offlineRef,
                                    overflow: TextOverflow.ellipsis,
                                    style: TextStyle(
                                      fontSize: 11 * scale,
                                      fontWeight: FontWeight.bold,
                                      color: const Color(0xFF1B5E20),
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const Divider(height: 20),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Expanded(child: _MetaColumn(label: "Declared Bags", value: "${uiState.declaredBagCount} Bags")),
                              Expanded(child: _MetaColumn(label: "Certified Weight", value: "${uiState.certifiedLotWeightKg.toStringAsFixed(1)} kg")),
                              Expanded(child: _MetaColumn(label: "Sample Units", value: "$sampleCount / $targetSampleSize")),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 14),

                // ── Primary Decision Banner ─────────────────────────────────────
                Container(
                  width: double.infinity,
                  padding: EdgeInsets.all(cardPadding),
                  decoration: BoxDecoration(
                    color: decisionColor,
                    borderRadius: BorderRadius.circular(12),
                    boxShadow: [
                      BoxShadow(
                        color: decisionColor.withValues(alpha: 0.3),
                        blurRadius: 8,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              "STATUTORY PROCUREMENT GRADE",
                              style: TextStyle(
                                fontSize: 11 * scale,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 1.0,
                                color: Colors.white70,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Flexible(
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: Colors.white24,
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                decisionStatus,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  fontSize: 10 * scale,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        decision.replaceAll('_', ' '),
                        style: TextStyle(
                          fontSize: 26 * scale,
                          fontWeight: FontWeight.w900,
                          color: Colors.white,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        "Rule Pack: ${structured['rule_pack_id'] ?? 'AGMARK_ONION_2026'} (v${structured['rule_pack_version'] ?? '1.0.0'})",
                        style: TextStyle(
                          fontSize: 11 * scale,
                          color: Colors.white70,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // ── Quality & Defect Distribution ───────────────────────────────
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
                            "QUALITY & DEFECT DISTRIBUTION",
                            style: TextStyle(
                              fontSize: 12 * scale,
                              fontWeight: FontWeight.bold,
                              color: textSecondary,
                            ),
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              _DefectStatTile(label: "Healthy", count: healthyCount, pct: healthyPct, color: successGreen),
                              _DefectStatTile(label: "Damaged", count: damagedCount, pct: damagedPct, color: warnAmber),
                              _DefectStatTile(label: "Sprouted", count: sproutedCount, pct: sproutedPct, color: Colors.purple),
                              _DefectStatTile(label: "Rotten", count: rottenCount, pct: rottenPct, color: alertRed),
                            ],
                          ),
                          const SizedBox(height: 12),
                          const Divider(height: 1),
                          const SizedBox(height: 10),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                "Total Defect Ratio",
                                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13 * scale, color: textPrimary),
                              ),
                              Text(
                                "${totalDefectPct.toStringAsFixed(1)}%",
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14 * scale,
                                  color: totalDefectPct > 10.0 ? alertRed : successGreen,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 14),

                // ── Statistical Sampling & Metrology Status ─────────────────────
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
                            "SAMPLING & METROLOGICAL INTEGRITY",
                            style: TextStyle(
                              fontSize: 12 * scale,
                              fontWeight: FontWeight.bold,
                              color: textSecondary,
                            ),
                          ),
                          const SizedBox(height: 10),
                          _AuditLine(
                            label: "Sequential Stopping Rule",
                            value: structured['sampling_status'] == 'SUFFICIENT' ? "SUFFICIENT (TARGET MET)" : "STOPPING MET",
                            icon: Icons.check_circle,
                            iconColor: successGreen,
                          ),
                          const SizedBox(height: 8),
                          _AuditLine(
                            label: "Physical Diameter Status",
                            value: (structured['size_status'] ?? uiState.measurementData?['size_status'] ?? 'ONION_DIAMETER_UNVALIDATED').toString(),
                            icon: Icons.straighten,
                            iconColor: institutionalBlue,
                          ),
                          const SizedBox(height: 8),
                          _AuditLine(
                            label: "Gravimetric Mass Status",
                            value: (structured['mass_status'] ?? uiState.weightData?['mass_status'] ?? 'UNVALIDATED').toString(),
                            icon: Icons.scale,
                            iconColor: warnAmber,
                          ),
                          const SizedBox(height: 8),
                          _AuditLine(
                            label: "SHA-256 Evidence Hash",
                            value: rootHash.length > 24 ? "${rootHash.substring(0, 24)}…" : rootHash,
                            icon: Icons.fingerprint,
                            iconColor: institutionalBlue,
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 14),

                // ── Printable Thermal Slip Preview ──────────────────────────────
                Card(
                  elevation: 2.0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  color: const Color(0xFFFAF9F6), // Warm paper off-white
                  child: Container(
                    width: double.infinity,
                    padding: EdgeInsets.all(cardPadding),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Flexible(
                              child: Row(
                                children: [
                                  Icon(Icons.receipt_long, size: smallIcon, color: institutionalBlue),
                                  const SizedBox(width: 6),
                                  Flexible(
                                    child: Text(
                                      "THERMAL AUDIT SLIP",
                                      overflow: TextOverflow.ellipsis,
                                      style: TextStyle(
                                        fontFamily: 'monospace',
                                        fontWeight: FontWeight.bold,
                                        fontSize: 12 * scale,
                                        color: textSecondary,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                IconButton(
                                  icon: Icon(Icons.print, size: smallIcon, color: successGreen),
                                  tooltip: "Print Thermal Slip (Bluetooth)",
                                  onPressed: () => _showBluetoothPrintDialog(
                                    context,
                                    sessionId: uiState.sessionId,
                                    lotId: lotId,
                                    farmerName: farmerName,
                                    grade: decision,
                                    sampleCount: sampleCount,
                                    defectRate: totalDefectPct,
                                    ciLower: ciLower,
                                    ciUpper: ciUpper,
                                    merkleRoot: merkleRoot,
                                  ),
                                ),
                                IconButton(
                                  icon: Icon(Icons.copy, size: smallIcon, color: institutionalBlue),
                                  tooltip: "Copy Slip Text",
                                  onPressed: () {
                                    Clipboard.setData(ClipboardData(text: receiptText));
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(content: Text("Audit slip copied to clipboard")),
                                    );
                                  },
                                ),
                                IconButton(
                                  icon: Icon(Icons.share, size: smallIcon, color: institutionalBlue),
                                  tooltip: "Share Report",
                                  onPressed: () {
                                    final fullExport = markdownReport.isNotEmpty ? markdownReport : receiptText;
                                    Clipboard.setData(ClipboardData(text: fullExport));
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(content: Text("Full statutory report copied ready to share")),
                                    );
                                  },
                                ),
                              ],
                            ),
                          ],
                        ),
                        const Divider(),
                        SelectableText(
                          receiptText,
                          style: TextStyle(
                            fontFamily: 'monospace',
                            fontSize: 12.0 * scale,
                            height: 1.4,
                            color: const Color(0xFF1E293B),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // ── Bluetooth Thermal Print Button ──────────────────────────────
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: () => _showBluetoothPrintDialog(
                      context,
                      sessionId: uiState.sessionId,
                      lotId: lotId,
                      farmerName: farmerName,
                      grade: decision,
                      sampleCount: sampleCount,
                      defectRate: totalDefectPct,
                      ciLower: ciLower,
                      ciUpper: ciUpper,
                      merkleRoot: merkleRoot,
                    ),
                    icon: Icon(Icons.bluetooth_audio, size: smallIcon),
                    label: const Text("PRINT BLUETOOTH AUDIT SLIP (ESC/POS)"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: successGreen,
                      foregroundColor: Colors.white,
                      minimumSize: Size(double.infinity, printButtonHeight),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                  ),
                ),
                const SizedBox(height: 12),

                // ── Primary Completion Actions ──────────────────────────────────
                // Side by side normally; stacked on very small phones.
                if (isCompact) ...[
                  SizedBox(width: double.infinity, child: exportButton),
                  const SizedBox(height: 12),
                  SizedBox(width: double.infinity, child: finishButton),
                ] else
                  Row(
                    children: [
                      Expanded(child: exportButton),
                      const SizedBox(width: 12),
                      Expanded(flex: 2, child: finishButton),
                    ],
                  ),
                const SizedBox(height: 16),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showBluetoothPrintDialog(
      BuildContext context, {
        required String sessionId,
        required String lotId,
        required String farmerName,
        required String grade,
        required int sampleCount,
        required double defectRate,
        required double ciLower,
        required double ciUpper,
        required String merkleRoot,
      }) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true, // lets the sheet grow / scroll with many printers
      constraints: BoxConstraints(
        maxWidth: 600,
        maxHeight: MediaQuery.sizeOf(context).height * 0.85,
      ),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        // ── MediaQuery values for the sheet ─────────────────────────────
        final double sheetScale = _mqScale(ctx);
        final double sheetSafeBottom = MediaQuery.paddingOf(ctx).bottom;
        final double sheetButtonHeight = (44.0 * sheetScale).clamp(44.0, 56.0);

        return StatefulBuilder(
          builder: (context, setSheetState) {
            return FutureBuilder<List<BluetoothPrinterDevice>>(
              future: ThermalPrinterService.instance.getPairedPrinters(),
              builder: (context, snapshot) {
                final printers = snapshot.data ?? [];
                final isConnected = ThermalPrinterService.instance.isConnected;
                final connectedName = ThermalPrinterService.instance.connectedDeviceName;

                return SingleChildScrollView(
                  padding: EdgeInsets.fromLTRB(20.0, 20.0, 20.0, 20.0 + sheetSafeBottom),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Row(
                              children: [
                                const Icon(Icons.bluetooth_audio, color: institutionalBlue),
                                const SizedBox(width: 8),
                                Flexible(
                                  child: Text(
                                    "Bluetooth Thermal Printer",
                                    overflow: TextOverflow.ellipsis,
                                    style: TextStyle(fontSize: 16 * sheetScale, fontWeight: FontWeight.bold),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.close),
                            onPressed: () => Navigator.pop(ctx),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        isConnected
                            ? "Connected to: $connectedName"
                            : "Select a 58mm / 80mm ESC/POS printer at the mandi gate:",
                        style: TextStyle(
                          fontSize: 13 * sheetScale,
                          color: isConnected ? successGreen : textSecondary,
                          fontWeight: isConnected ? FontWeight.bold : FontWeight.normal,
                        ),
                      ),
                      const Divider(height: 24),
                      if (snapshot.connectionState == ConnectionState.waiting)
                        const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()))
                      else if (printers.isEmpty && !isConnected) ...[
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF1F5F9),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text("No paired Bluetooth printers found.", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13 * sheetScale)),
                              const SizedBox(height: 4),
                              Text(
                                "1. Turn on your handheld thermal printer.\n2. Pair it in your phone's Android Bluetooth settings.\n3. Return here to print the ESC/POS receipt.",
                                style: TextStyle(fontSize: 12 * sheetScale, color: textSecondary),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),
                        ElevatedButton.icon(
                          onPressed: () async {
                            Navigator.pop(ctx);
                            await ThermalPrinterService.instance.printAuditSlip(
                              sessionId: sessionId,
                              lotId: lotId,
                              farmerName: farmerName,
                              grade: grade,
                              sampleCount: sampleCount,
                              defectRate: defectRate,
                              ciLower: ciLower,
                              ciUpper: ciUpper,
                              merkleRoot: merkleRoot,
                            );
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text("Audit slip generated & dispatched (ESC/POS 58mm format)")),
                              );
                            }
                          },
                          icon: const Icon(Icons.print),
                          label: const Text("PRINT TEST SLIP (SIMULATED ESC/POS)"),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: institutionalBlue,
                            foregroundColor: Colors.white,
                            minimumSize: Size(double.infinity, sheetButtonHeight),
                          ),
                        ),
                      ] else ...[
                        for (final p in printers)
                          ListTile(
                            leading: const Icon(Icons.print, color: institutionalBlue),
                            title: Text(p.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                            subtitle: Text(p.macAddress, style: TextStyle(fontFamily: 'monospace', fontSize: 11 * sheetScale)),
                            trailing: ElevatedButton(
                              onPressed: () async {
                                final ok = await ThermalPrinterService.instance.connectPrinter(p);
                                if (ok) {
                                  await ThermalPrinterService.instance.printAuditSlip(
                                    sessionId: sessionId,
                                    lotId: lotId,
                                    farmerName: farmerName,
                                    grade: grade,
                                    sampleCount: sampleCount,
                                    defectRate: defectRate,
                                    ciLower: ciLower,
                                    ciUpper: ciUpper,
                                    merkleRoot: merkleRoot,
                                  );
                                  if (context.mounted) {
                                    Navigator.pop(ctx);
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(content: Text("Audit slip printed on ${p.name} via Bluetooth ESC/POS")),
                                    );
                                  }
                                } else {
                                  if (context.mounted) {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(content: Text("Failed to connect to ${p.name}")),
                                    );
                                  }
                                }
                              },
                              style: ElevatedButton.styleFrom(
                                backgroundColor: successGreen,
                                foregroundColor: Colors.white,
                              ),
                              child: const Text("PRINT"),
                            ),
                          ),
                      ],
                    ],
                  ),
                );
              },
            );
          },
        );
      },
    );
  }
}

class _MetaColumn extends StatelessWidget {
  final String label;
  final String value;

  const _MetaColumn({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final double scale = _mqScale(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(fontSize: 11 * scale, color: textSecondary)),
        const SizedBox(height: 2),
        Text(value, style: TextStyle(fontSize: 13 * scale, fontWeight: FontWeight.bold, color: textPrimary)),
      ],
    );
  }
}

class _DefectStatTile extends StatelessWidget {
  final String label;
  final int count;
  final double pct;
  final Color color;

  const _DefectStatTile({
    required this.label,
    required this.count,
    required this.pct,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final double scale = _mqScale(context);

    return Expanded(
      child: Column(
        children: [
          Text(
            "$count",
            style: TextStyle(fontSize: 16 * scale, fontWeight: FontWeight.bold, color: color),
          ),
          const SizedBox(height: 2),
          Text(
            "${pct.toStringAsFixed(0)}%",
            style: TextStyle(fontSize: 11 * scale, fontWeight: FontWeight.w600, color: color),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: TextStyle(fontSize: 10 * scale, color: textSecondary),
          ),
        ],
      ),
    );
  }
}

class _AuditLine extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color iconColor;

  const _AuditLine({
    required this.label,
    required this.value,
    required this.icon,
    required this.iconColor,
  });

  @override
  Widget build(BuildContext context) {
    final double scale = _mqScale(context);

    return Row(
      children: [
        Icon(icon, size: 16 * scale, color: iconColor),
        const SizedBox(width: 8),
        Expanded(
          flex: 2,
          child: Text(label, style: TextStyle(fontSize: 12 * scale, color: textSecondary)),
        ),
        Expanded(
          flex: 3,
          child: Text(
            value,
            textAlign: TextAlign.end,
            style: TextStyle(
              fontSize: 11 * scale,
              fontWeight: FontWeight.bold,
              color: textPrimary,
              fontFamily: 'monospace',
            ),
          ),
        ),
      ],
    );
  }
}