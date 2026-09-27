import 'dart:convert';

import 'package:objectbox/objectbox.dart';
import 'package:path_provider/path_provider.dart';

import '../extensions/object.dart';
import '../network/account_session.dart';
import 'cached_response.dart';
import '../../../objectbox.g.dart'; // generated — run: dart run build_runner build

class ObjectBoxCacheService {
  static late final Store _store;
  static Box<CachedResponse>? _box;

  static Future<void> init() async {
    final docsDir = await getApplicationDocumentsDirectory();
    _store = await openStore(directory: '${docsDir.path}/objectbox');
    _box = _store.box<CachedResponse>();
  }

  static void save(String key, Map<String, dynamic> json) {
    final Box<CachedResponse>? box = _box;
    if (box == null) return;
    key = AccountSession.cacheKey(key);
    final jsonStr = jsonEncode(json);
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
  }

  static Map<String, dynamic>? read(String key) {
    final Box<CachedResponse>? box = _box;
    if (box == null) return null;
    final Query<CachedResponse> query = box
        .query(CachedResponse_.key.equals(AccountSession.cacheKey(key)))
        .build();
    final CachedResponse? cached = query.findFirst();
    query.close();
    if (cached == null) return null;
    try {
      return jsonDecode(cached.jsonValue) as Map<String, dynamic>;
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
  }
}
