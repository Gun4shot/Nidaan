// lib/screens/history/history_screen.dart
import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../../widgets/shared_widgets.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // TODO: wire to backend GET /history
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Health History')),
      body: DefaultTabController(
        length: 2,
        child: Column(
          children: [
            Container(
              color: AppColors.surface,
              child: TabBar(
                labelColor: AppColors.accent,
                unselectedLabelColor: AppColors.textSecondary,
                indicatorColor: AppColors.accent,
                indicatorSize: TabBarIndicatorSize.label,
                tabs: const [
                  Tab(text: 'Chats'),
                  Tab(text: 'Diagnoses'),
                ],
              ),
            ),
            const Expanded(
              child: TabBarView(
                children: [
                  _ChatHistoryTab(),
                  _DiagnosisHistoryTab(),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ChatHistoryTab extends StatelessWidget {
  const _ChatHistoryTab();

  @override
  Widget build(BuildContext context) {
    // Placeholder entries — replace with real data from SharedPreferences/DB
    final sessions = [
      _HistoryEntry(
        title: 'Chest pain & shortness of breath',
        subtitle: 'Chat with AI Doctor',
        time: '2 hours ago',
        icon: Icons.chat_bubble_outline_rounded,
        iconColor: AppColors.primary,
      ),
      _HistoryEntry(
        title: 'Recurring headache questions',
        subtitle: 'Chat with AI Doctor',
        time: 'Yesterday',
        icon: Icons.chat_bubble_outline_rounded,
        iconColor: AppColors.primary,
      ),
      _HistoryEntry(
        title: 'Fever and body aches',
        subtitle: 'Chat with AI Doctor',
        time: '3 days ago',
        icon: Icons.chat_bubble_outline_rounded,
        iconColor: AppColors.primary,
      ),
    ];

    if (sessions.isEmpty) {
      return const StateCard(
        icon: Icons.chat_bubble_outline_rounded,
        title: 'No chat history yet',
        subtitle: 'Your AI Doctor conversations will appear here',
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(20),
      itemCount: sessions.length,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (_, i) => _HistoryCard(entry: sessions[i]),
    );
  }
}

class _DiagnosisHistoryTab extends StatelessWidget {
  const _DiagnosisHistoryTab();

  @override
  Widget build(BuildContext context) {
    final reports = [
      _HistoryEntry(
        title: 'Flu — 87% confidence',
        subtitle: 'Fever, cough, body aches',
        time: '1 day ago',
        icon: Icons.medical_information_outlined,
        iconColor: const Color(0xFF7C3AED),
      ),
      _HistoryEntry(
        title: 'Possible Pneumonia — 91%',
        subtitle: 'Chest X-Ray analysis',
        time: '5 days ago',
        icon: Icons.document_scanner_outlined,
        iconColor: AppColors.accent,
      ),
    ];

    if (reports.isEmpty) {
      return const StateCard(
        icon: Icons.medical_information_outlined,
        title: 'No diagnoses yet',
        subtitle: 'Your disease predictions and scan results will appear here',
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(20),
      itemCount: reports.length,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (_, i) => _HistoryCard(entry: reports[i]),
    );
  }
}

class _HistoryEntry {
  final String title, subtitle, time;
  final IconData icon;
  final Color iconColor;

  const _HistoryEntry({
    required this.title, required this.subtitle,
    required this.time, required this.icon, required this.iconColor,
  });
}

class _HistoryCard extends StatelessWidget {
  final _HistoryEntry entry;
  const _HistoryCard({required this.entry});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          Container(
            width: 42, height: 42,
            decoration: BoxDecoration(
              color: entry.iconColor.withOpacity(0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(entry.icon, color: entry.iconColor, size: 20),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(entry.title,
                    maxLines: 1, overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontSize: 14)),
                const SizedBox(height: 2),
                Text(entry.subtitle,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppColors.textSecondary)),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Text(entry.time,
              style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(width: 4),
          const Icon(Icons.chevron_right_rounded,
              size: 18, color: AppColors.textHint),
        ],
      ),
    );
  }
}
