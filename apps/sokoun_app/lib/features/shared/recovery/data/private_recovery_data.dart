import 'dart:async';
import 'dart:convert';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'recovery_scope.dart';

abstract interface class RecoveryStorage {
  Future<String?> read(String key);
  Future<void> write(String key, String value);
  Future<void> delete(String key);
}

class ProtectedRecoveryStorage implements RecoveryStorage {
  const ProtectedRecoveryStorage();
  @override
  Future<String?> read(String key) => SecureStorage.read(key);
  @override
  Future<void> write(String key, String value) =>
      SecureStorage.write(key, value);
  @override
  Future<void> delete(String key) => SecureStorage.delete(key);
}

/// Small, protected record store. The index contains keys, never form contents.
/// A single ordered lane prevents logout deletion racing an in-flight write.
abstract final class PrivateRecoveryData {
  static const String _indexKey = 'sokoun_private_index_v2';
  static Future<void>? _operations;
  static bool _initialized = false;
  static void initialize() {
    if (_initialized) return;
    _initialized = true;
    AccountSession.registerCleanup(clearAccount);
  }

  static Future<T> ordered<T>(Future<T> Function() operation) {
    final Future<T> result = _operations == null
        ? Future.sync(operation)
        : _operations!.then((_) => operation());
    late final Future<void> tail;
    void release() {
      if (identical(_operations, tail)) _operations = null;
    }

    tail = result.then<void>(
      (_) => release(),
      onError: (Object _, StackTrace __) => release(),
    );
    _operations = tail;
    return result;
  }

  static Future<Map<String, String>> _index(RecoveryStorage storage) async {
    final String? raw = await storage.read(_indexKey);
    return raw == null ? {} : Map<String, String>.from(jsonDecode(raw) as Map);
  }

  static Future<void> clearAccount(String accountId) => ordered(() async {
    const RecoveryStorage storage = ProtectedRecoveryStorage();
    final Map<String, String> index = await _index(storage);
    for (final String key in index.keys.toList()) {
      if (index[key] != accountId) continue;
      await storage.delete(key);
      index.remove(key);
    }
    // Legacy chat keys were protected but had no environment or cleanup index.
    for (final String key in (await SecureStorage.readAll()).keys) {
      if (!key.startsWith('chat_drafts_v1_')) continue;
      try {
        final List identity =
            jsonDecode(
                  utf8.decode(
                    base64Url.decode(key.substring('chat_drafts_v1_'.length)),
                  ),
                )
                as List;
        if (identity.first == accountId) await storage.delete(key);
      } catch (_) {
        /* Do not infer ownership from malformed keys. */
      }
    }
    await storage.write(_indexKey, jsonEncode(index));
  });

  static Future<void> write({
    required RecoveryScope scope,
    required Map<String, dynamic> value,
    required int generation,
    RecoveryStorage storage = const ProtectedRecoveryStorage(),
  }) => ordered(() async {
    if (generation != AccountSession.generation) {
      throw StateError('Expired draft session');
    }
    // Index first: a crash between index and payload still permits cleanup.
    final Map<String, String> index = await _index(storage);
    index[scope.key] = scope.accountId;
    await storage.write(_indexKey, jsonEncode(index));
    if (generation != AccountSession.generation) {
      throw StateError('Expired draft session');
    }
    await storage.write(scope.key, jsonEncode(value));
  });

  static Future<void> delete(
    RecoveryScope scope, {
    RecoveryStorage storage = const ProtectedRecoveryStorage(),
  }) => ordered(() async {
    await storage.delete(scope.key);
    final Map<String, String> index = await _index(storage);
    index.remove(scope.key);
    await storage.write(_indexKey, jsonEncode(index));
  });
}

class DraftRecord<T> {
  const DraftRecord({
    required this.value,
    required this.sequence,
    required this.savedAt,
    this.serverRevision = '',
  });
  final T value;
  final int sequence;
  final DateTime savedAt;
  final String serverRevision;
}

class PrivateDraftStore<T> {
  PrivateDraftStore({
    required Future<RecoveryScope> Function() scope,
    required this.encode,
    required this.decode,
    this.storage = const ProtectedRecoveryStorage(),
  }) : _resolveScope = scope;
  final Future<RecoveryScope> Function() _resolveScope;
  Future<RecoveryScope>? _scopeValue;
  Future<RecoveryScope> get scope =>
      _scopeValue ??= _resolveScope().catchError((Object error) {
        _scopeValue = null;
        throw error;
      });
  final Map<String, dynamic> Function(T) encode;
  final T Function(Map<String, dynamic>) decode;
  final RecoveryStorage storage;
  final int _generation = AccountSession.generation;
  int _sequence = 0;
  Future<DraftRecord<T>?> read() async {
    PrivateRecoveryData.initialize();
    if (_generation != AccountSession.generation) return null;
    final RecoveryScope identity = await scope;
    if (identity.accountId.isEmpty || identity.accountId == '0') return null;
    if (storage is ProtectedRecoveryStorage &&
        identity.accountId != AccountSession.userId) {
      return null;
    }
    final String? raw = await storage.read(identity.key);
    if (_generation != AccountSession.generation || raw == null) return null;
    final Map<String, dynamic> json = Map<String, dynamic>.from(
      jsonDecode(raw) as Map,
    );
    if (json['schema'] != 2 || json['scope'] != identity.key) return null;
    _sequence = (json['sequence'] as num?)?.toInt() ?? 0;
    return DraftRecord(
      value: decode(Map<String, dynamic>.from(json['value'] as Map)),
      sequence: _sequence,
      savedAt: DateTime.parse(json['saved_at'] as String),
      serverRevision: json['server_revision'] as String? ?? '',
    );
  }

  Future<DraftRecord<T>> write(T value, {String serverRevision = ''}) async {
    PrivateRecoveryData.initialize();
    if (_generation != AccountSession.generation) {
      throw StateError('Expired draft session');
    }
    final RecoveryScope identity = await scope;
    if (identity.accountId.isEmpty || identity.accountId == '0') {
      throw StateError('A signed-in account is required');
    }
    if (storage is ProtectedRecoveryStorage &&
        identity.accountId != AccountSession.userId) {
      throw StateError('Expired account scope');
    }
    final DraftRecord<T> record = DraftRecord(
      value: value,
      sequence: ++_sequence,
      savedAt: DateTime.now().toUtc(),
      serverRevision: serverRevision,
    );
    await PrivateRecoveryData.write(
      scope: identity,
      generation: _generation,
      storage: storage,
      value: {
        'schema': 2,
        'scope': identity.key,
        'sequence': record.sequence,
        'saved_at': record.savedAt.toIso8601String(),
        'server_revision': serverRevision,
        'value': encode(value),
      },
    );
    return record;
  }

  Future<void> clear() async =>
      PrivateRecoveryData.delete(await scope, storage: storage);
}
