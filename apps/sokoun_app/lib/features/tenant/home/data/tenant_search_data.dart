import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_content.dart';

abstract final class TenantSearchData {
  static const String _recentSearchesCacheKey = 'tenant_recent_searches';
  static const int maxRecentSearches = 5;

  static List<RecentSearchContent> getRecentSearches() {
    return CacheStorage.readList(_recentSearchesCacheKey)
        .where((title) => title.trim().isNotEmpty)
        .map((title) => RecentSearchContent(title: title))
        .take(maxRecentSearches)
        .toList(growable: false);
  }

  static Future<void> saveRecentSearches(
    List<RecentSearchContent> searches,
  ) async {
    final List<String> titles = searches
        .map((search) => search.title.trim())
        .where((title) => title.isNotEmpty)
        .take(maxRecentSearches)
        .toList(growable: false);
    await CacheStorage.write(_recentSearchesCacheKey, titles);
  }
}
