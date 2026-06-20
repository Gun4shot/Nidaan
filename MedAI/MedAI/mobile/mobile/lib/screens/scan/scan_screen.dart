// lib/screens/scan/scan_screen.dart
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import '../../core/theme/app_theme.dart';
import '../../models/scan_model.dart';
import '../../providers/diagnosis_provider.dart';
import '../../widgets/shared_widgets.dart';

class ScanScreen extends ConsumerWidget {
  const ScanScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(scanProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Medical Scan')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _ScanTypeSelector(
              selected: state.scanType,
              onSelect: (t) => ref.read(scanProvider.notifier).setScanType(t),
            ),
            const SizedBox(height: 20),
            _ImageUploadZone(
              image: state.selectedImage,
              onPickImage: (file) =>
                  ref.read(scanProvider.notifier).setImage(file),
            ),
            const SizedBox(height: 20),
            if (state.selectedImage != null && state.status != ScanStatus.success)
              GradientButton(
                label: 'Analyze Scan',
                icon: Icons.biotech_rounded,
                isLoading: state.status == ScanStatus.loading,
                onTap: () => ref.read(scanProvider.notifier).analyze(),
              ),
            if (state.status == ScanStatus.loading) ...[
              const SizedBox(height: 24),
              _AnalyzingIndicator(),
            ],
            if (state.status == ScanStatus.success && state.result != null) ...[
              const SizedBox(height: 24),
              _ScanResultCard(result: state.result!),
            ],
            if (state.status == ScanStatus.error) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppColors.accentDanger.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                      color: AppColors.accentDanger.withOpacity(0.3)),
                ),
                child: Row(children: [
                  const Icon(Icons.error_outline_rounded,
                      color: AppColors.accentDanger, size: 18),
                  const SizedBox(width: 10),
                  Expanded(child: Text(
                    state.error ?? 'Analysis failed. Please try again.',
                    style: const TextStyle(
                      color: AppColors.accentDanger, fontSize: 13),
                  )),
                ]),
              ),
            ],
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}

// ──────────────────────────────────────────────
// Scan type pill selector
// ──────────────────────────────────────────────
class _ScanTypeSelector extends StatelessWidget {
  final ScanType selected;
  final void Function(ScanType) onSelect;
  const _ScanTypeSelector({required this.selected, required this.onSelect});

  static const _types = [
    (ScanType.xray, 'X-Ray',    Icons.radio_button_checked_rounded),
    (ScanType.skin, 'Skin',     Icons.face_retouching_natural_rounded),
    (ScanType.ct,   'CT Scan',  Icons.layers_rounded),
    (ScanType.mri,  'MRI',      Icons.blur_circular_rounded),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Scan type',
            style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 12),
        Row(
          children: _types.map((t) {
            final isActive = t.$1 == selected;
            return Expanded(
              child: GestureDetector(
                onTap: () => onSelect(t.$1),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  margin: EdgeInsets.only(
                    right: t.$1 != ScanType.mri ? 8 : 0),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  decoration: BoxDecoration(
                    gradient: isActive ? AppColors.primaryGradient : null,
                    color: isActive ? null : AppColors.surfaceElevated,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: isActive
                          ? Colors.transparent : AppColors.border,
                    ),
                  ),
                  child: Column(
                    children: [
                      Icon(t.$3, size: 20,
                          color: isActive
                              ? Colors.white : AppColors.textSecondary),
                      const SizedBox(height: 4),
                      Text(t.$2,
                          style: TextStyle(
                            fontSize: 11, fontWeight: FontWeight.w600,
                            color: isActive
                                ? Colors.white : AppColors.textSecondary,
                          )),
                    ],
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }
}

// ──────────────────────────────────────────────
// Upload drop zone
// ──────────────────────────────────────────────
class _ImageUploadZone extends StatelessWidget {
  final File? image;
  final void Function(File) onPickImage;
  const _ImageUploadZone({this.image, required this.onPickImage});

  Future<void> _pick(BuildContext context) async {
    final picker = ImagePicker();
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Container(width: 40, height: 4,
              decoration: BoxDecoration(
                color: AppColors.border,
                borderRadius: BorderRadius.circular(100))),
          const SizedBox(height: 20),
          ListTile(
            leading: Container(
              width: 40, height: 40,
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.photo_library_outlined,
                  color: AppColors.primary),
            ),
            title: const Text('Choose from gallery'),
            onTap: () => Navigator.pop(context, ImageSource.gallery),
          ),
          ListTile(
            leading: Container(
              width: 40, height: 40,
              decoration: BoxDecoration(
                color: AppColors.accent.withOpacity(0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.camera_alt_outlined,
                  color: AppColors.accent),
            ),
            title: const Text('Take a photo'),
            onTap: () => Navigator.pop(context, ImageSource.camera),
          ),
          const SizedBox(height: 8),
        ]),
      ),
    );
    if (source == null) return;
    final picked = await picker.pickImage(source: source, imageQuality: 85);
    if (picked != null) onPickImage(File(picked.path));
  }

