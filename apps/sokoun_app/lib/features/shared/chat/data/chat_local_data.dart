import 'dart:convert';
import 'package:melos_core/core/helpers/cache_service.dart';
import '../../recovery/data/private_recovery_data.dart';
import '../../recovery/data/recovery_scope.dart';
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
  PrivateDraftStore<ChatLocalState> _store() => PrivateDraftStore(
    scope: () => RecoveryScope.currentEnvironment().then(
      (environment) => RecoveryScope(
        environment: environment,
        accountId: accountId,
        flow: 'chat',
        entityId: conversationId,
      ),
    ),
    encode: (value) => value.toJson(),
    decode: ChatLocalState.fromJson,
  );
  @override
  Future<ChatLocalState> read() async {
    if (accountId.isEmpty || accountId == '0' || conversationId.isEmpty) {
      return const ChatLocalState.initial();
    }
    await SecureStorage.delete(keyFor(accountId, conversationId));
    return (await _store().read())?.value ?? const ChatLocalState.initial();
  }

  @override
  Future<void> write(ChatLocalState state) async {
    if (accountId.isEmpty || accountId == '0' || conversationId.isEmpty) {
      throw StateError('An authorized conversation is required');
    }
    final store = _store();
    if (state.draft.isEmpty && state.messages.isEmpty) {
      await store.clear();
    } else {
      await store.write(state);
    }
  }
}
