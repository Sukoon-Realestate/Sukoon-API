import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

class ActiveFilterContent {
  const ActiveFilterContent({required this.label});

  final String label;
}

class SearchResultContent {
  const SearchResultContent({
    required this.title,
    required this.propertyType,
    required this.district,
    required this.location,
    required this.rooms,
    required this.bathrooms,
    required this.area,
    required this.tags,
    required this.price,
    required this.monthlyPrice,
    required this.rentalTerm,
    required this.tenantType,
    required this.smokingPolicy,
    required this.amenities,
    required this.photoCount,
    required this.imageColor,
    required this.imageColorEnd,
    required this.isVerified,
  });

  final String title;
  final String propertyType;
  final String district;
  final String location;
  final String rooms;
  final String bathrooms;
  final String area;
  final List<String> tags;
  final String price;
  final int monthlyPrice;
  final String rentalTerm;
  final String tenantType;
  final String smokingPolicy;
  final List<String> amenities;
  final int photoCount;
  final Color imageColor;
  final Color imageColorEnd;
  final bool isVerified;

  bool matchesQuery(String query) {
    final normalizedQuery = query.trim();
    if (normalizedQuery.isEmpty) {
      return true;
    }

    final searchableValues = [
      title,
      propertyType,
      district,
      location,
      rooms,
      bathrooms,
      area,
      price,
      rentalTerm,
      tenantType,
      smokingPolicy,
      ...tags,
      ...amenities,
    ];
    final tokens = normalizedQuery
        .replaceAll('،', ' ')
        .split(' ')
        .where((token) => token.trim().isNotEmpty);

    return tokens.every(
      (token) => searchableValues.any((value) => value.contains(token)),
    );
  }

  bool matchesFilter(String filter) {
    final minPrice = _priceValue(filter, 'من ');
    if (minPrice != null) {
      return monthlyPrice >= minPrice;
    }

    final maxPrice = _priceValue(filter, 'إلى ');
    if (maxPrice != null) {
      return monthlyPrice <= maxPrice;
    }

    return (filter == 'موثّق' && isVerified) ||
        (filter == 'إثبات ملكية' && isVerified) ||
        rooms == filter ||
        bathrooms == filter ||
        propertyType == filter ||
        district == filter ||
        location.contains(filter) ||
        rentalTerm == filter ||
        tenantType == filter ||
        smokingPolicy == filter ||
        tags.contains(filter) ||
        amenities.contains(filter);
  }

  int? _priceValue(String filter, String prefix) {
    if (!filter.startsWith(prefix)) {
      return null;
    }
    return int.tryParse(filter.replaceFirst(prefix, '').trim());
  }
}

class TenantResultsFilterGroupContent {
  const TenantResultsFilterGroupContent({
    required this.title,
    required this.options,
  });

  final String title;
  final List<String> options;
}

class TenantSearchResultsFilterState {
  const TenantSearchResultsFilterState({
    required this.query,
    required this.selectedFilters,
  });

  factory TenantSearchResultsFilterState.initial({
    String? query,
    Set<String>? selectedFilters,
  }) {
    return TenantSearchResultsFilterState(
      query: query ?? 'شقة مفروشة مدينة نصر',
      selectedFilters:
          selectedFilters ??
          const {
            'شقة',
            'مدينة نصر',
            '6 شهور',
            'عائلات',
            'ممنوع التدخين',
            'أسانسير',
          },
    );
  }

  final String query;
  final Set<String> selectedFilters;

  List<ActiveFilterContent> get activeFilters {
    return [
      for (final filter in selectedFilters) ActiveFilterContent(label: filter),
    ];
  }

  TenantSearchResultsFilterState copyWith({
    String? query,
    Set<String>? selectedFilters,
  }) {
    return TenantSearchResultsFilterState(
      query: query ?? this.query,
      selectedFilters: selectedFilters ?? this.selectedFilters,
    );
  }
}

abstract final class TenantSearchResultContent {
  static const propertyTypeOptions = [
    'شقة',
    'ستوديو',
    'غرفة',
    'دوبلكس',
    'فيلا',
  ];

  static const districtOptions = [
    'مدينة نصر',
    'التجمع الخامس',
    'مصر الجديدة',
    'الشيخ زايد',
    'المهندسين',
    'الزمالك',
  ];

  static const rentalTermOptions = ['3 شهور', '6 شهور', 'سنة'];
  static const tenantTypeOptions = ['عائلات', 'فردي', 'بنات فقط', 'ولاد فقط'];
  static const smokingOptions = ['ممنوع التدخين', 'مسموح التدخين'];
  static const amenityOptions = [
    'أسانسير',
    'جراج',
    'قريبة من المترو',
    'مكيف',
    'واي فاي',
  ];

