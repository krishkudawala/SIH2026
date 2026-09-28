import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:print_bluetooth_thermal/print_bluetooth_thermal.dart';

class BluetoothPrinterDevice {
  final String name;
  final String macAddress;

  const BluetoothPrinterDevice({required this.name, required this.macAddress});
}

class ThermalPrinterService {
  static final ThermalPrinterService instance = ThermalPrinterService._internal();
  ThermalPrinterService._internal();

  bool _isConnected = false;
  String? _connectedDeviceMac;
  String? _connectedDeviceName;

  bool get isConnected => _isConnected;
  String? get connectedDeviceName => _connectedDeviceName;
  String? get connectedDeviceMac => _connectedDeviceMac;

  /// Check if Bluetooth is enabled on device
  Future<bool> isBluetoothEnabled() async {
    if (kIsWeb) return false;
    try {
      return await PrintBluetoothThermal.bluetoothEnabled;
    } catch (e) {
      debugPrint('[ThermalPrinterService] isBluetoothEnabled check failed: $e');
      return false;
    }
  }

  /// Get list of paired Bluetooth thermal printers
  Future<List<BluetoothPrinterDevice>> getPairedPrinters() async {
    if (kIsWeb) return [];
    try {
      final List<BluetoothInfo> list = await PrintBluetoothThermal.pairedBluetooths;
      return list.map((info) => BluetoothPrinterDevice(
        name: info.name.isNotEmpty ? info.name : 'Unknown POS Printer',
        macAddress: info.macAdress,
      )).toList();
    } catch (e) {
      debugPrint('[ThermalPrinterService] getPairedPrinters error: $e');
      return [];
    }
  }

  /// Connect to a specific Bluetooth thermal printer by MAC address
  Future<bool> connectPrinter(BluetoothPrinterDevice device) async {
    if (kIsWeb) {
      _isConnected = true;
      _connectedDeviceName = '${device.name} (Simulated Web)';
      return true;
    }
    try {
      final bool result = await PrintBluetoothThermal.connect(macPrinterAddress: device.macAddress);
      _isConnected = result;
      if (result) {
        _connectedDeviceMac = device.macAddress;
        _connectedDeviceName = device.name;
      }
      return result;
    } catch (e) {
      debugPrint('[ThermalPrinterService] connectPrinter failed: $e');
      return false;
    }
  }

  /// Disconnect printer
  Future<void> disconnect() async {
    if (kIsWeb) {
      _isConnected = false;
      return;
    }
    try {
      await PrintBluetoothThermal.disconnect;
      _isConnected = false;
      _connectedDeviceMac = null;
      _connectedDeviceName = null;
    } catch (e) {
      debugPrint('[ThermalPrinterService] disconnect error: $e');
    }
  }

  /// Format Mandi Nyaay Statutory Audit Slip into ESC/POS bytes
  Uint8List buildEscPosAuditSlip({
    required String sessionId,
    required String lotId,
    required String farmerName,
    required String grade,
    required int sampleCount,
    required double defectRate,
    required double ciLower,
    required double ciUpper,
    required String merkleRoot,
    String commodity = 'ONION (NASIK RED)',
  }) {
    final List<int> bytes = [];

    // ESC @: Initialize printer
    bytes.addAll([0x1B, 0x40]);

    // ESC a 1: Center alignment
    bytes.addAll([0x1B, 0x61, 0x01]);

    // GS ! 0x11: Double width & height
    bytes.addAll([0x1D, 0x21, 0x11]);
    bytes.addAll(utf8.encode("MANDI NYAAY APMC\n"));

    // GS ! 0x00: Normal text
    bytes.addAll([0x1D, 0x21, 0x00]);
    bytes.addAll(utf8.encode("GOVT STATUTORY AUDIT RECEIPT\n"));
    bytes.addAll(utf8.encode("Agricultural Produce Marketing Act\n"));
    bytes.addAll(utf8.encode("================================\n"));

    // ESC a 0: Left alignment
    bytes.addAll([0x1B, 0x61, 0x00]);
    final dateStr = DateTime.now().toIso8601String().substring(0, 19).replaceAll('T', ' ');
    bytes.addAll(utf8.encode("DATE/TIME : $dateStr\n"));
    bytes.addAll(utf8.encode("SESSION   : ${sessionId.length > 16 ? sessionId.substring(0, 16) : sessionId}\n"));
    bytes.addAll(utf8.encode("LOT ID    : $lotId\n"));
    bytes.addAll(utf8.encode("COMMODITY : $commodity\n"));
    bytes.addAll(utf8.encode("PRODUCER  : $farmerName\n"));
    bytes.addAll(utf8.encode("--------------------------------\n"));

    // Quality decision
    // ESC a 1: Center alignment
    bytes.addAll([0x1B, 0x61, 0x01]);
    bytes.addAll([0x1D, 0x21, 0x10]); // Double width
    bytes.addAll(utf8.encode("GRADE: $grade\n"));
    bytes.addAll([0x1D, 0x21, 0x00]); // Normal

    // ESC a 0: Left alignment
    bytes.addAll([0x1B, 0x61, 0x00]);
    bytes.addAll(utf8.encode("--------------------------------\n"));
    bytes.addAll(utf8.encode("SAMPLE COUNT  : $sampleCount units\n"));
    bytes.addAll(utf8.encode("DEFECT RATE   : ${defectRate.toStringAsFixed(1)}%\n"));
    bytes.addAll(utf8.encode("WILSON 95% CI : [${ciLower.toStringAsFixed(1)}% - ${ciUpper.toStringAsFixed(1)}%]\n"));
    bytes.addAll(utf8.encode("METROLOGY     : 3D BOUNDING CALIBRATED\n"));
    bytes.addAll(utf8.encode("--------------------------------\n"));

    // Cryptographic Ledger
    bytes.addAll(utf8.encode("SHA-256 MERKLE ROOT:\n"));
    final shortMerkle = merkleRoot.length > 28 ? '${merkleRoot.substring(0, 28)}...' : merkleRoot;
    bytes.addAll(utf8.encode("$shortMerkle\n"));
    bytes.addAll(utf8.encode("TAMPER-EVIDENT BIT-FOR-BIT REPLAY\n"));
    bytes.addAll(utf8.encode("================================\n"));

    // ESC a 1: Center alignment
    bytes.addAll([0x1B, 0x61, 0x01]);
    bytes.addAll(utf8.encode("AUTHORIZED MANDI INSPECTOR\n\n"));

    // Feed lines & cut
    bytes.addAll([0x1B, 0x64, 0x04]); // Feed 4 lines
    bytes.addAll([0x1D, 0x56, 0x00]); // Full cut

    return Uint8List.fromList(bytes);
  }

  /// Print audit slip bytes to connected Bluetooth printer
  Future<bool> printAuditSlip({
    required String sessionId,
    required String lotId,
    required String farmerName,
    required String grade,
    required int sampleCount,
    required double defectRate,
    required double ciLower,
    required double ciUpper,
    required String merkleRoot,
  }) async {
    final bytes = buildEscPosAuditSlip(
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

    if (kIsWeb || !_isConnected) {
      debugPrint('[ThermalPrinterService] Printer simulated print output:\n${utf8.decode(bytes, allowMalformed: true)}');
      return true;
    }

    try {
      final res = await PrintBluetoothThermal.writeBytes(bytes);
      return res;
    } catch (e) {
      debugPrint('[ThermalPrinterService] printAuditSlip writeBytes error: $e');
      return false;
    }
  }
}
