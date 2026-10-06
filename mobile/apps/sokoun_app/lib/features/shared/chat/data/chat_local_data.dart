import 'dart:convert';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'models/chat_local_state.dart';

abstract interface class ChatLocalStore {
  Future<ChatLocalState> read();
  Future<void> write(ChatLocalState state);
}

class ChatLocalData implements ChatLocalStore {
  const ChatLocalData({required this.accountId, required this.conversationId});
  final String accountId;
  final String conversationId;
  static String keyFor(String accountId, String conversationId) =>
      'chat_drafts_v1_${base64Url.encode(utf8.encode(jsonEncode([accountId, conversationId])))}';
  String get _key => keyFor(accountId, conversationId);
  @override
  Future<ChatLocalState> read() async {
    if (accountId.isEmpty || accountId == '0' || conversationId.isEmpty) {
      return const ChatLocalState.initial();
    }
    final json = await SecureStorage.read(_key);
    if (json == null || json.isEmpty) return const ChatLocalState.initial();
    return ChatLocalState.fromJson(
      Map<String, dynamic>.from(jsonDecode(json) as Map),
    );
  }

  @override
  Future<void> write(ChatLocalState state) async {
    if (accountId.isEmpty || accountId == '0' || conversationId.isEmpty) return;
    if (state.draft.isEmpty && state.messages.isEmpty) {
      await SecureStorage.delete(_key);
      return;
    }
    await SecureStorage.write(_key, jsonEncode(state.toJson()));
  }
}
