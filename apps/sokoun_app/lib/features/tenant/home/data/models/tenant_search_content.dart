import 'package:melos_core/core/helpers/cache_service.dart';

class SearchCategoryContent {
  const SearchCategoryContent({required this.label, this.isSelected = false});

  final String label;
  final bool isSelected;
}

class RecentSearchContent {
  const RecentSearchContent({required this.title});

  final String title;
}

abstract final class TenantSearchContent {
  static const String _recentSearchesCacheKey = 'tenant_recent_searches';
  static const int _maxRecentSearches = 5;

  static List<RecentSearchContent> get recentSearches {
    return CacheStorage.readList(_recentSearchesCacheKey)
        .where((title) => title.trim().isNotEmpty)
        .map((title) => RecentSearchContent(title: title))
        .take(_maxRecentSearches)
        .toList(growable: false);
  }

  static Future<void> saveRecentSearches(
    List<RecentSearchContent> searches,
  ) async {
    final List<String> titles = searches
        .map((search) => search.title.trim())
        .where((title) => title.isNotEmpty)
        .take(_maxRecentSearches)
        .toList(growable: false);
    await CacheStorage.write(_recentSearchesCacheKey, titles);
  }
}

class TenantSearchFormState {
  const TenantSearchFormState({
    required this.selectedCategory,
    required this.selectedArea,
    required this.recentSearches,
  });

  factory TenantSearchFormState.initial() {
    return TenantSearchFormState(
      selectedCategory: '',
      selectedArea: null,
      recentSearches: TenantSearchContent.recentSearches,
    );
  }

  final String selectedCategory;
  final String? selectedArea;
  final List<RecentSearchContent> recentSearches;

  TenantSearchFormState copyWith({
    String? selectedCategory,
    String? selectedArea,
    bool clearSelectedArea = false,
    List<RecentSearchContent>? recentSearches,
  }) {
    return TenantSearchFormState(
      selectedCategory: selectedCategory ?? this.selectedCategory,
      selectedArea: clearSelectedArea
          ? null
          : selectedArea ?? this.selectedArea,
      recentSearches: recentSearches ?? this.recentSearches,
    );
  }

  TenantSearchFormState withRecentSearch(String title) {
    final normalizedTitle = title.trim();
    if (normalizedTitle.isEmpty) {
      return this;
    }

    final updatedRecent = [
      RecentSearchContent(title: normalizedTitle),
      for (final search in recentSearches)
        if (search.title != normalizedTitle) search,
    ].take(5).toList();

    return copyWith(recentSearches: updatedRecent);
  }
}
