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

  static const String _recentSearchesCacheKey = 'tenant_recent_searches';

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
    final List<String> titles = searches
        .map((search) => search.title.trim())
        .where((title) => title.isNotEmpty)
        .take(TenantSearchData.maxRecentSearches)
        .toList(growable: false);
    await CacheStorage.write(_recentSearchesCacheKey, titles);
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
