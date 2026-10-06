import 'package:melos_core/core/helpers/cache_service.dart';
import 'models/decision_notebook.dart';

abstract interface class DecisionToolsStore {
  Future<DecisionNotebook> read(String accountId);
  Future<void> write(String accountId, DecisionNotebook notebook);
}

class DecisionToolsData implements DecisionToolsStore {
  const DecisionToolsData();
  static String keyFor(String accountId) =>
      'decision_notebook_v1_${accountId.isEmpty ? 'guest' : accountId}';
  @override
  Future<DecisionNotebook> read(String accountId) async {
    final json = CacheStorage.read(keyFor(accountId), isDecoded: true);
    if (json is! Map<String, dynamic>) return const DecisionNotebook.initial();
    return DecisionNotebook.fromJson(json);
  }

  @override
  Future<void> write(String accountId, DecisionNotebook notebook) =>
      CacheStorage.write(keyFor(accountId), notebook.toJson());
}
