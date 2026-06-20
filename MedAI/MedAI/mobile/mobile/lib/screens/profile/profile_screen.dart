// lib/screens/profile/profile_screen.dart
import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Profile')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            _ProfileHeader(),
            const SizedBox(height: 24),
            _StatsRow(),
            const SizedBox(height: 24),
            _SettingsSection(),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}

class _ProfileHeader extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          Container(
            width: 64, height: 64,
            decoration: BoxDecoration(
              gradient: AppColors.primaryGradient,
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Icon(Icons.person_rounded,
                color: Colors.white, size: 32),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('John Doe',
                    style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 4),
                Text('john.doe@example.com',
                    style: Theme.of(context).textTheme.bodyMedium),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.accentGreen.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(100),
                  ),
                  child: const Text('Active',
                      style: TextStyle(
                        fontSize: 11, fontWeight: FontWeight.w700,
                        color: AppColors.accentGreen, letterSpacing: 0.5)),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.edit_outlined,
                color: AppColors.textSecondary),
            onPressed: () {},
          ),
        ],
      ),
    );
  }
}

class _StatsRow extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    const stats = [
      ('12', 'Chats'),
      ('5', 'Diagnoses'),
      ('2', 'Scans'),
    ];
    return Row(
      children: stats.asMap().entries.map((e) {
        return Expanded(
          child: Container(
            margin: EdgeInsets.only(right: e.key < 2 ? 10 : 0),
            padding: const EdgeInsets.symmetric(vertical: 16),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.border),
            ),
            child: Column(children: [
              Text(e.value.$1,
                  style: Theme.of(context).textTheme.displayMedium?.copyWith(
                    fontSize: 24,
                  )),
              const SizedBox(height: 2),
              Text(e.value.$2,
                  style: Theme.of(context).textTheme.bodySmall),
            ]),
          ),
        );
      }).toList(),
    );
  }
}

class _SettingsSection extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final items = [
      (Icons.notifications_outlined, 'Notifications', ''),
      (Icons.language_outlined,      'Language',      'English'),
      (Icons.shield_outlined,         'Privacy',       ''),
      (Icons.help_outline_rounded,    'Help & Support',''),
      (Icons.info_outline_rounded,    'About MedAI',   'v1.0.0'),
      (Icons.logout_rounded,          'Sign Out',      ''),
    ];

    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: items.asMap().entries.map((e) {
          final (icon, label, value) = e.value;
          final isLast = e.key == items.length - 1;
          final isSignOut = label == 'Sign Out';
          return Column(
            children: [
              ListTile(
                leading: Icon(icon,
                    size: 20,
                    color: isSignOut
                        ? AppColors.accentDanger : AppColors.textSecondary),
                title: Text(label,
                    style: TextStyle(
                      fontSize: 14, fontWeight: FontWeight.w500,
                      color: isSignOut
                          ? AppColors.accentDanger : AppColors.textPrimary,
                    )),
                trailing: value.isNotEmpty
                    ? Text(value,
                    style: const TextStyle(
                      fontSize: 13, color: AppColors.textHint))
                    : const Icon(Icons.chevron_right_rounded,
                    size: 18, color: AppColors.textHint),
                onTap: () {},
              ),
              if (!isLast)
                const Divider(
                    height: 1, color: AppColors.border,
                    indent: 54),
            ],
          );
        }).toList(),
      ),
    );
  }
}
