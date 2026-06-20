// lib/widgets/shared_widgets.dart
import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';

// ──────────────────────────────────────────────
// Gradient primary button
// ──────────────────────────────────────────────
class GradientButton extends StatelessWidget {
  final String label;
  final VoidCallback? onTap;
  final IconData? icon;
  final bool isLoading;
  final double? width;

  const GradientButton({
    super.key,
    required this.label,
    this.onTap,
    this.icon,
    this.isLoading = false,
    this.width,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: isLoading ? null : onTap,
      child: Container(
        width: width ?? double.infinity,
        height: 52,
        decoration: BoxDecoration(
          gradient: onTap == null
              ? null
              : AppColors.primaryGradient,
          color: onTap == null ? AppColors.border : null,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Center(
          child: isLoading
              ? const SizedBox(
                  width: 20, height: 20,
                  child: CircularProgressIndicator(
                      strokeWidth: 2, color: Colors.white),
                )
              : Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (icon != null) ...[
                      Icon(icon, size: 18, color: Colors.white),
                      const SizedBox(width: 8),
                    ],
                    Text(label,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                        )),
                  ],
                ),
        ),
      ),
    );
  }
}

// ──────────────────────────────────────────────
// Section header
// ──────────────────────────────────────────────
class SectionHeader extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget? trailing;

  const SectionHeader({
    super.key, required this.title, this.subtitle, this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: Theme.of(context).textTheme.titleMedium),
              if (subtitle != null)
                Padding(
                  padding: const EdgeInsets.only(top: 2),
                  child: Text(subtitle!,
                      style: Theme.of(context).textTheme.bodyMedium),
                ),
            ],
          ),
        ),
        if (trailing != null) trailing!,
      ],
    );
  }
}

// ──────────────────────────────────────────────
// Confidence bar
// ──────────────────────────────────────────────
class ConfidenceBar extends StatelessWidget {
  final double value; // 0.0–1.0
  final Color? color;
  final String? label;

  const ConfidenceBar({super.key, required this.value, this.color, this.label});

  @override
  Widget build(BuildContext context) {
    final c = color ?? _colorFor(value);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (label != null) ...[
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label!, style: Theme.of(context).textTheme.bodySmall),
              Text('${(value * 100).round()}%',
                  style: TextStyle(
                    fontSize: 12, fontWeight: FontWeight.w600, color: c)),
            ],
          ),
          const SizedBox(height: 4),
        ],
        ClipRRect(
          borderRadius: BorderRadius.circular(100),
          child: LinearProgressIndicator(
            value: value,
            minHeight: 6,
            backgroundColor: AppColors.border,
            valueColor: AlwaysStoppedAnimation<Color>(c),
          ),
        ),
      ],
    );
  }

  Color _colorFor(double v) {
    if (v >= 0.75) return AppColors.accentGreen;
    if (v >= 0.50) return AppColors.accentWarning;
    return AppColors.accentDanger;
  }
}

// ──────────────────────────────────────────────
// Severity badge
// ──────────────────────────────────────────────
class SeverityBadge extends StatelessWidget {
  final String severity;
  const SeverityBadge({super.key, required this.severity});

  @override
  Widget build(BuildContext context) {
    final (color, bg) = _colors(severity);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
          color: bg, borderRadius: BorderRadius.circular(100)),
      child: Text(severity.toUpperCase(),
          style: TextStyle(
            fontSize: 10, fontWeight: FontWeight.w700, color: color,
            letterSpacing: 0.8,
          )),
    );
  }

  (Color, Color) _colors(String s) {
    switch (s.toLowerCase()) {
      case 'mild':   return (AppColors.accentGreen, AppColors.accentGreen.withOpacity(0.15));
      case 'severe': return (AppColors.accentDanger, AppColors.accentDanger.withOpacity(0.15));
      default:       return (AppColors.accentWarning, AppColors.accentWarning.withOpacity(0.15));
    }
  }
}

// ──────────────────────────────────────────────
// Error/empty state card
// ──────────────────────────────────────────────
class StateCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final String? buttonLabel;
  final VoidCallback? onButton;

  const StateCard({
    super.key, required this.icon, required this.title,
    required this.subtitle, this.buttonLabel, this.onButton,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 72, height: 72,
              decoration: BoxDecoration(
                color: AppColors.surfaceElevated,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppColors.border),
              ),
              child: Icon(icon, size: 32, color: AppColors.textHint),
            ),
            const SizedBox(height: 16),
            Text(title, style: Theme.of(context).textTheme.titleMedium,
                textAlign: TextAlign.center),
            const SizedBox(height: 6),
            Text(subtitle, style: Theme.of(context).textTheme.bodyMedium,
                textAlign: TextAlign.center),
            if (buttonLabel != null && onButton != null) ...[
              const SizedBox(height: 20),
              GradientButton(
                label: buttonLabel!, onTap: onButton,
                width: 180,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
