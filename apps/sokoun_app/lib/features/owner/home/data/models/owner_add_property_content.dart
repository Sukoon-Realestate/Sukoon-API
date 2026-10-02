import 'dart:io';
import 'property_location.dart';

import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';

class AddPropertyChipContent {
  const AddPropertyChipContent({required this.label, this.isSelected = false});

  final String label;
  final bool isSelected;
}

class AddPropertyFieldContent {
  const AddPropertyFieldContent({
    required this.label,
    required this.value,
    this.isFocused = false,
    this.textAlign = TextAlign.start,
  });

  final String label;
  final String value;
  final bool isFocused;
  final TextAlign textAlign;
}

class AddPropertySummaryContent {
  const AddPropertySummaryContent({required this.label, required this.value});

  final String label;
  final String value;
}

abstract final class OwnerAddPropertyContent {
  static List<String> get photoTips => [
    LocaleKeys.ownerAddPropertyPhotoTipRooms,
    LocaleKeys.ownerAddPropertyPhotoTipLighting,
    LocaleKeys.ownerAddPropertyPhotoTipPrivacy,
    LocaleKeys.ownerAddPropertyPhotoTipLimits,
  ];

  static const minimumPhotoCount = 10;
  static const maxPhotoCount = 25;

  static List<String> get depositOptions => [
    LocaleKeys.ownerAddPropertyNoDeposit,
    LocaleKeys.ownerAddPropertyHalfMonth,
    LocaleKeys.ownerAddPropertyOneMonth,
    LocaleKeys.ownerAddPropertyTwoMonths,
  ];

  static List<String> get rentalUnitOptions => [
    LocaleKeys.ownerAddPropertyDay,
    LocaleKeys.ownerAddPropertyMonth,
    LocaleKeys.ownerAddPropertyYear,
  ];

  static List<String> get amenityOptions => [
    LocaleKeys.ownerAddPropertyWifi,
    LocaleKeys.ownerAddPropertyFurnished,
    LocaleKeys.ownerAddPropertyGarage,
    LocaleKeys.ownerAddPropertyElevator,
    LocaleKeys.ownerAddPropertySecurity,
    LocaleKeys.ownerAddPropertyBalcony,
    LocaleKeys.ownerAddPropertyAirConditioning,
    LocaleKeys.ownerAddPropertyNaturalGas,
    LocaleKeys.ownerAddPropertyNearMetro,
  ];

  static List<String> get smokingOptionLabels => [
    LocaleKeys.ownerAddPropertyAllowed,
    LocaleKeys.ownerAddPropertyNotAllowed,
    LocaleKeys.ownerAddPropertyByAgreement,
  ];

  static List<String> get suitableForOptions => [
    LocaleKeys.ownerAddPropertyEveryone,
    LocaleKeys.ownerAddPropertyMalesOnly,
    LocaleKeys.ownerAddPropertyFemalesOnly,
    LocaleKeys.ownerAddPropertyFamilies,
    LocaleKeys.ownerAddPropertyIndividuals,
    LocaleKeys.ownerAddPropertyShared,
  ];

  static const tealSoft = AppColors.tealAlpha07;
  static const tealBorder = AppColors.tealAlpha19;

  static List<AddPropertyChipContent> singleSelectedChips({
    required List<String> labels,
    required String selectedValue,
  }) {
    return labels
        .map(
          (label) => AddPropertyChipContent(
            label: label,
            isSelected: label == selectedValue,
          ),
        )
        .toList();
  }

  static List<AddPropertyChipContent> multiSelectedChips({
    required List<String> labels,
    required Set<String> selectedValues,
  }) {
    return labels
        .map(
          (label) => AddPropertyChipContent(
            label: label,
            isSelected: selectedValues.contains(label),
          ),
        )
        .toList();
  }
}

class OwnerPropertyVideoSelection {
  const OwnerPropertyVideoSelection({
    required this.file,
    required this.duration,
  });

  final File file;
  final Duration duration;

  String get formattedDuration {
    final String minutes = duration.inMinutes.toString().padLeft(2, '0');
    final String seconds = (duration.inSeconds % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }
}

class OwnerPropertyPhotoDraft {
  const OwnerPropertyPhotoDraft({
    this.file,
    this.existingId = '',
    this.existingUrl = '',
    this.name = '',
    this.description = '',
  });