  @override
  Widget build(BuildContext context) {
    if (image != null) {
      return Stack(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: Image.file(image!,
                width: double.infinity, height: 240,
                fit: BoxFit.cover),
          ),
          Positioned(
            top: 8, right: 8,
            child: GestureDetector(
              onTap: () => _pick(context),
              child: Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.background.withOpacity(0.85),
                  borderRadius: BorderRadius.circular(100),
                  border: Border.all(color: AppColors.border),
                ),
                child: const Row(children: [
                  Icon(Icons.swap_horiz_rounded,
                      size: 14, color: AppColors.textPrimary),
                  SizedBox(width: 4),
                  Text('Change', style: TextStyle(
                    fontSize: 12, color: AppColors.textPrimary,
                    fontWeight: FontWeight.w500,
                  )),
                ]),
              ),
            ),
          ),
        ],
      );
    }

    return GestureDetector(
      onTap: () => _pick(context),
      child: Container(
        height: 200,
        decoration: BoxDecoration(
          color: AppColors.surfaceElevated,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: AppColors.border, style: BorderStyle.solid, width: 1.5),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 56, height: 56,
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.12),
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(Icons.upload_file_rounded,
                  color: AppColors.primary, size: 28),
            ),
            const SizedBox(height: 14),
            const Text('Upload medical scan',
                style: TextStyle(
                  fontSize: 15, fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary)),
            const SizedBox(height: 4),
            const Text('Tap to choose from gallery or camera',
                style: TextStyle(
                  fontSize: 13, color: AppColors.textSecondary)),
          ],
        ),
      ),
    );
  }
}

// ──────────────────────────────────────────────
// Processing animation
// ──────────────────────────────────────────────
class _AnalyzingIndicator extends StatelessWidget {
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(20),
    decoration: BoxDecoration(
      color: AppColors.surfaceElevated,
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: AppColors.border),
    ),
    child: Row(children: [
      SizedBox(
        width: 36, height: 36,
        child: CircularProgressIndicator(
          strokeWidth: 3,
          valueColor: AlwaysStoppedAnimation<Color>(AppColors.accent),
        ),
      ),
      const SizedBox(width: 16),
      Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Analyzing scan...',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(fontSize: 15)),
        const SizedBox(height: 2),
        Text('AI Vision model is processing your image',
            style: Theme.of(context).textTheme.bodySmall),
      ]),
    ]),
  );
}

// ──────────────────────────────────────────────
// Result card
// ──────────────────────────────────────────────
class _ScanResultCard extends StatelessWidget {
  final ScanResult result;
  const _ScanResultCard({required this.result});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Container(
              width: 42, height: 42,
              decoration: BoxDecoration(
                gradient: AppColors.primaryGradient,
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.biotech_rounded,
                  color: Colors.white, size: 20),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Analysis Complete',
                      style: Theme.of(context).textTheme.titleMedium),
                  Text(result.typeLabel,
                      style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
            ),
            SeverityBadge(severity: result.severity),
          ]),
          const SizedBox(height: 20),
          const Divider(color: AppColors.border, height: 1),
          const SizedBox(height: 20),
          Text('Finding',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w600,
              )),
          const SizedBox(height: 6),
          Text(result.finding,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontSize: 18, height: 1.3,
              )),
          const SizedBox(height: 20),
          ConfidenceBar(
            value: result.confidence,
            label: 'Confidence Score',
          ),
          if (result.recommendations.isNotEmpty) ...[
            const SizedBox(height: 20),
            const Divider(color: AppColors.border, height: 1),
            const SizedBox(height: 16),
            Text('Recommendations',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: AppColors.textSecondary,
                )),
            const SizedBox(height: 10),
            ...result.recommendations.map((r) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Icon(Icons.arrow_right_rounded,
                    color: AppColors.accent, size: 20),
                const SizedBox(width: 6),
                Expanded(child: Text(r,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      fontSize: 13, height: 1.4))),
              ]),
            )),
          ],
        ],
      ),
    );
  }
}
