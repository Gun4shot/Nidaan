// lib/screens/root_scaffold.dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/theme/app_theme.dart';
import '../providers/chat_provider.dart';
import 'home/home_screen.dart';
import 'chat/chat_screen.dart';
import 'diagnosis/diagnosis_screen.dart';
import 'scan/scan_screen.dart';
import 'history/history_screen.dart';

class RootScaffold extends ConsumerWidget {
  const RootScaffold({super.key});

  static const _screens = [
    HomeScreen(),
    ChatScreen(),
    DiagnosisScreen(),
    ScanScreen(),
    HistoryScreen(),
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentIndex = ref.watch(navigationIndexProvider);

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light.copyWith(
        statusBarColor: Colors.transparent,
        systemNavigationBarColor: AppColors.surface,
      ),
      child: Scaffold(
        body: IndexedStack(
          index: currentIndex,
          children: _screens,
        ),
        bottomNavigationBar: _BottomNav(
          currentIndex: currentIndex,
          onTap: (i) => ref.read(navigationIndexProvider.notifier).state = i,
        ),
      ),
    );
  }
}

class _BottomNav extends StatelessWidget {
  final int currentIndex;
  final void Function(int) onTap;

  const _BottomNav({required this.currentIndex, required this.onTap});

  static const _items = [
    (Icons.home_rounded,                  Icons.home_outlined,               'Home'),
    (Icons.chat_bubble_rounded,           Icons.chat_bubble_outline_rounded,  'Chat'),
    (Icons.medical_information_rounded,   Icons.medical_information_outlined, 'Predict'),
    (Icons.document_scanner_rounded,      Icons.document_scanner_outlined,    'Scan'),
    (Icons.history_rounded,               Icons.history_outlined,             'History'),
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).padding.bottom,
      ),
      child: Row(
        children: _items.asMap().entries.map((e) {
          final idx = e.key;
          final (activeIcon, inactiveIcon, label) = e.value;
          final isActive = idx == currentIndex;
          return Expanded(
            child: GestureDetector(
              onTap: () => onTap(idx),
              behavior: HitTestBehavior.opaque,
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 10),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    AnimatedSwitcher(
                      duration: const Duration(milliseconds: 200),
                      child: Icon(
                        isActive ? activeIcon : inactiveIcon,
                        key: ValueKey(isActive),
                        size: 24,
                        color: isActive
                            ? AppColors.accent : AppColors.textHint,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(label,
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: isActive
                              ? FontWeight.w600 : FontWeight.w400,
                          color: isActive
                              ? AppColors.accent : AppColors.textHint,
                        )),
                  ],
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}