  final File? file;
  final String existingId;
  final String existingUrl;
  final String name;
  final String description;

  bool get isExisting => existingUrl.trim().isNotEmpty;
  bool get canRemove => !isExisting;
  bool get isMetadataReady =>
      isExisting || (name.trim().isNotEmpty && description.trim().isNotEmpty);
  String get id => isExisting
      ? (existingId.isNotEmpty ? existingId : existingUrl)
      : file?.path ?? '';

  OwnerPropertyPhotoDraft copyWith({
    File? file,
    String? existingId,
    String? existingUrl,
    String? name,
    String? description,
  }) {
    return OwnerPropertyPhotoDraft(
      file: file ?? this.file,
      existingId: existingId ?? this.existingId,
      existingUrl: existingUrl ?? this.existingUrl,
      name: name ?? this.name,
      description: description ?? this.description,
    );
  }
}

class OwnerAddPropertyFormState {
  const OwnerAddPropertyFormState({
    required this.title,
    required this.propertyType,
    this.propertyTypeValue = '',
    required this.governorateId,
    required this.governorate,
    required this.districtId,
    required this.district,
    required this.street,
    required this.bedrooms,
    required this.bathrooms,
    required this.space,
    required this.floor,
    required this.buildingYear,
    required this.mapQuery,
    this.location,
    required this.photoDrafts,
    required this.video,
    required this.monthlyPrice,
    required this.deposit,
    required this.rentalDuration,
    required this.rentalUnit,
    required this.amenities,
    required this.description,
    required this.smokingPolicy,
    required this.suitableFor,
    required this.ownershipProofUrl,
    required this.ownershipProof,
    this.submittedAt,
  });

  factory OwnerAddPropertyFormState.initial() {
    return const OwnerAddPropertyFormState(
      title: '',
      propertyType: '',
      governorateId: '',
      governorate: '',
      districtId: '',
      district: '',
      street: '',
      bedrooms: '',
      bathrooms: '',
      space: '',
      floor: '',
      buildingYear: '',
      mapQuery: '',
      location: null,
      photoDrafts: [],
      video: null,
      monthlyPrice: '',
      deposit: '',
      rentalDuration: '',
      rentalUnit: '',
      amenities: {},
      description: '',
      smokingPolicy: '',
      suitableFor: '',
      ownershipProofUrl: '',
      ownershipProof: null,
    );
  }

  final String title;
  final String propertyType;
  final String propertyTypeValue;
  final String governorateId;
  final String governorate;
  final String districtId;
  final String district;
  final String street;
  final String bedrooms;
  final String bathrooms;
  final String space;
  final String floor;
  final String buildingYear;
  final String mapQuery;
  final PropertyLocation? location;
  bool get isLocationSelected => location?.isValid == true;
  final List<OwnerPropertyPhotoDraft> photoDrafts;
  final OwnerPropertyVideoSelection? video;
  final String monthlyPrice;
  final String deposit;
  final String rentalDuration;
  final String rentalUnit;
  final Set<String> amenities;
  final String description;
  final String smokingPolicy;
  final String suitableFor;
  final String ownershipProofUrl;
  final File? ownershipProof;
  final DateTime? submittedAt;

  int get photoCount => photoDrafts.length;
  List<String> get existingPhotoUrls => photoDrafts
      .where((photo) => photo.isExisting)
      .map((photo) => photo.existingUrl)
      .toList(growable: false);
  List<File> get photos => photoDrafts
      .map((photo) => photo.file)
      .whereType<File>()
      .toList(growable: false);
  bool get isProofUploaded =>
      ownershipProof != null || ownershipProofUrl.isNotEmpty;

  bool get isBasicsReady {
    return title.trim().isNotEmpty &&
        propertyType.trim().isNotEmpty &&
        governorateId.trim().isNotEmpty &&
        governorate.trim().isNotEmpty &&
        districtId.trim().isNotEmpty &&
        district.trim().isNotEmpty &&
        street.trim().isNotEmpty &&
        _hasPositiveNumber(bedrooms) &&
        _hasPositiveNumber(bathrooms) &&
        _hasPositiveNumber(space) &&
        int.tryParse(floor) != null &&
        isLocationSelected;
  }

  bool get isPhotosReady =>
      photoCount >= OwnerAddPropertyContent.minimumPhotoCount &&
      photoDrafts.every((photo) => photo.isMetadataReady);

