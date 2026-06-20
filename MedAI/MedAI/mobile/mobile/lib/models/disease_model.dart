// lib/models/disease_model.dart

class Symptom {
  final String id;
  final String name;
  final String? category;
  bool isSelected;

  Symptom({
    required this.id,
    required this.name,
    this.category,
    this.isSelected = false,
  });
}

class DiseaseResult {
  final String name;
  final double confidence;
  final String severity; // 'mild' | 'moderate' | 'severe'
  final String? description;
  final List<String> recommendations;

  const DiseaseResult({
    required this.name,
    required this.confidence,
    required this.severity,
    this.description,
    this.recommendations = const [],
  });

  factory DiseaseResult.fromJson(Map<String, dynamic> json) => DiseaseResult(
    name: json['name'],
    confidence: (json['confidence'] as num).toDouble(),
    severity: json['severity'] ?? 'moderate',
    description: json['description'],
    recommendations: List<String>.from(json['recommendations'] ?? []),
  );
}

class DiagnosisReport {
  final String id;
  final List<String> symptoms;
  final List<DiseaseResult> results;
  final DateTime createdAt;

  const DiagnosisReport({
    required this.id,
    required this.symptoms,
    required this.results,
    required this.createdAt,
  });
}

// Static symptom list — replace with API fetch if needed
class SymptomData {
  static final List<Symptom> all = [
    Symptom(id: 's01', name: 'Fever',           category: 'General'),
    Symptom(id: 's02', name: 'Cough',            category: 'Respiratory'),
    Symptom(id: 's03', name: 'Shortness of breath', category: 'Respiratory'),
    Symptom(id: 's04', name: 'Chest pain',       category: 'Cardiac'),
    Symptom(id: 's05', name: 'Headache',         category: 'Neurological'),
    Symptom(id: 's06', name: 'Fatigue',          category: 'General'),
    Symptom(id: 's07', name: 'Nausea',           category: 'Gastro'),
    Symptom(id: 's08', name: 'Vomiting',         category: 'Gastro'),
    Symptom(id: 's09', name: 'Diarrhea',         category: 'Gastro'),
    Symptom(id: 's10', name: 'Abdominal pain',   category: 'Gastro'),
    Symptom(id: 's11', name: 'Sore throat',      category: 'Respiratory'),
    Symptom(id: 's12', name: 'Runny nose',       category: 'Respiratory'),
    Symptom(id: 's13', name: 'Body aches',       category: 'General'),
    Symptom(id: 's14', name: 'Chills',           category: 'General'),
    Symptom(id: 's15', name: 'Dizziness',        category: 'Neurological'),
    Symptom(id: 's16', name: 'Rash',             category: 'Skin'),
    Symptom(id: 's17', name: 'Swollen lymph nodes', category: 'Immune'),
    Symptom(id: 's18', name: 'Loss of appetite', category: 'General'),
    Symptom(id: 's19', name: 'Joint pain',       category: 'Musculoskeletal'),
    Symptom(id: 's20', name: 'Blurred vision',   category: 'Neurological'),
  ];
}
