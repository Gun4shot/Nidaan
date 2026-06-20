// lib/services/websocket_service.dart
import 'dart:async';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../core/constants/app_constants.dart';

enum WsStatus { disconnected, connecting, connected, error }

class WebSocketService {
  static final WebSocketService _instance = WebSocketService._internal();
  factory WebSocketService() => _instance;
  WebSocketService._internal();

  WebSocketChannel? _channel;
  WsStatus _status = WsStatus.disconnected;

  final StreamController<String> _tokenController =
      StreamController<String>.broadcast();
  final StreamController<WsStatus> _statusController =
      StreamController<WsStatus>.broadcast();

  Stream<String> get tokenStream   => _tokenController.stream;
  Stream<WsStatus> get statusStream => _statusController.stream;
  WsStatus get status => _status;

  void connect() {
    if (_status == WsStatus.connected || _status == WsStatus.connecting) return;
    _setStatus(WsStatus.connecting);
    try {
      _channel = WebSocketChannel.connect(
        Uri.parse('${AppConstants.wsUrl}${AppConstants.wsEndpoint}'),
      );
      _setStatus(WsStatus.connected);

      _channel!.stream.listen(
        (data) {
          if (data is String) {
            // Each incoming string is a streaming token from the LLM
            _tokenController.add(data);
          }
        },
        onError: (_) => _setStatus(WsStatus.error),
        onDone:  () => _setStatus(WsStatus.disconnected),
      );
    } catch (_) {
      _setStatus(WsStatus.error);
    }
  }

  void sendMessage(String message) {
    if (_status != WsStatus.connected) connect();
    _channel?.sink.add(message);
  }

  void disconnect() {
    _channel?.sink.close();
    _setStatus(WsStatus.disconnected);
  }

  void _setStatus(WsStatus s) {
    _status = s;
    _statusController.add(s);
  }

  void dispose() {
    disconnect();
    _tokenController.close();
    _statusController.close();
  }
}
