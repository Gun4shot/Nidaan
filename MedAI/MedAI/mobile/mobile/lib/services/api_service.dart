// lib/services/api_service.dart
import 'dart:convert';
import 'dart:io';
import 'package:dio/dio.dart';
import '../core/constants/app_constants.dart';
import '../models/disease_model.dart';
import '../models/scan_model.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  late final Dio _dio = Dio(
    BaseOptions(
      baseUrl: AppConstants.baseUrl,
      connectTimeout: const Duration(milliseconds: AppConstants.connectTimeout),
      receiveTimeout: const Duration(milliseconds: AppConstants.receiveTimeout),
      headers: {'Content-Type': 'application/json'},
    ),
  )..interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          // Attach auth token if present
          // final token = SharedPrefs.token;
          // if (token != null) options.headers['Authorization'] = 'Bearer $token';
          handler.next(options);
        },
        onError: (error, handler) {
          handler.next(error);
        },
      ),
    );

  // ──────────────────────────────────────────────
  // Chat (non-streaming fallback)
  // ──────────────────────────────────────────────
  Future<String> sendMessage(String message) async {
    try {
      final res = await _dio.post(
        AppConstants.chatEndpoint,
        data: {'message': message},
      );
      return res.data['response'] as String;
    } on DioException catch (e) {
      throw _parseError(e);
    }
  }

  // ──────────────────────────────────────────────
  // SSE Chat Streaming (Merged & Optimized)
  // ──────────────────────────────────────────────
  Stream<String> streamChat(String message) async* {
    try {
      final response = await _dio.post<ResponseBody>(
        AppConstants.chatStreamEndpoint,
        data: {'message': message},
        options: Options(responseType: ResponseType.stream),
      );

      if (response.data != null) {
        // LineSplitter safely catches line breaks even across chunk boundaries
        final lineStream = response.data!.stream
            .cast<List<int>>()
            .transform(utf8.decoder)
            .transform(const LineSplitter());

        await for (final line in lineStream) {
          if (!line.startsWith('data:')) continue;

          final data = line.substring(5).trim();
          if (data.isEmpty) continue;

          yield data;
        }
      }
    } on DioException catch (e) {
      throw _parseError(e);
    }
  }

  // ──────────────────────────────────────────────
  // Disease Prediction
  // ──────────────────────────────────────────────
  Future<List<DiseaseResult>> predictDisease(List<String> symptoms) async {
    try {
      final res = await _dio.post(
        AppConstants.predictEndpoint,
        data: {'symptoms': symptoms},
      );
      final List raw = res.data['results'] ?? [];
      return raw.map((e) => DiseaseResult.fromJson(e)).toList();
    } on DioException catch (e) {
      throw _parseError(e);
    }
  }

  // ──────────────────────────────────────────────
  // Medical Scan Upload
  // ──────────────────────────────────────────────
  Future<ScanResult> uploadMedicalImage(File image, ScanType type) async {
    try {
      final fileName = image.path.split('/').last;
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(image.path, filename: fileName),
        'scan_type': type.name,
      });
      final res = await _dio.post(
        AppConstants.scanEndpoint,
        data: formData,
        options: Options(contentType: 'multipart/form-data'),
      );
      return ScanResult.fromJson(res.data);
    } on DioException catch (e) {
      throw _parseError(e);
    }
  }

  // ──────────────────────────────────────────────
  // Health check
  // ──────────────────────────────────────────────
  Future<bool> checkHealth() async {
    try {
      final res = await _dio.get(AppConstants.healthEndpoint);
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  String _parseError(DioException e) {
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.connectionError) {
      return 'Cannot reach server. Check your connection.';
    }
    if (e.response?.statusCode == 503) {
      return 'AI model is loading. Please try again in a moment.';
    }
    return e.response?.data?['detail'] ?? 'Something went wrong.';
  }
}