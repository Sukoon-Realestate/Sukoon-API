import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';

import 'property_details_model.dart';

class TenantPropertyMetricContent {
  const TenantPropertyMetricContent({
    required this.icon,
    required this.value,
    required this.label,
  });

  final IconData icon;
  final String value;
  final String label;
}

class TenantNearbyPlaceContent {
  const TenantNearbyPlaceContent({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final String title;
  final String subtitle;
}

class TenantPropertyDetailsContent {
  const TenantPropertyDetailsContent({
    required this.id,
    required this.title,
    required this.propertyType,
    required this.location,
    required this.price,
    required this.rating,
    required this.reviewCount,
    required this.isVerified,
    required this.isFurnished,
    required this.isFavorite,
    required this.isSaved,
    required this.metrics,
    required this.description,
    required this.amenities,
    required this.photoLabels,
    required this.nearbyPlaces,
    required this.ownerName,
    required this.ownerId,
    required this.ownerMeta,
    required this.imageColors,
    required this.latitude,
    required this.longitude,
    this.imageUrls = const [],
    this.videoUrl,
    this.videoDuration,
    this.propertyLink = '',
  });

  factory TenantPropertyDetailsContent.fromModel(PropertyDetailsModel model) {
    return TenantPropertyDetailsContent(
      id: model.id,
      title: model.title,
      propertyType: model.propertyTypeLabel,
      location: model.locationLabel,
      price: model.formattedPrice,
      rating: model.rating.toStringAsFixed(1),
      reviewCount: '0',
      isVerified: model.isVerified,
      isFurnished: model.isFurnished,
      isFavorite: model.isFav,
      isSaved: model.isSaved,
      metrics: [
        TenantPropertyMetricContent(
          icon: Icons.bed_outlined,
          value: '${model.bedrooms}',
          label: LocaleKeys.tenantSearchResultsBeds,
        ),
        TenantPropertyMetricContent(
          icon: Icons.shower_outlined,
          value: '${model.bathrooms}',
          label: LocaleKeys.tenantSearchResultsBaths,
        ),
        TenantPropertyMetricContent(
          icon: Icons.square_foot_outlined,
          value: '${model.area}',
          label: LocaleKeys.tenantSearchResultsSquareMeters,
        ),
        TenantPropertyMetricContent(
          icon: Icons.calendar_month_outlined,
          value: '${model.rentalPeriod}',
          label: LocaleKeys.tenantPropertyDetailsRentalMonths,
        ),
      ],
      description: model.description,
      amenities: model.amenityLabels,
      photoLabels: model.photoLabels,
      nearbyPlaces: const [],
      ownerName: model.owner,
      ownerId: model.ownerId,
      ownerMeta: model.isVerified
          ? LocaleKeys.tenantPropertyDetailsVerifiedOwner
          : LocaleKeys.tenantPropertyDetailsOwner,
      imageColors: const [AppColors.tealDark, AppColors.sokoonTeal],
      imageUrls: model.imageUrls,
      videoUrl: model.video,
      videoDuration: model.videoDuration,
      propertyLink: model.propertyLink,
      latitude: model.latitude,
      longitude: model.longitude,
    );
  }

  final String id;
  final String title;
  final String propertyType;
  final String location;
  final String price;
  final String rating;
  final String reviewCount;
  final bool isVerified;
  final bool isFurnished;
  final bool isFavorite;
  final bool isSaved;
  final List<TenantPropertyMetricContent> metrics;
  final String description;
  final List<String> amenities;
  final List<String> photoLabels;
  final List<TenantNearbyPlaceContent> nearbyPlaces;
  final String ownerName;
  final String ownerId;
  final String ownerMeta;
  final List<Color> imageColors;
  final List<String> imageUrls;
  final String latitude;
  final String longitude;
  final String? videoUrl;
  final int? videoDuration;
  final String propertyLink;

  String get shortTitle => title;
  String get shareUrl {
    final Uri? uri = Uri.tryParse(propertyLink.trim());
    if (uri != null &&
        (uri.scheme == 'https' || uri.scheme == 'http') &&
        uri.host.isNotEmpty) {
      return uri.toString();
    }
    return 'https://sokoun.app/properties/${Uri.encodeComponent(id)}';
  }
}

class TenantFilterFormState {
  const TenantFilterFormState({
    required this.propertyTypes,
    required this.city,
    required this.district,
    required this.minPrice,
    required this.maxPrice,
    required this.rooms,
    required this.bathrooms,
    required this.rentalTerm,
    required this.tenantType,
    required this.smoking,
    required this.amenities,
    required this.verifiedOnly,
    required this.ownershipVerifiedOnly,
  });

  factory TenantFilterFormState.initial({
    String query = '',
    Set<String> selectedFilters = const {},
  }) {
    final selectedPropertyTypes = selectedFilters
        .where(TenantPropertyFilterOptions.propertyTypes.contains)
        .toSet();
    final selectedAmenities = selectedFilters
        .where(TenantPropertyFilterOptions.amenities.contains)
        .toSet();

    return TenantFilterFormState(
      propertyTypes: selectedPropertyTypes,
      city: query.contains('القاهرة') ? 'القاهرة' : '',
      district: _firstMatching(
        selectedFilters,
        TenantPropertyFilterOptions.districts,
      ),
      minPrice: '',
      maxPrice: '',
      rooms: selectedFilters.contains('3 غرف') ? '3' : 'الكل',
      bathrooms: 'الكل',
      rentalTerm: _firstMatching(
        selectedFilters,
        TenantPropertyFilterOptions.rentalTerms,
        fallback: 'الكل',
      ),
      tenantType: _firstMatching(
        selectedFilters,
        TenantPropertyFilterOptions.tenantTypes,
        fallback: 'الكل',
      ),
      smoking: selectedFilters.contains('ممنوع التدخين')
          ? 'ممنوع'
          : selectedFilters.contains('مسموح التدخين')
          ? 'مسموح'
          : 'الكل',
      amenities: selectedAmenities,
      verifiedOnly: selectedFilters.contains('موثّق'),
      ownershipVerifiedOnly: selectedFilters.contains('إثبات ملكية'),
    );
  }

  final Set<String> propertyTypes;
  final String city;
  final String district;
  final String minPrice;
  final String maxPrice;
  final String rooms;
  final String bathrooms;
  final String rentalTerm;
  final String tenantType;
  final String smoking;
  final Set<String> amenities;
  final bool verifiedOnly;
  final bool ownershipVerifiedOnly;

  int get activeCount {
    return propertyTypes.length +
        (city.trim().isEmpty ? 0 : 1) +
        (district.trim().isEmpty ? 0 : 1) +
        (minPrice.trim().isEmpty ? 0 : 1) +
        (maxPrice.trim().isEmpty ? 0 : 1) +
        (rooms == 'الكل' ? 0 : 1) +
        (bathrooms == 'الكل' ? 0 : 1) +
        (rentalTerm == 'الكل' ? 0 : 1) +
        (tenantType == 'الكل' ? 0 : 1) +
        (smoking == 'الكل' ? 0 : 1) +
        amenities.length +
        (verifiedOnly ? 1 : 0) +
        (ownershipVerifiedOnly ? 1 : 0);
  }

  String get query {
    return [
      district,
      city,
    ].where((value) => value.trim().isNotEmpty).join('، ');
  }

  Set<String> get selectedFilters {
    return {
      ...propertyTypes,
      if (district.trim().isNotEmpty) district.trim(),
      if (minPrice.trim().isNotEmpty) 'من ${minPrice.trim()}',
      if (maxPrice.trim().isNotEmpty) 'إلى ${maxPrice.trim()}',
      if (rooms != 'الكل') '$rooms غرف',
      if (bathrooms != 'الكل') '$bathrooms حمام',
      if (rentalTerm != 'الكل') rentalTerm,
      if (tenantType != 'الكل') tenantType,
      if (smoking == 'ممنوع') 'ممنوع التدخين',
      if (smoking == 'مسموح') 'مسموح التدخين',
      ...amenities,
      if (verifiedOnly) 'موثّق',
      if (ownershipVerifiedOnly) 'إثبات ملكية',
    };
  }

  static String _firstMatching(
    Set<String> selectedFilters,
    List<String> options, {
    String fallback = '',
  }) {
    for (final option in options) {
      if (selectedFilters.contains(option)) {
        return option;
      }
    }
    return fallback;
  }

  TenantFilterFormState copyWith({
    Set<String>? propertyTypes,
    String? city,
    String? district,
    String? minPrice,
    String? maxPrice,
    String? rooms,
    String? bathrooms,
    String? rentalTerm,
    String? tenantType,
    String? smoking,
    Set<String>? amenities,
    bool? verifiedOnly,
    bool? ownershipVerifiedOnly,
  }) {
    return TenantFilterFormState(
      propertyTypes: propertyTypes ?? this.propertyTypes,
      city: city ?? this.city,
      district: district ?? this.district,
      minPrice: minPrice ?? this.minPrice,
      maxPrice: maxPrice ?? this.maxPrice,
      rooms: rooms ?? this.rooms,
      bathrooms: bathrooms ?? this.bathrooms,
      rentalTerm: rentalTerm ?? this.rentalTerm,
      tenantType: tenantType ?? this.tenantType,
      smoking: smoking ?? this.smoking,
      amenities: amenities ?? this.amenities,
      verifiedOnly: verifiedOnly ?? this.verifiedOnly,
      ownershipVerifiedOnly:
          ownershipVerifiedOnly ?? this.ownershipVerifiedOnly,
    );
  }
}

abstract final class TenantPropertyFilterOptions {
  static const propertyTypes = [
    'شقة',
    'ستوديو',
    'غرفة',
    'دوبلكس',
    'فيلا',
    'روف',
  ];
  static const districts = [
    'مدينة نصر',
    'التجمع الخامس',
    'مصر الجديدة',
    'الشيخ زايد',
    'المهندسين',
    'الزمالك',
  ];
  static const rooms = ['الكل', '1', '2', '3', '4+'];
  static const bathrooms = ['الكل', '1', '2', '3+'];
  static const rentalTerms = ['الكل', '3 شهور', '6 شهور', 'سنة'];
  static const tenantTypes = ['الكل', 'عائلات', 'فردي', 'بنات فقط', 'ولاد فقط'];
  static const smokingOptions = ['الكل', 'مسموح', 'ممنوع', 'حسب الاتفاق'];
  static const amenities = [
    'واي فاي',
    'أسانسير',
    'جراج',
    'أمن',
    'بلكونة',
    'تكييف',
    'مفروش',
    'قريب من المترو',
    'غاز طبيعي',
    'عداد كهرباء',
    'عداد مياه',
  ];
}
