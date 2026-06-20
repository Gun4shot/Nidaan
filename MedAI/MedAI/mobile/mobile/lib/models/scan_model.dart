// lib/models/scan_model.dart
enum ScanType { xray, skin, ct, mri, other }

class ScanResult {
  final String id;
  final ScanType type;
  final String finding;
  final double confidence;
  final String severity;
  final List<String> recommendations;
  final DateTime createdAt;

  const ScanResult({
    required this.id,
    required this.type,
    required this.finding,
    required this.confidence,
    required this.severity,
    this.recommendations = const [],
    required this.createdAt,
  });

  factory ScanResult.fromJson(Map<String, dynamic> json) => ScanResult(
    id: json['id'] ?? '',
    type: ScanType.values.firstWhere(
      (e) => e.name == json['type'],
      orElse: () => ScanType.other,
    ),
    finding: json['finding'],
    confidence: (json['confidence'] as num).toDouble(),
    severity: json['severity'] ?? 'moderate',
    recommendations: List<String>.from(json['recommendations'] ?? []),
    createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
  );

  String get typeLabel {
    switch (type) {
      case ScanType.xray: return 'X-Ray';
      case ScanType.skin: return 'Skin Scan';
      case ScanType.ct:   return 'CT Scan';
      case ScanType.mri:  return 'MRI';
      default:            return 'Medical Scan';
    }
  }
}
