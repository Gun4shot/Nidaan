// lib/screens/chat/chat_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../models/chat_model.dart';
import '../../providers/chat_provider.dart';
import '../../widgets/chat_bubble.dart';
import '../../widgets/shared_widgets.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});
  @override ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _inputCtrl    = TextEditingController();
  final _scrollCtrl   = ScrollController();
  final _focusNode    = FocusNode();
  bool _hasText       = false;

  @override
  void initState() {
    super.initState();
    _inputCtrl.addListener(() {
      setState(() => _hasText = _inputCtrl.text.trim().isNotEmpty);
    });
  }

  @override
  void dispose() {
    _inputCtrl.dispose();
    _scrollCtrl.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _send() {
    final text = _inputCtrl.text.trim();
    if (text.isEmpty) return;
    _inputCtrl.clear();
    ref.read(chatProvider.notifier).sendMessage(text);
    Future.delayed(const Duration(milliseconds: 100), _scrollToBottom);
  }

  void _scrollToBottom() {
    if (_scrollCtrl.hasClients) {
      _scrollCtrl.animateTo(
        _scrollCtrl.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(chatProvider);

    // Auto-scroll when new message arrives
    ref.listen(chatProvider, (_, next) {
      Future.delayed(const Duration(milliseconds: 80), _scrollToBottom);
    });

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: _buildAppBar(state),
      body: Column(
        children: [
          Expanded(
            child: state.messages.isEmpty
                ? _EmptyChat()
                : _MessageList(messages: state.messages, scrollCtrl: _scrollCtrl),
          ),
          // Error bar
          if (state.status == ChatRequestStatus.error && state.error != null)
            _ErrorBar(error: state.error!),
          // Input bar
          _InputBar(
            controller: _inputCtrl,
            focusNode: _focusNode,
            hasText: _hasText,
            isStreaming: state.status == ChatRequestStatus.streaming,
            onSend: _send,
          ),
        ],
      ),
    );
  }

  PreferredSizeWidget _buildAppBar(ChatState state) {
    return AppBar(
      backgroundColor: AppColors.background,
      title: Row(
        children: [
          Container(
            width: 36, height: 36,
            decoration: BoxDecoration(
              gradient: AppColors.primaryGradient,
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.medical_services_rounded,
                color: Colors.white, size: 18),
          ),
          const SizedBox(width: 10),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('AI Doctor',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              Text(
                state.status == ChatRequestStatus.streaming
                    ? 'Typing...' : 'Online',
                style: TextStyle(
                  fontSize: 11,
                  color: state.status == ChatRequestStatus.streaming
                      ? AppColors.accent : AppColors.accentGreen,
                ),
              ),
            ],
          ),
        ],
      ),
      actions: [
        if (state.messages.isNotEmpty)
          IconButton(
            icon: const Icon(Icons.delete_outline_rounded,
                color: AppColors.textSecondary),
            onPressed: () => _confirmClear(context),
            tooltip: 'Clear chat',
          ),
        const SizedBox(width: 4),
      ],
      bottom: PreferredSize(
        preferredSize: const Size.fromHeight(1),
        child: Container(height: 1, color: AppColors.border),
      ),
    );
  }

  void _confirmClear(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Clear conversation?'),
        content: const Text('This chat will be deleted.',
            style: TextStyle(color: AppColors.textSecondary)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel',
                style: TextStyle(color: AppColors.textSecondary)),
          ),
          TextButton(
            onPressed: () {
              ref.read(chatProvider.notifier).clearChat();
              Navigator.pop(context);
            },
            child: const Text('Clear',
                style: TextStyle(color: AppColors.accentDanger)),
          ),
        ],
      ),
    );
  }
}

// ──────────────────────────────────────────────
// Message list
// ──────────────────────────────────────────────
class _MessageList extends StatelessWidget {
  final List<ChatMessage> messages;
  final ScrollController scrollCtrl;
  const _MessageList({required this.messages, required this.scrollCtrl});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      controller: scrollCtrl,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      itemCount: messages.length,
      itemBuilder: (_, i) => ChatBubble(message: messages[i]),
    );
  }
}

