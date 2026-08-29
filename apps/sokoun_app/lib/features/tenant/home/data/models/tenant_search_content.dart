import 'package:flutter/material.dart';
import 'package:melos_core/core/helpers/cache_service.dart';

class SearchCategoryContent {
  const SearchCategoryContent({required this.label, this.isSelected = false});

  final String label;
  final bool isSelected;
}

class SuggestedAreaContent {
  const SuggestedAreaContent({
    required this.title,
    required this.subtitle,
    required this.backgroundColor,
    required this.icon,
    required this.iconColor,
    required this.searchQuery,
  });

  final String title;
  final String subtitle;
  final Color backgroundColor;
  final IconData icon;
  final Color iconColor;
  final String searchQuery;
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
    required this.query,
    required this.selectedCategory,
    required this.selectedPropertyTypeId,
    required this.selectedArea,
    required this.recentSearches,
  });

  factory TenantSearchFormState.initial() {
    return TenantSearchFormState(
      query: 'مدينة نصر، القاهرة',
      selectedCategory: '',
      selectedPropertyTypeId: '',
      selectedArea: null,
      recentSearches: TenantSearchContent.recentSearches,
    );
  }

  final String query;
  final String selectedCategory;
  final String selectedPropertyTypeId;
  final String? selectedArea;
  final List<RecentSearchContent> recentSearches;

  bool get canSearch {
    return query.trim().isNotEmpty ||
        selectedCategory.isNotEmpty ||
        selectedArea != null;
  }

  Set<String> get resultFilters {
    return {
      if (selectedCategory.isNotEmpty) selectedCategory,
      if (selectedArea != null) selectedArea!,
    };
  }

  TenantSearchFormState copyWith({
    String? query,
    String? selectedCategory,
    String? selectedPropertyTypeId,
    String? selectedArea,
    bool clearSelectedArea = false,
    List<RecentSearchContent>? recentSearches,
  }) {
    return TenantSearchFormState(
      query: query ?? this.query,
      selectedCategory: selectedCategory ?? this.selectedCategory,
      selectedPropertyTypeId:
          selectedPropertyTypeId ?? this.selectedPropertyTypeId,
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
