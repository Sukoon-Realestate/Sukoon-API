import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
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
  });

  final String title;
  final String subtitle;
  final Color backgroundColor;
  final IconData icon;
  final Color iconColor;
}

class RecentSearchContent {
  const RecentSearchContent({required this.title});

  final String title;
}

abstract final class TenantSearchContent {
  static const String _recentSearchesCacheKey = 'tenant_recent_searches';
  static const int _maxRecentSearches = 5;

  static const suggestedAreas = [
    SuggestedAreaContent(
      title: 'المهندسين',
      subtitle: '76 عقار',
      backgroundColor: AppColors.orangePale,
      icon: Icons.location_city_outlined,
      iconColor: AppColors.amber,
    ),
    SuggestedAreaContent(
      title: 'التجمع الخامس',
      subtitle: '89 عقار',
      backgroundColor: AppColors.bluePale,
      icon: Icons.maps_home_work_outlined,
      iconColor: AppColors.blue,
    ),
    SuggestedAreaContent(
      title: 'مدينة نصر',
      subtitle: '142 عقار',
      backgroundColor: AppColors.mintLight,
      icon: Icons.apartment_rounded,
      iconColor: AppColors.sokoonTeal,
    ),
    SuggestedAreaContent(
      title: 'مصر الجديدة',
      subtitle: '47 عقار',
      backgroundColor: AppColors.grayBackground,
      icon: Icons.account_balance_outlined,
      iconColor: AppColors.sokoonGray,
    ),
    SuggestedAreaContent(
      title: 'المعادي',
      subtitle: '58 عقار',
      backgroundColor: AppColors.redPale,
      icon: Icons.park_outlined,
      iconColor: AppColors.red,
    ),
    SuggestedAreaContent(
      title: 'الزمالك',
      subtitle: '34 عقار',
      backgroundColor: AppColors.greenPale,
      icon: Icons.water_outlined,
      iconColor: AppColors.green,
    ),
  ];

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
    required this.selectedArea,
    required this.recentSearches,
  });

  factory TenantSearchFormState.initial() {
    return TenantSearchFormState(
      query: 'مدينة نصر، القاهرة',
      selectedCategory: '',
      selectedArea: 'مدينة نصر',
      recentSearches: TenantSearchContent.recentSearches,
    );
  }

  final String query;
  final String selectedCategory;
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
    String? selectedArea,
    bool clearSelectedArea = false,
    List<RecentSearchContent>? recentSearches,
  }) {
    return TenantSearchFormState(
      query: query ?? this.query,
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