// ──────────────────────────────────────────────
// Empty state
// ──────────────────────────────────────────────
class _EmptyChat extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 80, height: 80,
              decoration: BoxDecoration(
                gradient: AppColors.primaryGradient,
                borderRadius: BorderRadius.circular(24),
              ),
              child: const Icon(Icons.medical_services_rounded,
                  color: Colors.white, size: 36),
            ),
            const SizedBox(height: 20),
            Text('AI Doctor',
                style: Theme.of(context).textTheme.displayMedium),
            const SizedBox(height: 8),
            Text(
              'Describe your symptoms or ask any health question. I\'ll provide guidance based on medical knowledge.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.6),
            ),
            const SizedBox(height: 32),
            ..._suggestions(context),
          ],
        ),
      ),
    );
  }

  List<Widget> _suggestions(BuildContext context) {
    final prompts = [
      'I have a headache and mild fever',
      'What are symptoms of diabetes?',
      'I\'ve had chest tightness for 2 days',
    ];
    return prompts.map((p) => Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: GestureDetector(
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: AppColors.surfaceElevated,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.border),
          ),
          child: Row(
            children: [
              const Icon(Icons.chat_bubble_outline_rounded,
                  size: 16, color: AppColors.accent),
              const SizedBox(width: 10),
              Expanded(child: Text(p,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textPrimary, fontSize: 13,
                  ))),
            ],
          ),
        ),
      ),
    )).toList();
  }
}

// ──────────────────────────────────────────────
// Input bar
// ──────────────────────────────────────────────
class _InputBar extends StatelessWidget {
  final TextEditingController controller;
  final FocusNode focusNode;
  final bool hasText;
  final bool isStreaming;
  final VoidCallback onSend;

  const _InputBar({
    required this.controller, required this.focusNode,
    required this.hasText, required this.isStreaming, required this.onSend,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(
        16, 12, 16, MediaQuery.of(context).padding.bottom + 12),
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: AppColors.surfaceElevated,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppColors.border),
              ),
              child: TextField(
                controller: controller,
                focusNode: focusNode,
                maxLines: 4, minLines: 1,
                style: const TextStyle(
                    color: AppColors.textPrimary, fontSize: 15),
                decoration: const InputDecoration(
                  hintText: 'Describe your symptoms...',
                  border: InputBorder.none,
                  contentPadding:
                      EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                ),
                onSubmitted: (_) => onSend(),
                textInputAction: TextInputAction.send,
              ),
            ),
          ),
          const SizedBox(width: 10),
          AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            child: GestureDetector(
              onTap: isStreaming ? null : (hasText ? onSend : null),
              child: Container(
                width: 46, height: 46,
                decoration: BoxDecoration(
                  gradient: (hasText && !isStreaming)
                      ? AppColors.primaryGradient : null,
                  color: (hasText && !isStreaming) ? null : AppColors.surfaceElevated,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppColors.border),
                ),
                child: isStreaming
                    ? const Padding(
                        padding: EdgeInsets.all(13),
                        child: CircularProgressIndicator(
                          strokeWidth: 2, color: AppColors.accent),
                      )
                    : Icon(
                        Icons.send_rounded,
                        size: 20,
                        color: hasText ? Colors.white : AppColors.textHint,
                      ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorBar extends StatelessWidget {
  final String error;
  const _ErrorBar({required this.error});

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.fromLTRB(16, 0, 16, 8),
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
    decoration: BoxDecoration(
      color: AppColors.accentDanger.withOpacity(0.12),
      borderRadius: BorderRadius.circular(10),
      border: Border.all(color: AppColors.accentDanger.withOpacity(0.3)),
    ),
    child: Row(
      children: [
        const Icon(Icons.error_outline_rounded,
            size: 16, color: AppColors.accentDanger),
        const SizedBox(width: 8),
        Expanded(child: Text(error,
            style: const TextStyle(
              fontSize: 13, color: AppColors.accentDanger))),
      ],
    ),
  );
}
