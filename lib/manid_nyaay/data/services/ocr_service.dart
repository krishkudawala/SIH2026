import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:sih2631/manid_nyaay/data/api/api_client.dart';

class WeighbridgeOcrResult {
  final double? grossWeightKg;
  final double? tareWeightKg;
  final double? netWeightKg;
  final String? vehicleNumber;
  final String? slipId;
  final String? farmerName;
  final double confidence;
  final String rawText;
  final String engineUsed; // 'GOOGLE_MLKIT_ON_DEVICE' or 'BACKEND_OCR'

  const WeighbridgeOcrResult({
    this.grossWeightKg,
    this.tareWeightKg,
    this.netWeightKg,
    this.vehicleNumber,
    this.slipId,
    this.farmerName,
    required this.confidence,
    required this.rawText,
    required this.engineUsed,
  });

  Map<String, dynamic> toMap() => {
    'gross_weight_kg': grossWeightKg,
    'tare_weight_kg': tareWeightKg,
    'net_weight_kg': netWeightKg,
    'vehicle_number': vehicleNumber,
    'slip_id': slipId,
    'farmer_name': farmerName,
    'confidence': confidence,
    'raw_text': rawText,
    'engine_used': engineUsed,
  };
}

class OcrService {
  static final OcrService instance = OcrService._internal();
  OcrService._internal();

  /// Scans a weighbridge receipt image using Native On-Device ML Kit (Android/iOS)
  /// with automatic fallback to Backend Tesseract/OpenCV on Web or Desktop.
  Future<WeighbridgeOcrResult> scanWeighbridgeSlip({
    String? filePath,
    Uint8List? imageBytes,
    String? base64Image,
  }) async {
    // 1. Try On-Device ML Kit first on mobile devices (Android/iOS)
    if (!kIsWeb && filePath != null && (defaultTargetPlatform == TargetPlatform.android || defaultTargetPlatform == TargetPlatform.iOS)) {
      try {
        final onDeviceResult = await _runOnDeviceMlKit(filePath);
        if (onDeviceResult != null && (onDeviceResult.netWeightKg != null || onDeviceResult.vehicleNumber != null || onDeviceResult.slipId != null)) {
          return onDeviceResult;
        }
      } catch (e) {
        debugPrint('[OcrService] On-Device ML Kit failed, falling back to backend: $e');
      }
    }

    // 2. Fallback to Mandi Nyaay Backend OCR
    try {
      String? b64 = base64Image;
      if (b64 == null && imageBytes != null) {
        b64 = base64Encode(imageBytes);
      }

      final backendRes = await MandiApiClient().scanOcr(
        imagePath: filePath,
        imageBase64: b64,
      );

      final candidates = backendRes['candidates'] as List<dynamic>? ?? [];
      double? gross;
      double? tare;
      double? net;
      String? vehicle;
      String? slip;
      String? farmer;

      for (final c in candidates) {
        final field = c['field_type']?.toString();
        final text = c['text']?.toString() ?? '';
        final val = double.tryParse(text.replaceAll(RegExp(r'[^\d.]'), ''));

        if (field == 'GROSS_WEIGHT' && val != null) gross = val;
        if (field == 'TARE_WEIGHT' && val != null) tare = val;
        if (field == 'NET_WEIGHT' && val != null) net = val;
        if (field == 'VEHICLE_NUMBER') vehicle = text;
        if (field == 'SLIP_ID') slip = text;
        if (field == 'FARMER_NAME') farmer = text;
      }

      // If net was not explicitly tagged, calculate gross - tare if available
      if (net == null && gross != null && tare != null && gross > tare) {
        net = gross - tare;
      }

      return WeighbridgeOcrResult(
        grossWeightKg: gross,
        tareWeightKg: tare,
        netWeightKg: net,
        vehicleNumber: vehicle,
        slipId: slip,
        farmerName: farmer,
        confidence: 0.90,
        rawText: backendRes['raw_text']?.toString() ?? 'Processed via Mandi Nyaay Backend OCR',
        engineUsed: 'BACKEND_OCR (TESSERACT)',
      );
    } catch (e) {
      debugPrint('[OcrService] Backend OCR also failed: $e');
      // Graceful default extraction
      return const WeighbridgeOcrResult(
        grossWeightKg: null,
        tareWeightKg: null,
        netWeightKg: null,
        vehicleNumber: null,
        slipId: null,
        farmerName: null,
        confidence: 0.0,
        rawText: 'OCR could not process image',
        engineUsed: 'FALLBACK',
      );
    }
  }