  bool get isPricingReady {
    return _hasPositiveNumber(monthlyPrice) &&
        _hasPositiveNumber(rentalDuration) &&
        rentalUnit.trim().isNotEmpty &&
        suitableFor.trim().isNotEmpty &&
        description.trim().length >= 10;
  }

  bool get isExtraDetailsReady {
    return suitableFor.trim().isNotEmpty;
  }

  String get locationSummary => '$district، $governorate';

  String get priceSummary {
    final price = monthlyPrice.trim().isEmpty ? '0' : monthlyPrice.trim();
    return LocaleKeys.ownerAddPropertyMonthlyPrice.replaceAll('{price}', price);
  }

  String get photoSummary => LocaleKeys.ownerAddPropertyPhotoCountSummary
      .replaceAll('{count}', '$photoCount');

  String get videoSummary {
    final OwnerPropertyVideoSelection? selectedVideo = video;
    return selectedVideo == null
        ? LocaleKeys.ownerAddPropertyVideoSkipped
        : LocaleKeys.ownerAddPropertyVideoUploadedSummary.replaceAll(
            '{duration}',
            selectedVideo.formattedDuration,
          );
  }

  String get proofFileName {
    final File? proof = ownershipProof;
    if (proof != null && proof.uri.pathSegments.isNotEmpty) {
      return proof.uri.pathSegments.last;
    }
    final Uri? existingProof = Uri.tryParse(ownershipProofUrl);
    if (existingProof == null || existingProof.pathSegments.isEmpty) {
      return ownershipProofUrl;
    }
    return existingProof.pathSegments.last;
  }

  List<AddPropertySummaryContent> get submittedSummary {
    return [
      AddPropertySummaryContent(
        label: LocaleKeys.ownerAddPropertyType,
        value: propertyType,
      ),
      AddPropertySummaryContent(
        label: LocaleKeys.ownerAddPropertyAreaSummary,
        value: locationSummary,
      ),
      AddPropertySummaryContent(
        label: LocaleKeys.ownerAddPropertyPrice,
        value: priceSummary,
      ),
      AddPropertySummaryContent(
        label: LocaleKeys.ownerAddPropertyPhotosSummary,
        value: photoSummary,
      ),
      for (int index = 0; index < photoDrafts.length; index++)
        if (photoDrafts[index].name.trim().isNotEmpty ||
            photoDrafts[index].description.trim().isNotEmpty)
          AddPropertySummaryContent(
            label:
                '${LocaleKeys.ownerAddPropertyPhotoNumber.replaceAll('{number}', '${index + 1}')} '
                '${photoDrafts[index].name.trim()}',
            value: photoDrafts[index].description.trim(),
          ),
      AddPropertySummaryContent(
        label: LocaleKeys.ownerAddPropertySubmittedAtSummary,
        value: _formatSubmittedAt(submittedAt ?? DateTime.now()),
      ),
    ];
  }

  OwnerAddPropertyFormState copyWith({
    String? title,
    String? propertyType,
    String? propertyTypeValue,
    String? governorateId,
    String? governorate,
    String? districtId,
    String? district,
    String? street,
    String? bedrooms,
    String? bathrooms,
    String? space,
    String? floor,
    String? buildingYear,
    String? mapQuery,
    PropertyLocation? location,
    bool clearLocation = false,
    List<OwnerPropertyPhotoDraft>? photoDrafts,
    OwnerPropertyVideoSelection? video,
    bool clearVideo = false,
    String? monthlyPrice,
    String? deposit,
    String? rentalDuration,
    String? rentalUnit,
    Set<String>? amenities,
    String? description,
    String? smokingPolicy,
    String? suitableFor,
    String? ownershipProofUrl,
    File? ownershipProof,
    bool clearOwnershipProof = false,
    DateTime? submittedAt,
  }) {
    return OwnerAddPropertyFormState(
      title: title ?? this.title,
      propertyType: propertyType ?? this.propertyType,
      propertyTypeValue: propertyTypeValue ?? this.propertyTypeValue,
      governorateId: governorateId ?? this.governorateId,
      governorate: governorate ?? this.governorate,
      districtId: districtId ?? this.districtId,
      district: district ?? this.district,
      street: street ?? this.street,
      bedrooms: bedrooms ?? this.bedrooms,
      bathrooms: bathrooms ?? this.bathrooms,
      space: space ?? this.space,
      floor: floor ?? this.floor,
      buildingYear: buildingYear ?? this.buildingYear,
      mapQuery: mapQuery ?? this.mapQuery,
      location: clearLocation ? null : location ?? this.location,
      photoDrafts: photoDrafts ?? this.photoDrafts,
      video: clearVideo ? null : video ?? this.video,
      monthlyPrice: monthlyPrice ?? this.monthlyPrice,
      deposit: deposit ?? this.deposit,
      rentalDuration: rentalDuration ?? this.rentalDuration,
      rentalUnit: rentalUnit ?? this.rentalUnit,
      amenities: amenities ?? this.amenities,
      description: description ?? this.description,
      smokingPolicy: smokingPolicy ?? this.smokingPolicy,
      suitableFor: suitableFor ?? this.suitableFor,
      ownershipProofUrl: clearOwnershipProof
          ? ''
          : ownershipProofUrl ?? this.ownershipProofUrl,
      ownershipProof: clearOwnershipProof
          ? null
          : ownershipProof ?? this.ownershipProof,
      submittedAt: submittedAt ?? this.submittedAt,
    );
  }

