import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:sokoun_app/features/shared/recovery/data/private_recovery_data.dart';
import 'package:sokoun_app/features/shared/recovery/data/recovery_scope.dart';
import 'models/decision_notebook.dart';

abstract interface class DecisionToolsStore {
  Future<DecisionNotebook> read(String accountId);
  Future<void> write(String accountId, DecisionNotebook notebook);
}

class DecisionToolsData implements DecisionToolsStore {
  const DecisionToolsData();
  static String keyFor(String accountId) =>
      'decision_notebook_v1_${accountId.isEmpty ? 'guest' : accountId}';
  PrivateDraftStore<DecisionNotebook> _store(String accountId) =>
      PrivateDraftStore(
        scope: () => RecoveryScope.currentEnvironment().then(
          (environment) => RecoveryScope(
            environment: environment,
            accountId: accountId,
            flow: 'decision_notebook',
            workspace: 'tenant',
          ),
        ),
        encode: (value) => value.toJson(),
        decode: DecisionNotebook.fromJson,
      );
  @override
  Future<DecisionNotebook> read(String accountId) async {
    // Unprotected legacy records lack environment provenance and cannot be reused.
    await CacheStorage.delete(keyFor(accountId));
    return (await _store(accountId).read())?.value ??
        const DecisionNotebook.initial();
  }

  @override
  Future<void> write(String accountId, DecisionNotebook notebook) async {
    await _store(accountId).write(notebook);
  }
}
