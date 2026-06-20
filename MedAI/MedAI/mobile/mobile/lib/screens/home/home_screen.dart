// lib/screens/home/home_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../providers/chat_provider.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: CustomScrollView(
          slivers: [
            // ── Header ──────────────────────────────
            SliverToBoxAdapter(child: _Header()),
            // ── Status banner ────────────────────────
            SliverToBoxAdapter(child: _StatusBanner()),
            // ── Quick actions ────────────────────────
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 0),
              sliver: SliverToBoxAdapter(
                child: Text('What can I help with?',
                    style: Theme.of(context).textTheme.titleMedium),
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              sliver: SliverGrid.count(
                crossAxisCount: 2,
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 1.05,
                children: _quickActions(context),
              ),
            ),
            // ── Disclaimer ──────────────────────────
            SliverToBoxAdapter(child: _Disclaimer()),
            const SliverPadding(padding: EdgeInsets.only(bottom: 32)),
          ],
        ),
      ),
    );
  }

  List<Widget> _quickActions(BuildContext context) => [
    _QuickCard(
      icon: Icons.chat_bubble_outline_rounded,
      label: 'Ask AI Doctor',
      sublabel: 'Describe symptoms, get guidance',
      gradient: AppColors.primaryGradient,
      onTap: () => _navigate(context, 1),
    ),
    _QuickCard(
      icon: Icons.medical_information_outlined,
      label: 'Disease Prediction',
      sublabel: 'Select symptoms, detect conditions',
      gradient: const LinearGradient(
        colors: [Color(0xFF7C3AED), Color(0xFF4F46E5)],
        begin: Alignment.topLeft, end: Alignment.bottomRight,
      ),
      onTap: () => _navigate(context, 2),
    ),
    _QuickCard(
      icon: Icons.document_scanner_outlined,
      label: 'Medical Scan',
      sublabel: 'Analyze X-rays, CT scans & more',
      gradient: const LinearGradient(
        colors: [Color(0xFF0891B2), Color(0xFF00D4C8)],
        begin: Alignment.topLeft, end: Alignment.bottomRight,
      ),
      onTap: () => _navigate(context, 3),
    ),
    _QuickCard(
      icon: Icons.history_rounded,
      label: 'Health History',
      sublabel: 'Past chats and diagnoses',
      gradient: const LinearGradient(
        colors: [Color(0xFF059669), Color(0xFF22C55E)],
        begin: Alignment.topLeft, end: Alignment.bottomRight,
      ),
      onTap: () => _navigate(context, 4),
    ),
  ];

  void _navigate(BuildContext context, int index) {
    final container = ProviderScope.containerOf(context, listen: false);
    container.read(navigationIndexProvider.notifier).state = index;
  }
}

class _Header extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
      child: Row(
        children: [
          // Logo mark
          Container(
            width: 44, height: 44,
            decoration: BoxDecoration(
              gradient: AppColors.primaryGradient,
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Icon(Icons.medical_services_rounded,
                color: Colors.white, size: 22),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('MedAI',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: AppColors.textPrimary,
                    letterSpacing: -0.3,
                  )),
              Text('AI Health Companion',
                  style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
          const Spacer(),
          IconButton(
            icon: const Icon(Icons.notifications_none_rounded,
                color: AppColors.textSecondary),
            onPressed: () {},
          ),
        ],
      ),
    );
  }
}

class _StatusBanner extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF1C2539), Color(0xFF111827)],
            begin: Alignment.topLeft, end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('AI systems online',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 4),
                  Text('Medical LLM · Disease ML · Vision AI',
                      style: Theme.of(context)
                          .textTheme.bodyMedium?.copyWith(fontSize: 12)),
                ],
              ),
            ),
            Column(children: [
              _StatusDot(label: 'LLM',    active: true),
              const SizedBox(height: 4),
              _StatusDot(label: 'ML',     active: true),
              const SizedBox(height: 4),
              _StatusDot(label: 'Vision', active: false),
            ]),
          ],
        ),
      ),
    );
  }
}

class _StatusDot extends StatelessWidget {
  final String label;
  final bool active;
  const _StatusDot({required this.label, required this.active});

  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Text(label,
          style: TextStyle(
            fontSize: 10, color: AppColors.textHint,
            fontWeight: FontWeight.w500,
          )),
      const SizedBox(width: 5),
      Container(
        width: 7, height: 7,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: active ? AppColors.accentGreen : AppColors.textHint,
          boxShadow: active ? [BoxShadow(
            color: AppColors.accentGreen.withOpacity(0.5),
            blurRadius: 6,
          )] : null,
        ),
      ),
    ],
  );
}

class _QuickCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String sublabel;
  final LinearGradient gradient;
  final VoidCallback onTap;

  const _QuickCard({
    required this.icon, required this.label, required this.sublabel,
    required this.gradient, required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 42, height: 42,
              decoration: BoxDecoration(
                gradient: gradient,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: Colors.white, size: 20),
            ),
            const Spacer(),
            Text(label,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontSize: 14,
                )),
            const SizedBox(height: 3),
            Text(sublabel,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  height: 1.3,
                )),
          ],
        ),
      ),
    );
  }
}

class _Disclaimer extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 0),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.accentWarning.withOpacity(0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
              color: AppColors.accentWarning.withOpacity(0.25)),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.info_outline_rounded,
                size: 16, color: AppColors.accentWarning),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                'MedAI provides informational guidance only. Always consult a qualified healthcare provider for medical decisions.',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppColors.accentWarning.withOpacity(0.9),
                  height: 1.5,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
