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

class TenantPropertyDetailsContent {
  const TenantPropertyDetailsContent({
    required this.id,
    required this.title,
    required this.propertyType,
    required this.location,
    required this.price,
    required this.rating,
    required this.isVerified,
    this.isOwnerVerified = false,
    this.isOwnershipVerified = false,
    required this.isFurnished,
    required this.isFavorite,
    required this.isSaved,
    required this.metrics,
    required this.description,
    required this.amenities,
    required this.photoLabels,
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
    this.pricePeriodLabel = '',
    this.bedrooms,
    this.floor,
    this.suitableFor = '',
    this.smokingAllowed,
    this.buildingYear = 0,
    this.deposit = '',
    this.photoDescriptions = const [],
    this.country = '',
    this.cityName = '',
    this.governorateName = '',
    this.district = '',
    this.street = '',
    this.space = '',
    this.status = '',
    this.createdAt = '',
    this.updatedAt = '',
  });

  factory TenantPropertyDetailsContent.fromModel(PropertyDetailsModel model) {
    return TenantPropertyDetailsContent(
      id: model.id,
      title: model.title,
      propertyType: model.propertyTypeLabel,
      location: model.locationLabel,
      price: model.formattedPrice,
      rating: model.rating.toStringAsFixed(1),
      isVerified: model.isVerified,
      isOwnerVerified: model.isOwnerVerified,
      isOwnershipVerified: model.isOwnershipVerified,
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
          value: model.area > 0 ? '${model.area}' : model.space,
          label: LocaleKeys.tenantSearchResultsSquareMeters,
        ),
        TenantPropertyMetricContent(
          icon: Icons.calendar_month_outlined,
          value: '${model.rentalPeriod}',
          label: model.rentalPeriodUnitLabel,
        ),
      ],
      description: model.description,
      amenities: model.amenityLabels,
      photoLabels: model.photoLabels,
      photoDescriptions: model.galleryImages
          .map((image) => image.description)
          .toList(growable: false),
      floor: model.floor,
      suitableFor: model.suitableFor,
      smokingAllowed: model.smokingAllowed,
      buildingYear: model.buildingYear,
      deposit: model.deposit,
      ownerName: model.owner,
      ownerId: model.ownerId,
      ownerMeta: model.isOwnerVerified
          ? LocaleKeys.tenantPropertyDetailsVerifiedOwner
          : LocaleKeys.tenantPropertyDetailsOwner,
      imageColors: const [AppColors.tealDark, AppColors.sokoonTeal],
      imageUrls: model.imageUrls,
      videoUrl: model.video,
      videoDuration: model.videoDuration,
      propertyLink: model.propertyLink,
      pricePeriodLabel: model.pricePeriodLabel,
      bedrooms: model.bedrooms,
      latitude: model.latitude,
      longitude: model.longitude,
      country: model.country,
      cityName: model.city.name,
      governorateName: model.governorateName,
      district: model.district,
      street: model.street,
      space: model.space,
      status: model.status,
      createdAt: model.createdAt,
      updatedAt: model.updatedAt,
    );
  }

  final String id;
  final String title;
  final String propertyType;
  final String location;
  final String price;
  final String rating;
  final bool isVerified;
  final bool isOwnerVerified;
  final bool isOwnershipVerified;
  final bool isFurnished;
  final bool isFavorite;
  final bool isSaved;
  final List<TenantPropertyMetricContent> metrics;
  final String description;
  final List<String> amenities;
  final List<String> photoLabels;
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
  final String pricePeriodLabel;
  final int? bedrooms;
  final int? floor;
  final String suitableFor;
  final bool? smokingAllowed;
  final int buildingYear;
  final String deposit;
  final List<String> photoDescriptions;
  final String country;
  final String cityName;
  final String governorateName;
  final String district;
  final String street;
  final String space;
  final String status;
  final String createdAt;
  final String updatedAt;

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
