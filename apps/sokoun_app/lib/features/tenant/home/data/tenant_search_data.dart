import 'dart:convert';
import 'package:melos_core/core/local_db/read_cache_policy.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_content.dart';

abstract interface class TenantSearchDataSource {
  int get maxRecentSearches;

  List<RecentSearchContent> getRecentSearches();

  Future<void> saveRecentSearches(List<RecentSearchContent> searches);
}

final class TenantSearchCacheDataSource implements TenantSearchDataSource {
  const TenantSearchCacheDataSource();

  static const String _prefix = 'tenant_recent_searches_v2_';
  static bool _initialized = false;
  static String get _recentSearchesCacheKey {
    if (!_initialized) {
      _initialized = true;
      AccountSession.registerCleanup((accountId) async {
        for (final key
            in CacheStorage.keys
                .where((key) => key.startsWith(_prefix))
                .toList()) {
          try {
            final identity =
                jsonDecode(
                      utf8.decode(
                        base64Url.decode(key.substring(_prefix.length)),
                      ),
                    )
                    as List;
            if (identity[1] == accountId) await CacheStorage.delete(key);
          } catch (_) {
            /* Malformed records are never restored. */
          }
        }
      });
    }
    return '$_prefix${base64Url.encode(utf8.encode(jsonEncode([ReadCacheContext.environment, AccountSession.userId ?? 'guest'])))}';
  }

  @override
  int get maxRecentSearches => TenantSearchData.maxRecentSearches;

  @override
  List<RecentSearchContent> getRecentSearches() {
    return CacheStorage.readList(_recentSearchesCacheKey)
        .where((title) => title.trim().isNotEmpty)
        .map((title) => RecentSearchContent(title: title))
        .take(TenantSearchData.maxRecentSearches)
        .toList(growable: false);
  }

  @override
  Future<void> saveRecentSearches(List<RecentSearchContent> searches) async {
    final String key = _recentSearchesCacheKey;
    final List<String> titles = searches
        .map((search) => search.title.trim())
        .where((title) => title.isNotEmpty)
        .take(TenantSearchData.maxRecentSearches)
        .toList(growable: false);
    await CacheStorage.write(key, titles);
  }
}

abstract final class TenantSearchData {
  static const int maxRecentSearches = 5;

  static TenantSearchDataSource get source =>
      injector.isRegistered<TenantSearchDataSource>()
      ? injector<TenantSearchDataSource>()
      : const TenantSearchCacheDataSource();

  static List<RecentSearchContent> getRecentSearches() =>
      source.getRecentSearches();

  static Future<void> saveRecentSearches(List<RecentSearchContent> searches) =>
      source.saveRecentSearches(searches);
}