  static const filterGroups = [
    TenantResultsFilterGroupContent(
      title: 'نوع العقار',
      options: propertyTypeOptions,
    ),
    TenantResultsFilterGroupContent(title: 'المنطقة', options: districtOptions),
    TenantResultsFilterGroupContent(
      title: 'مدة الإيجار',
      options: rentalTermOptions,
    ),
    TenantResultsFilterGroupContent(
      title: 'مناسب لـ',
      options: tenantTypeOptions,
    ),
    TenantResultsFilterGroupContent(title: 'التدخين', options: smokingOptions),
    TenantResultsFilterGroupContent(title: 'الخدمات', options: amenityOptions),
  ];

  static const activeFilters = [
    ActiveFilterContent(label: 'شقة'),
    ActiveFilterContent(label: 'مدينة نصر'),
    ActiveFilterContent(label: '6 شهور'),
    ActiveFilterContent(label: 'عائلات'),
    ActiveFilterContent(label: 'ممنوع التدخين'),
    ActiveFilterContent(label: 'أسانسير'),
  ];

  static const results = [
    SearchResultContent(
      title: 'شقة مفروشة 3 غرف',
      propertyType: 'شقة',
      district: 'مدينة نصر',
      location: 'مدينة نصر، القاهرة',
      rooms: '3 غرف',
      bathrooms: '2 حمام',
      area: '90م²',
      tags: ['عائلات', 'أسانسير', 'ممنوع التدخين'],
      price: '6,500',
      monthlyPrice: 6500,
      rentalTerm: '6 شهور',
      tenantType: 'عائلات',
      smokingPolicy: 'ممنوع التدخين',
      amenities: ['أسانسير', 'مكيف', 'واي فاي'],
      photoCount: 8,
      imageColor: AppColors.sokoonTeal,
      imageColorEnd: AppColors.tealAlpha80,
      isVerified: false,
    ),
    SearchResultContent(
      title: 'ستوديو واسع',
      propertyType: 'ستوديو',
      district: 'التجمع الخامس',
      location: 'التجمع الخامس، القاهرة',
      rooms: '1 غرفة',
      bathrooms: '1 حمام',
      area: '55م²',
      tags: ['فردي', 'قريبة من المترو'],
      price: '3,200',
      monthlyPrice: 3200,
      rentalTerm: '3 شهور',
      tenantType: 'فردي',
      smokingPolicy: 'ممنوع التدخين',
      amenities: ['قريبة من المترو', 'واي فاي'],
      photoCount: 12,
      imageColor: AppColors.blue,
      imageColorEnd: AppColors.blueGrayLight,
      isVerified: true,
    ),
    SearchResultContent(
      title: 'غرفة مفروشة',
      propertyType: 'غرفة',
      district: 'مصر الجديدة',
      location: 'مصر الجديدة، القاهرة',
      rooms: '1 غرفة',
      bathrooms: '1 حمام',
      area: '30م²',
      tags: ['بنات فقط', 'ممنوع التدخين'],
      price: '1,800',
      monthlyPrice: 1800,
      rentalTerm: '6 شهور',
      tenantType: 'بنات فقط',
      smokingPolicy: 'ممنوع التدخين',
      amenities: ['واي فاي'],
      photoCount: 6,
      imageColor: AppColors.rose,
      imageColorEnd: AppColors.roseAlpha19,
      isVerified: false,
    ),
    SearchResultContent(
      title: 'شقة 4 غرف فيلا',
      propertyType: 'فيلا',
      district: 'الشيخ زايد',
      location: 'الشيخ زايد، الجيزة',
      rooms: '4 غرف',
      bathrooms: '3 حمام',
      area: '200م²',
      tags: ['عائلات', 'جراج', 'أسانسير'],
      price: '12,000',
      monthlyPrice: 12000,
      rentalTerm: 'سنة',
      tenantType: 'عائلات',
      smokingPolicy: 'مسموح التدخين',
      amenities: ['جراج', 'أسانسير', 'مكيف'],
      photoCount: 15,
      imageColor: AppColors.gold,
      imageColorEnd: AppColors.goldAlpha15,
      isVerified: true,
    ),
    SearchResultContent(
      title: 'شقة هادئة في المهندسين',
      propertyType: 'شقة',
      district: 'المهندسين',
      location: 'المهندسين، الجيزة',
      rooms: '2 غرف',
      bathrooms: '1 حمام',
      area: '75م²',
      tags: ['فردي', 'مكيف', 'قريبة من المترو'],
      price: '5,200',
      monthlyPrice: 5200,
      rentalTerm: '6 شهور',
      tenantType: 'فردي',
      smokingPolicy: 'ممنوع التدخين',
      amenities: ['مكيف', 'قريبة من المترو'],
      photoCount: 10,
      imageColor: AppColors.green,
      imageColorEnd: AppColors.greenAlpha19,
      isVerified: true,
    ),
  ];

  static List<SearchResultContent> filterResults(
    TenantSearchResultsFilterState filters,
  ) {
    return results.where((item) {
      final matchesQuery = item.matchesQuery(filters.query);
      final matchesFilters = filters.selectedFilters.every(item.matchesFilter);
      return matchesQuery && matchesFilters;
    }).toList();
  }
}