  Map<String, dynamic> toRequestBody() => toJson();

  Map<String, dynamic> toJson({bool includeMainImage = true}) {
    final Set<String> selectedAmenities = amenities;
    return {
      'title': title.trim(),
      'description': description.trim(),
      'price': monthlyPrice.trim(),
      'price_period': _rentalUnitValue(rentalUnit),
      'property_type': propertyTypeApiValue,
      'is_furnished': _containsOption(
        selectedAmenities,
        localized: LocaleKeys.ownerAddPropertyFurnished,
        apiValue: 'furnished',
        arabic: 'مفروش',
        english: 'Furnished',
      ),
      'bedrooms': int.parse(bedrooms),
      'bathrooms': int.parse(bathrooms),
      'area': int.parse(space),
      'space': space.trim(),
      'floor': int.parse(floor),
      'rental_period': int.parse(rentalDuration),
      'suitable_for': _suitableForValue(suitableFor),
      'governorate': governorateId,
      'city': districtId,
      'district': street.trim(),
      if (location?.isValid == true) ...{
        'latitude': location!.latitude,
        'longitude': location!.longitude,
      },
      if (includeMainImage && photos.isNotEmpty) 'main_image': photos.first,
      'has_wifi': _containsOption(
        selectedAmenities,
        localized: LocaleKeys.ownerAddPropertyWifi,
        apiValue: 'wifi',
        arabic: 'واي فاي',
        english: 'WiFi',
      ),
      'has_elevator': _containsOption(
        selectedAmenities,
        localized: LocaleKeys.ownerAddPropertyElevator,
        apiValue: 'elevator',
        arabic: 'أسانسير',
        english: 'Elevator',
      ),
      'has_garage': _containsOption(
        selectedAmenities,
        localized: LocaleKeys.ownerAddPropertyGarage,
        apiValue: 'garage',
        arabic: 'جراج',
        english: 'Garage',
      ),
      'has_security': _containsOption(
        selectedAmenities,
        localized: LocaleKeys.ownerAddPropertySecurity,
        apiValue: 'security',
        arabic: 'أمن',
        english: 'Security',
      ),
      'has_balcony': _containsOption(
        selectedAmenities,
        localized: LocaleKeys.ownerAddPropertyBalcony,
        apiValue: 'balcony',
        arabic: 'بلكونة',
        english: 'Balcony',
      ),
      'has_air_conditioning': _containsOption(
        selectedAmenities,
        localized: LocaleKeys.ownerAddPropertyAirConditioning,
        apiValue: 'air_conditioning',
        arabic: 'تكييف',
        english: 'Air conditioning',
      ),
      'near_metro': _containsOption(
        selectedAmenities,
        localized: LocaleKeys.ownerAddPropertyNearMetro,
        apiValue: 'near_metro',
        arabic: 'قريب من المترو',
        english: 'Near the metro',
      ),
      'has_natural_gas': _containsOption(
        selectedAmenities,
        localized: LocaleKeys.ownerAddPropertyNaturalGas,
        apiValue: 'natural_gas',
        arabic: 'غاز طبيعي',
        english: 'Natural gas',
      ),
    };
  }

