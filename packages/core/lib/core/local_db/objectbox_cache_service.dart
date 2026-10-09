import 'dart:convert';

import 'package:objectbox/objectbox.dart';
import 'package:path_provider/path_provider.dart';

import '../extensions/object.dart';
import '../network/account_session.dart';
import 'cached_response.dart';
import 'read_cache_policy.dart';
import '../../../objectbox.g.dart'; // generated — run: dart run build_runner build

class ObjectBoxCacheService {
  static late final Store _store;
  static Box<CachedResponse>? _box;

  static Future<void> init() async {
    final docsDir = await getApplicationDocumentsDirectory();
    _store = await openStore(directory: '${docsDir.path}/objectbox');
    _box = _store.box<CachedResponse>();
  }

  static String _key(String key, ReadCachePolicy? policy) =>
      policy?.publicContent == true
      ? 'public_v2_${ReadCacheContext.scope}_$key'
      : AccountSession.cacheKey(key);
  static void save(
    String key,
    Map<String, dynamic> json, {
    ReadCachePolicy? policy,
  }) {
    if (policy?.persist == false) return;
    final Box<CachedResponse>? box = _box;
    if (box == null) return;
    key = _key(key, policy);
    final String jsonStr = jsonEncode(
      policy == null
          ? json
          : {
              'schema': 2,
              'saved_at': DateTime.now().toUtc().toIso8601String(),
              'expires_at': DateTime.now()
                  .toUtc()
                  .add(policy.maxAge)
                  .toIso8601String(),
              'value': json,
            },
    );
    if (policy != null && utf8.encode(jsonStr).length > 32 * 1024 * 1024) {
      return;
    }
    final Query<CachedResponse> query = box
        .query(CachedResponse_.key.equals(key))
        .build();
    final CachedResponse? existing = query.findFirst();
    query.close();
    if (existing.isNotNull) {
      existing!.jsonValue = jsonStr;
      box.put(existing);
    } else {
      box.put(CachedResponse(key: key, jsonValue: jsonStr));
    }
    if (policy?.publicContent == true) _prunePublic(box);
  }

  static void _prunePublic(Box<CachedResponse> box) {
    final List<CachedResponse> entries = box
        .getAll()
        .where((entry) => entry.key.startsWith('public_v2_'))
        .toList();
    DateTime savedAt(CachedResponse entry) {
      try {
        final Map envelope = jsonDecode(entry.jsonValue) as Map;
        return DateTime.tryParse('${envelope['saved_at']}') ??
            DateTime.fromMillisecondsSinceEpoch(0, isUtc: true);
      } catch (_) {
        return DateTime.fromMillisecondsSinceEpoch(0, isUtc: true);
      }
    }

    entries.sort((a, b) => savedAt(a).compareTo(savedAt(b)));
    int bytes = entries.fold(
      0,
      (total, entry) => total + utf8.encode(entry.jsonValue).length,
    );
    while (entries.length > 200 || bytes > 32 * 1024 * 1024) {
      final CachedResponse oldest = entries.removeAt(0);
      bytes -= utf8.encode(oldest.jsonValue).length;
      box.remove(oldest.id);
    }
  }

  static Map<String, dynamic>? read(String key, {ReadCachePolicy? policy}) {
    if (policy?.persist == false) return null;
    final Box<CachedResponse>? box = _box;
    if (box == null) return null;
    final Query<CachedResponse> query = box
        .query(CachedResponse_.key.equals(_key(key, policy)))
        .build();
    final CachedResponse? cached = query.findFirst();
    query.close();
    if (cached == null) return null;
    try {
      final Map<String, dynamic> json =
          jsonDecode(cached.jsonValue) as Map<String, dynamic>;
      if (policy == null) return json;
      final DateTime? expiry = DateTime.tryParse(
        json['expires_at']?.toString() ?? '',
      );
      if (json['schema'] != 2 ||
          expiry == null ||
          !expiry.isAfter(DateTime.now().toUtc())) {
        box.remove(cached.id);
        return null;
      }
      return Map<String, dynamic>.from(json['value'] as Map);
    } catch (_) {
      return null;
    }
  }

  static void clearAll() {
    _box?.removeAll();
  }

  static void remove(String key) {
    final Query<CachedResponse>? query = _box
        ?.query(CachedResponse_.key.equals(AccountSession.cacheKey(key)))
        .build();
    query?.remove();
    query?.close();
    final Query<CachedResponse>? publicQuery = _box
        ?.query(CachedResponse_.key.endsWith('_$key'))
        .build();
    publicQuery?.remove();
    publicQuery?.close();
  }

  static void removePublicCollections() {
    final Query<CachedResponse>? query = _box
        ?.query(CachedResponse_.key.startsWith('public_v2_'))
        .build();
    query?.remove();
    query?.close();
  }

  /// Sokoun no longer persists private reads without at-rest protection.
  static void removeLegacyAccountEntries() {
    final Query<CachedResponse>? query = _box
        ?.query(CachedResponse_.key.startsWith('account_v1_'))
        .build();
    query?.remove();
    query?.close();
  }
}
