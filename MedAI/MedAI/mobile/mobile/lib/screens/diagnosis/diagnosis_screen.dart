// lib/screens/diagnosis/diagnosis_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../models/disease_model.dart';
import '../../providers/diagnosis_provider.dart';
import '../../widgets/shared_widgets.dart';

class DiagnosisScreen extends ConsumerWidget {
  const DiagnosisScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(diagnosisProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Disease Prediction'),
        actions: [
          if (state.selected.isNotEmpty)
            TextButton(
              onPressed: () => ref.read(diagnosisProvider.notifier).clearAll(),
              child: const Text('Clear',
                  style: TextStyle(color: AppColors.textSecondary)),
            ),
        ],
      ),
      body: CustomScrollView(
        slivers: [
          // ── Intro ──────────────────────────────
          SliverToBoxAdapter(child: _ScreenHeader(selected: state.selected.length)),

          // ── Symptom groups ─────────────────────
          ..._buildSymptomSections(context, ref, state),

          // ── Predict button ─────────────────────
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
            sliver: SliverToBoxAdapter(
              child: GradientButton(
                label: 'Predict Conditions',
                icon: Icons.biotech_rounded,
                isLoading: state.status == DiagStatus.loading,
                onTap: state.selected.isEmpty
                    ? null
                    : () => ref.read(diagnosisProvider.notifier).predict(),
              ),
            ),
          ),

          // ── Results ────────────────────────────
          if (state.status == DiagStatus.success && state.results.isNotEmpty)
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 0),
              sliver: SliverToBoxAdapter(
                child: _ResultsSection(results: state.results),
              ),
            ),

          if (state.status == DiagStatus.error)
            SliverToBoxAdapter(
              child: StateCard(
                icon: Icons.error_outline_rounded,
                title: 'Prediction failed',
                subtitle: state.error ?? 'Unable to reach the AI server.',
                buttonLabel: 'Retry',
                onButton: () => ref.read(diagnosisProvider.notifier).predict(),
              ),
            ),

          const SliverPadding(padding: EdgeInsets.only(bottom: 40)),
        ],
      ),
    );
  }

  List<Widget> _buildSymptomSections(
      BuildContext context, WidgetRef ref, DiagnosisState state) {
    final categories = <String, List<Symptom>>{};
    for (final s in state.symptoms) {
      categories.putIfAbsent(s.category ?? 'Other', () => []).add(s);
    }

    return categories.entries.map((entry) {
      return SliverPadding(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
        sliver: SliverToBoxAdapter(
          child: _SymptomGroup(
            category: entry.key,
            symptoms: entry.value,
            onToggle: (id) =>
                ref.read(diagnosisProvider.notifier).toggleSymptom(id),
          ),
        ),
      );
    }).toList();
  }
}

class _ScreenHeader extends StatelessWidget {
  final int selected;
  const _ScreenHeader({required this.selected});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF1C1040), Color(0xFF111827)],
            begin: Alignment.topLeft, end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(
          children: [
            Container(
              width: 44, height: 44,
              decoration: BoxDecoration(
                color: const Color(0xFF7C3AED).withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.medical_information_outlined,
                  color: Color(0xFF7C3AED), size: 22),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Select your symptoms',
                      style: Theme.of(context).textTheme.titleMedium),
                  Text(
                    selected == 0
                        ? 'Choose all symptoms you\'re experiencing'
                        : '$selected symptom${selected > 1 ? 's' : ''} selected',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: selected > 0
                          ? AppColors.accent : AppColors.textHint,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SymptomGroup extends StatelessWidget {
  final String category;
  final List<Symptom> symptoms;
  final void Function(String id) onToggle;

  const _SymptomGroup({
    required this.category, required this.symptoms, required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: Text(category,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.5,
              )),
        ),
        Wrap(
          spacing: 8, runSpacing: 8,
          children: symptoms.map((s) => _SymptomChip(
            symptom: s, onTap: () => onToggle(s.id),
          )).toList(),
        ),
      ],
    );
  }
}

class _SymptomChip extends StatelessWidget {
  final Symptom symptom;
  final VoidCallback onTap;
  const _SymptomChip({required this.symptom, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
        decoration: BoxDecoration(
          gradient: symptom.isSelected ? AppColors.primaryGradient : null,
          color: symptom.isSelected ? null : AppColors.surfaceElevated,
          borderRadius: BorderRadius.circular(100),
          border: Border.all(
            color: symptom.isSelected
                ? Colors.transparent : AppColors.border,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (symptom.isSelected) ...[
              const Icon(Icons.check_circle_rounded,
                  size: 14, color: Colors.white),
              const SizedBox(width: 5),
            ],
            Text(symptom.name,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: symptom.isSelected
                      ? FontWeight.w600 : FontWeight.w400,
                  color: symptom.isSelected
                      ? Colors.white : AppColors.textPrimary,
                )),
          ],
        ),
      ),
    );
  }
}

// ──────────────────────────────────────────────
// Results
// ──────────────────────────────────────────────
class _ResultsSection extends StatelessWidget {
  final List<DiseaseResult> results;
  const _ResultsSection({required this.results});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SectionHeader(
          title: 'Possible Conditions',
          subtitle: 'Ranked by likelihood — consult a doctor for confirmation',
        ),
        const SizedBox(height: 14),
        ...results.asMap().entries.map((e) => Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: _DiseaseCard(result: e.value, rank: e.key + 1),
        )),
        // Disclaimer
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.accentWarning.withOpacity(0.08),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
                color: AppColors.accentWarning.withOpacity(0.2)),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.warning_amber_rounded,
                  size: 16, color: AppColors.accentWarning),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'These predictions are based on reported symptoms only. '
                  'A healthcare professional must confirm any diagnosis.',
                  style: TextStyle(
                    fontSize: 12, height: 1.5,
                    color: AppColors.accentWarning.withOpacity(0.9),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _DiseaseCard extends StatelessWidget {
  final DiseaseResult result;
  final int rank;
  const _DiseaseCard({required this.result, required this.rank});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: rank == 1 ? AppColors.primary.withOpacity(0.4) : AppColors.border,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 28, height: 28,
                decoration: BoxDecoration(
                  gradient: rank == 1 ? AppColors.primaryGradient : null,
                  color: rank == 1 ? null : AppColors.surfaceElevated,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Center(
                  child: Text('$rank',
                      style: TextStyle(
                        fontSize: 13, fontWeight: FontWeight.w700,
                        color: rank == 1 ? Colors.white : AppColors.textSecondary,
                      )),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(result.name,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontSize: 15,
                    )),
              ),
              SeverityBadge(severity: result.severity),
            ],
          ),
          const SizedBox(height: 14),
          ConfidenceBar(
            value: result.confidence,
            label: 'Confidence',
          ),
          if (result.description != null) ...[
            const SizedBox(height: 10),
            Text(result.description!,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontSize: 13, height: 1.5,
                )),
          ],
          if (result.recommendations.isNotEmpty) ...[
            const SizedBox(height: 12),
            const Divider(color: AppColors.border, height: 1),
            const SizedBox(height: 12),
            Text('Recommendations',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppColors.textSecondary,
                  fontWeight: FontWeight.w600,
                )),
            const SizedBox(height: 6),
            ...result.recommendations.map((r) => Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Padding(
                    padding: EdgeInsets.only(top: 5),
                    child: CircleAvatar(
                      radius: 3,
                      backgroundColor: AppColors.accent,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(child: Text(r,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontSize: 13,
                      ))),
                ],
              ),
            )),
          ],
        ],
      ),
    );
  }
}
