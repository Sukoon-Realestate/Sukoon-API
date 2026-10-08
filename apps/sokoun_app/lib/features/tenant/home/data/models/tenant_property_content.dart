import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/finance/data/egyptian_pound.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_price_period.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';

import 'property_details_model.dart';
import '../rental_property_gallery_data.dart';

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
    this.selection,
    this.hasRentalOffers = false,
    this.selectionConfirmed = false,
    this.propertyTitle = '',
    this.propertyDescription = '',
    this.galleryHasGeneralPhotos = false,
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
    this.ownerAvatar = '',
    this.ownerPhone = '',
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

  factory TenantPropertyDetailsContent.fromModel(
    PropertyDetailsModel model, {
    RentalSelection? selection,
    bool selectionConfirmed = false,
  }) {
    final inventory = model.rentalInventory;
    final offer = inventory?.offerById(selection?.offerId ?? '');
    final gallery = RentalPropertyGallery.fromProperty(
      model,
      selection: selection,
    );
    final hasOffers = model.hasRentalOffers || selection != null;
    return TenantPropertyDetailsContent(
      selection: selection,
      selectionConfirmed: selectionConfirmed,
      hasRentalOffers: hasOffers,
      propertyTitle: model.title,
      propertyDescription: model.description,
      galleryHasGeneralPhotos: gallery.hasGeneralPhotos,
      id: model.id,
      title: selection == null
          ? model.title
          : selection.name.isNotEmpty
          ? selection.name
          : selection.scope?.label ?? LocaleKeys.rentalUnknownScope,
      propertyType: model.propertyTypeLabel,
      location: model.locationLabel,
      price: selection == null
          ? (hasOffers ? '' : model.formattedPrice)
          : EgyptianPound.formatAmount(selection.terms.price),
      rating: model.rating.toStringAsFixed(1),
      isVerified: model.isVerified,
      isOwnerVerified: model.isOwnerVerified,
      isOwnershipVerified: model.isOwnershipVerified,
      isFurnished: model.isFurnished,
      isFavorite: model.isFav,
      isSaved: offer?.isSaved ?? model.isSaved,
      metrics: [
        if (model.bedrooms > 0)
          TenantPropertyMetricContent(
            icon: Icons.bed_outlined,
            value: '${model.bedrooms}',
            label: !hasOffers
                ? LocaleKeys.tenantSearchResultsBeds
                : LocaleKeys.rentalPropertyRooms,
          ),
        if (model.bathrooms > 0)
          TenantPropertyMetricContent(
            icon: Icons.shower_outlined,
            value: '${model.bathrooms}',
            label: hasOffers
                ? LocaleKeys.rentalParentPropertyBathrooms
                : LocaleKeys.tenantSearchResultsBaths,
          ),
        if (model.area > 0 || (!hasOffers && model.space.isNotEmpty))
          TenantPropertyMetricContent(
            icon: Icons.square_foot_outlined,
            value: model.area > 0 ? '${model.area}' : model.space,
            label: hasOffers
                ? LocaleKeys.rentalParentPropertyArea
                : LocaleKeys.tenantSearchResultsSquareMeters,
          ),
        if (!hasOffers)
          TenantPropertyMetricContent(
            icon: Icons.calendar_month_outlined,
            value: '${model.rentalPeriod}',
            label: model.rentalPeriodUnitLabel,
          ),
      ],
      description:
          selection?.terms.description ?? (hasOffers ? '' : model.description),
      amenities: model.amenityLabels,
      photoLabels: gallery.images.indexed
          .map(
            (entry) => [
              if (hasOffers)
                switch (gallery.contexts[entry.$1]) {
                  RentalPhotoContext.accommodation =>
                    LocaleKeys.rentalOfferPhotos,
                  RentalPhotoContext.parentRoom =>
                    LocaleKeys.rentalParentRoomPhotos,
                  RentalPhotoContext.shared => LocaleKeys.rentalSharedPhotos,
                  RentalPhotoContext.property =>
                    LocaleKeys.rentalPropertyPhotos,
                },
              if (entry.$2.name.isEmpty)
                LocaleKeys.tenantPropertyDetailsPhotoCountUnit
              else
                entry.$2.name,
            ].join(' · '),
          )
          .toList(),
      photoDescriptions: gallery.images
          .map((image) => image.description)
          .toList(growable: false),
      floor: model.floor,
      suitableFor:
          selection?.terms.suitableFor ?? (hasOffers ? '' : model.suitableFor),
      smokingAllowed:
          selection?.terms.smokingAllowed ??
          (hasOffers ? null : model.smokingAllowed),
      buildingYear: model.buildingYear,
      deposit: selection?.terms.deposit ?? (hasOffers ? '' : model.deposit),
      ownerName: model.owner,
      ownerAvatar: model.ownerAvatar,
      ownerPhone: model.revealedOwnerPhone,
      ownerId: model.ownerId,
      ownerMeta: model.isOwnerVerified
          ? LocaleKeys.tenantPropertyDetailsVerifiedOwner
          : LocaleKeys.tenantPropertyDetailsOwner,
      imageColors: const [AppColors.tealDark, AppColors.sokoonTeal],
      imageUrls: gallery.images.map((image) => image.image).toList(),
      videoUrl: model.video,
      videoDuration: model.videoDuration,
      propertyLink: model.propertyLink,
      pricePeriodLabel: selection == null
          ? (hasOffers ? '' : model.pricePeriodLabel)
          : (PropertyPricePeriod.fromValue(
                  selection.terms.pricePeriod,
                )?.label ??
                selection.terms.pricePeriod),
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

  final RentalSelection? selection;
  final bool hasRentalOffers;
  final bool selectionConfirmed, galleryHasGeneralPhotos;
  final String propertyTitle, propertyDescription;
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
  final String ownerAvatar;
  final String ownerPhone;
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
    final selected = selection;
    final candidate = selected?.offerLink.isNotEmpty == true
        ? selected!.offerLink
        : propertyLink;
    final Uri? uri = Uri.tryParse(candidate.trim());
    if (uri != null &&
        (uri.scheme == 'https' || uri.scheme == 'http') &&
        uri.host.isNotEmpty) {
      return selected != null &&
              selected.offerId.isNotEmpty &&
              selected.offerLink.isEmpty
          ? uri
                .replace(
                  queryParameters: {
                    ...uri.queryParameters,
                    'offer_id': selected.offerId,
                  },
                )
                .toString()
          : uri.toString();
    }
    return 'https://sokoun.app/properties/${Uri.encodeComponent(id)}'
        '${selected?.offerId.isNotEmpty == true ? '/offers/${Uri.encodeComponent(selected!.offerId)}' : ''}';
  }
}