  String get propertyTypeApiValue => propertyTypeValue.isNotEmpty
      ? propertyTypeValue
      : _propertyTypeValue(propertyType);

  static String _propertyTypeValue(String value) {
    return {
          'apartment': 'apartment',
          'Apartment': 'apartment',
          'شقة': 'apartment',
          LocaleKeys.ownerAddPropertyApartment: 'apartment',
          'room': 'room',
          'Room': 'room',
          'غرفة': 'room',
          LocaleKeys.ownerAddPropertyRoom: 'room',
          'studio': 'studio',
          'Studio': 'studio',
          'استوديو': 'studio',
          LocaleKeys.ownerAddPropertyStudio: 'studio',
          'villa': 'villa',
          'Villa': 'villa',
          'فيلا': 'villa',
          LocaleKeys.ownerAddPropertyVilla: 'villa',
          'floor': 'floor',
          'Whole floor': 'floor',
          'دور': 'floor',
          LocaleKeys.ownerAddPropertyWholeFloor: 'floor',
          'roof': 'roof',
          'Roof': 'roof',
          'روف': 'roof',
          LocaleKeys.ownerAddPropertyRoof: 'roof',
        }[value] ??
        value;
  }

  static String _rentalUnitValue(String value) {
    return {
          'daily': 'daily',
          'Day': 'daily',
          'يوم': 'daily',
          LocaleKeys.ownerAddPropertyDay: 'daily',
          'weekly': 'weekly',
          'Week': 'weekly',
          'أسبوع': 'weekly',
          LocaleKeys.ownerAddPropertyWeek: 'weekly',
          'monthly': 'monthly',
          'Month': 'monthly',
          'شهر': 'monthly',
          LocaleKeys.ownerAddPropertyMonth: 'monthly',
          'yearly': 'yearly',
          'Year': 'yearly',
          'سنة': 'yearly',
          LocaleKeys.ownerAddPropertyYear: 'yearly',
        }[value] ??
        value;
  }

  static String _suitableForValue(String value) {
    return {
          'all': 'all',
          'Everyone': 'all',
          'الكل': 'all',
          LocaleKeys.ownerAddPropertyEveryone: 'all',
          'males_only': 'males_only',
          'Males only': 'males_only',
          'ولاد فقط': 'males_only',
          LocaleKeys.ownerAddPropertyMalesOnly: 'males_only',
          'females_only': 'females_only',
          'Females only': 'females_only',
          'بنات فقط': 'females_only',
          LocaleKeys.ownerAddPropertyFemalesOnly: 'females_only',
          'families': 'families',
          'Families': 'families',
          'عائلات': 'families',
          LocaleKeys.ownerAddPropertyFamilies: 'families',
          'individuals': 'singles',
          'Individuals': 'singles',
          'أفراد': 'singles',
          LocaleKeys.ownerAddPropertyIndividuals: 'singles',
          'shared': 'shared',
          'Shared': 'shared',
          'مشاركة': 'shared',
          LocaleKeys.ownerAddPropertyShared: 'shared',
        }[value] ??
        value;
  }

  static bool _hasPositiveNumber(String value) {
    final parsed = num.tryParse(value.trim());
    return parsed != null && parsed > 0;
  }

  static bool _containsOption(
    Set<String> values, {
    required String localized,
    required String apiValue,
    required String arabic,
    required String english,
  }) {
    return values.any(
      (value) => _matchesOption(
        value,
        localized: localized,
        apiValue: apiValue,
        arabic: arabic,
        english: english,
      ),
    );
  }

  static bool _matchesOption(
    String value, {
    required String localized,
    required String apiValue,
    required String arabic,
    required String english,
  }) {
    return value == localized ||
        value == apiValue ||
        value == arabic ||
        value == english;
  }

  static String _formatSubmittedAt(DateTime value) {
    final hour12 = value.hour % 12 == 0 ? 12 : value.hour % 12;
    final minute = value.minute.toString().padLeft(2, '0');
    final suffix = value.hour >= 12
        ? LocaleKeys.ownerAddPropertyPm
        : LocaleKeys.ownerAddPropertyAm;
    return LocaleKeys.ownerAddPropertyTodayAt
        .replaceAll('{time}', '$hour12:$minute')
        .replaceAll('{period}', suffix);
  }
}
