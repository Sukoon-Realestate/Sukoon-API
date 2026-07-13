import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

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
  static const categories = [
    SearchCategoryContent(label: 'الكل', isSelected: true),
    SearchCategoryContent(label: 'شقة'),
    SearchCategoryContent(label: 'ستوديو'),
    SearchCategoryContent(label: 'غرفة'),
    SearchCategoryContent(label: 'دوبلكس'),
    SearchCategoryContent(label: 'فيلا'),
  ];

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

  static const recentSearches = [
    RecentSearchContent(title: 'شقة مفروشة مدينة نصر'),
    RecentSearchContent(title: 'ستوديو التجمع الخامس'),
    RecentSearchContent(title: 'غرفة في الزمالك'),
  ];
}
