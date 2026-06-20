// lib/providers/chat_provider.dart
import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../models/chat_model.dart';
import '../services/api_service.dart';

// ──────────────────────────────────────────────
// Request state
// ──────────────────────────────────────────────
enum ChatRequestStatus { idle, loading, streaming, success, error }

class ChatState {
  final List<ChatMessage> messages;
  final ChatRequestStatus status;
  final String? error;
  final bool isConnected;

  const ChatState({
    this.messages = const [],
    this.status = ChatRequestStatus.idle,
    this.error,
    this.isConnected = false,
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    ChatRequestStatus? status,
    String? error,
    bool? isConnected,
  }) =>
      ChatState(
        messages:    messages    ?? this.messages,
        status:      status      ?? this.status,
        error:       error,
        isConnected: isConnected ?? this.isConnected,
      );
}

// ──────────────────────────────────────────────
// Notifier
// ──────────────────────────────────────────────
class ChatNotifier extends StateNotifier<ChatState> {

final ApiService _api;
final _uuid = const Uuid();
String _streamingId = '';

ChatNotifier(this._api)
    : super(const ChatState());

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    final userMsg = ChatMessage(
      id:        _uuid.v4(),
      content:   text.trim(),
      role:      MessageRole.user,
      timestamp: DateTime.now(),
    );

    // Create a placeholder for the AI streaming response
    _streamingId = _uuid.v4();
    final aiPlaceholder = ChatMessage(
      id:          _streamingId,
      content:     '',
      role:        MessageRole.assistant,
      timestamp:   DateTime.now(),
      isStreaming: true,
    );

    state = state.copyWith(
      messages: [...state.messages, userMsg, aiPlaceholder],
      status:   ChatRequestStatus.streaming,
      error:    null,
    );

    try {
  await for (final token in _api.streamChat(text.trim())) {
    if (_streamingId.isEmpty) continue;

    if (token == '[END]') {
      final msgs = List<ChatMessage>.from(state.messages);

      final idx = msgs.indexWhere(
        (m) => m.id == _streamingId,
      );

      if (idx != -1) {
        msgs[idx] = msgs[idx].copyWith(
          isStreaming: false,
        );
      }

      _streamingId = '';

      state = state.copyWith(
        messages: msgs,
        status: ChatRequestStatus.success,
      );

      break;
    }

    final msgs = List<ChatMessage>.from(state.messages);

    final idx = msgs.indexWhere(
      (m) => m.id == _streamingId,
    );

    if (idx != -1) {
      msgs[idx] = msgs[idx].copyWith(
        content: msgs[idx].content + token,
        isStreaming: true,
      );

      state = state.copyWith(
        messages: msgs,
        status: ChatRequestStatus.streaming,
      );
    }
  }
} catch (e) {
  state = state.copyWith(
    status: ChatRequestStatus.error,
    error: e.toString(),
  );
}
  }

  void clearChat() {
    state = const ChatState();
  }

 @override
void dispose() {
  super.dispose();
}

// ──────────────────────────────────────────────
// Provider declarations
// ──────────────────────────────────────────────

final apiServiceProvider = Provider<ApiService>((_) => ApiService());

final chatProvider =
    StateNotifierProvider<ChatNotifier, ChatState>((ref) {
  return ChatNotifier(
    ref.read(apiServiceProvider),
  );
});

final navigationIndexProvider = StateProvider<int>((_) => 0);
