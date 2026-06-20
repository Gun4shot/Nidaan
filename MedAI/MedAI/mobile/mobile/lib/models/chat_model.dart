// lib/models/chat_model.dart
import 'package:flutter/material.dart';

enum MessageRole { user, assistant }
enum MessageStatus { sending, sent, error }

class ChatMessage {
  final String id;
  final String content;
  final MessageRole role;
  final MessageStatus status;
  final DateTime timestamp;
  final bool isStreaming;

  const ChatMessage({
    required this.id,
    required this.content,
    required this.role,
    this.status = MessageStatus.sent,
    required this.timestamp,
    this.isStreaming = false,
  });

  ChatMessage copyWith({
    String? content,
    MessageStatus? status,
    bool? isStreaming,
  }) {
    return ChatMessage(
      id: id,
      content: content ?? this.content,
      role: role,
      status: status ?? this.status,
      timestamp: timestamp,
      isStreaming: isStreaming ?? this.isStreaming,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'content': content,
    'role': role.name,
    'timestamp': timestamp.toIso8601String(),
  };

  factory ChatMessage.fromJson(Map<String, dynamic> json) => ChatMessage(
    id: json['id'],
    content: json['content'],
    role: MessageRole.values.firstWhere((e) => e.name == json['role']),
    timestamp: DateTime.parse(json['timestamp']),
  );
}
