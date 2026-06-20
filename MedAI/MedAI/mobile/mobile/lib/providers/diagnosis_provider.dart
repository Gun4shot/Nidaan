// lib/providers/diagnosis_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/disease_model.dart';
import '../models/scan_model.dart';
import '../services/api_service.dart';
import 'dart:io';

// ──────────────────────────────────────────────
// Diagnosis State
// ──────────────────────────────────────────────
enum DiagStatus { idle, loading, success, error }

class DiagnosisState {
  final List<Symptom> symptoms;
  final List<DiseaseResult> results;
  final DiagStatus status;
  final String? error;

  DiagnosisState({
    List<Symptom>? symptoms,
    this.results = const [],
    this.status  = DiagStatus.idle,
    this.error,
  }) : symptoms = symptoms ?? SymptomData.all.map((s) => Symptom(
          id: s.id, name: s.name, category: s.category)).toList();

  DiagnosisState copyWith({
    List<Symptom>? symptoms,
    List<DiseaseResult>? results,
    DiagStatus? status,
    String? error,
  }) => DiagnosisState(
    symptoms: symptoms ?? this.symptoms,
    results:  results  ?? this.results,
    status:   status   ?? this.status,
    error:    error,
  );

  List<Symptom> get selected => symptoms.where((s) => s.isSelected).toList();
}

class DiagnosisNotifier extends StateNotifier<DiagnosisState> {
  final ApiService _api;
  DiagnosisNotifier(this._api) : super(DiagnosisState());

  void toggleSymptom(String id) {
    final updated = state.symptoms.map((s) {
      if (s.id == id) return Symptom(id: s.id, name: s.name,
          category: s.category, isSelected: !s.isSelected);
      return s;
    }).toList();
    state = state.copyWith(symptoms: updated, results: [], status: DiagStatus.idle);
  }

  void clearAll() {
    state = DiagnosisState();
  }

  Future<void> predict() async {
    final selected = state.selected.map((s) => s.name).toList();
    if (selected.isEmpty) return;

    state = state.copyWith(status: DiagStatus.loading, error: null);
    try {
      final results = await _api.predictDisease(selected);
      state = state.copyWith(results: results, status: DiagStatus.success);
    } catch (e) {
      state = state.copyWith(status: DiagStatus.error, error: e.toString());
    }
  }
}

final diagnosisProvider =
    StateNotifierProvider<DiagnosisNotifier, DiagnosisState>((ref) {
  return DiagnosisNotifier(ref.read(
      Provider<ApiService>((_) => ApiService())));
});

// ──────────────────────────────────────────────
// Scan State
// ──────────────────────────────────────────────
enum ScanStatus { idle, loading, success, error }

class ScanState {
  final File? selectedImage;
  final ScanType scanType;
  final ScanResult? result;
  final ScanStatus status;
  final String? error;

  const ScanState({
    this.selectedImage,
    this.scanType = ScanType.xray,
    this.result,
    this.status = ScanStatus.idle,
    this.error,
  });

  ScanState copyWith({
    File? selectedImage,
    ScanType? scanType,
    ScanResult? result,
    ScanStatus? status,
    String? error,
    bool clearImage = false,
    bool clearResult = false,
  }) => ScanState(
    selectedImage: clearImage ? null  : selectedImage ?? this.selectedImage,
    scanType:      scanType   ?? this.scanType,
    result:        clearResult? null  : result        ?? this.result,
    status:        status     ?? this.status,
    error:         error,
  );
}

class ScanNotifier extends StateNotifier<ScanState> {
  final ApiService _api;
  ScanNotifier(this._api) : super(const ScanState());

  void setImage(File file) =>
      state = state.copyWith(selectedImage: file, clearResult: true,
          status: ScanStatus.idle);

  void setScanType(ScanType t) => state = state.copyWith(scanType: t);

  void reset() => state = const ScanState();

  Future<void> analyze() async {
    if (state.selectedImage == null) return;
    state = state.copyWith(status: ScanStatus.loading, error: null);
    try {
      final result = await _api.uploadMedicalImage(
          state.selectedImage!, state.scanType);
      state = state.copyWith(result: result, status: ScanStatus.success);
    } catch (e) {
      state = state.copyWith(status: ScanStatus.error, error: e.toString());
    }
  }
}

final scanProvider = StateNotifierProvider<ScanNotifier, ScanState>((ref) {
  return ScanNotifier(ref.read(Provider<ApiService>((_) => ApiService())));
});