  Future<WeighbridgeOcrResult?> _runOnDeviceMlKit(String filePath) async {
    final inputImage = InputImage.fromFilePath(filePath);
    final textRecognizer = TextRecognizer(script: TextRecognitionScript.devanagiri);

    try {
      final RecognizedText recognizedText = await textRecognizer.processImage(inputImage);
      final raw = recognizedText.text;

      if (raw.trim().isEmpty) return null;

      double? gross;
      double? tare;
      double? net;
      String? vehicle;
      String? slip;
      String? farmer;

      // Extract fields with multi-lingual patterns (English, Hindi, Marathi)
      for (final block in recognizedText.blocks) {
        for (final line in block.lines) {
          final text = line.text.trim();

          // Net Weight: "Net Wt", "Net", "निव्वळ", "नेट"
          if (RegExp(r'(net|निव्वळ|नेट|काटा)\s*(wt|weight|वजन)?[:\-\s]*([\d,.]+)', caseSensitive: false).hasMatch(text)) {
            final match = RegExp(r'([\d,]+(?:\.\d+)?)').firstMatch(text);
            if (match != null) {
              net = double.tryParse(match.group(1)!.replaceAll(',', ''));
            }
          }

          // Gross Weight: "Gross", "सकल", "ग्रॉस", "कुल"
          if (RegExp(r'(gross|सकल|ग्रॉस|कुल)\s*(wt|weight|वजन)?[:\-\s]*([\d,.]+)', caseSensitive: false).hasMatch(text)) {
            final match = RegExp(r'([\d,]+(?:\.\d+)?)').firstMatch(text);
            if (match != null) {
              gross = double.tryParse(match.group(1)!.replaceAll(',', ''));
            }
          }

          // Tare Weight: "Tare", "रिकामे", "टेअर"
          if (RegExp(r'(tare|रिकामे|टेअर)\s*(wt|weight|वजन)?[:\-\s]*([\d,.]+)', caseSensitive: false).hasMatch(text)) {
            final match = RegExp(r'([\d,]+(?:\.\d+)?)').firstMatch(text);
            if (match != null) {
              tare = double.tryParse(match.group(1)!.replaceAll(',', ''));
            }
          }

          // Vehicle Number: "MH 15 AB 1234", "गाडी क्र."
          if (RegExp(r'[A-Z]{2}[-\s]?[0-9]{1,2}[-\s]?[A-Z]{1,3}[-\s]?[0-9]{4}', caseSensitive: false).hasMatch(text)) {
            final match = RegExp(r'([A-Z]{2}[-\s]?[0-9]{1,2}[-\s]?[A-Z]{1,3}[-\s]?[0-9]{4})', caseSensitive: false).firstMatch(text);
            if (match != null) {
              vehicle = match.group(1)?.toUpperCase();
            }
          }

          // Slip No: "Slip", "पावती", "Token"
          if (RegExp(r'(slip|पावती|token|ticket|receipt)\s*(no|num|cr|क्र)?[:\-\s]*([A-Za-z0-9\-]+)', caseSensitive: false).hasMatch(text)) {
            final match = RegExp(r'([0-9]{3,})').firstMatch(text);
            if (match != null) {
              slip = match.group(1);
            }
          }

          // Farmer: "Farmer", "शेतकरी"
          if (RegExp(r'(farmer|शेतकरी|नाव|name)[:\-\s]*([A-Za-z\u0900-\u097F\s]+)', caseSensitive: false).hasMatch(text)) {
            final parts = text.split(RegExp(r'[:\-]'));
            if (parts.length > 1 && parts[1].trim().isNotEmpty) {
              farmer = parts[1].trim();
            }
          }
        }
      }

      if (net == null && gross != null && tare != null && gross > tare) {
        net = gross - tare;
      }

      return WeighbridgeOcrResult(
        grossWeightKg: gross,
        tareWeightKg: tare,
        netWeightKg: net,
        vehicleNumber: vehicle,
        slipId: slip,
        farmerName: farmer,
        confidence: 0.95,
        rawText: raw,
        engineUsed: 'GOOGLE_MLKIT_ON_DEVICE (NATIVE)',
      );
    } finally {
      await textRecognizer.close();
    }
  }
}
