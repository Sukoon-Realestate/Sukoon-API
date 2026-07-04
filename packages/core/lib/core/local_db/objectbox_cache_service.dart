import 'dart:convert';

import 'package:objectbox/objectbox.dart';
import 'package:path_provider/path_provider.dart';

import '../extensions/object.dart';
import 'cached_response.dart';
import '../../../objectbox.g.dart'; // generated — run: dart run build_runner build

class ObjectBoxCacheService {
  static late final Store _store;
  static late final Box<CachedResponse> _box;

  static Future<void> init() async {
    final docsDir = await getApplicationDocumentsDirectory();
    _store = await openStore(directory: '${docsDir.path}/objectbox');
    _box = _store.box<CachedResponse>();
  }

  static void save(String key, Map<String, dynamic> json) {
    final jsonStr = jsonEncode(json);
    final existing = _box.query(CachedResponse_.key.equals(key)).build().findFirst();
    if (existing.isNotNull) {
      existing!.jsonValue = jsonStr;
      _box.put(existing);
    } else {
      _box.put(CachedResponse(key: key, jsonValue: jsonStr));
    }
  }

  static Map<String, dynamic>? read(String key) {
    final cached = _box.query(CachedResponse_.key.equals(key)).build().findFirst();
    if (cached == null) return null;
    try {
      return jsonDecode(cached.jsonValue) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  }

  static void clearAll() {
    _box.removeAll();
  }
}
