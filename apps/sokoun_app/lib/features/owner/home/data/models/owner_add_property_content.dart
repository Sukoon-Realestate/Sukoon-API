import 'dart:io';
import 'dart:convert';
import 'property_location.dart';

import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:sokoun_app/features/shared/finance/data/egyptian_pound.dart';

class AddPropertyChipContent {
  const AddPropertyChipContent({
    required this.label,
    this.isSelected = false,
    this.value,
  });

  final String label;
  final bool isSelected;
  final String? value;
  String get selectionValue => value ?? label;
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

  static const minimumPhotoCount = Validators.propertyMinPhotoCount;
  static const maxPhotoCount = Validators.propertyMaxPhotoCount;

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
    LocaleKeys.ownerAddPropertyElectricityMeter,
    LocaleKeys.ownerAddPropertyWaterMeter,
  ];

  static List<String> get suitableForOptions => [
    LocaleKeys.ownerAddPropertyEveryone,
    LocaleKeys.ownerAddPropertyMalesOnly,
    LocaleKeys.ownerAddPropertyFemalesOnly,
    LocaleKeys.ownerAddPropertyFamilies,
    LocaleKeys.ownerAddPropertyIndividuals,
    LocaleKeys.ownerAddPropertyShared,
  ];

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
  bool get canRemove => true;
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
    this.location,
    required this.photoDrafts,
    required this.monthlyPrice,
    required this.rentalDuration,
    required this.rentalUnit,
    required this.amenities,
    required this.description,
    required this.suitableFor,
    this.submittedAt,
    this.optionLabels = const {},
    this.videoFile,
    this.videoUrl = '',
    this.videoDuration,
    this.removeVideo = false,
    this.isVideoPreparing = false,
    this.country = '',
    this.neighborhood = '',
    this.buildingYear = '',
    this.deposit = '',
    this.smokingAllowed,
    this.ownershipProofFile,
    this.ownershipProofUrl = '',
    this.removeOwnershipProof = false,
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
      location: null,
      photoDrafts: [],
      monthlyPrice: '',
      rentalDuration: '',
      rentalUnit: '',
      amenities: {},
      description: '',
      suitableFor: '',
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
  final PropertyLocation? location;
  bool get isLocationSelected => location?.isValid == true;
  final List<OwnerPropertyPhotoDraft> photoDrafts;
  final String monthlyPrice;
  final String rentalDuration;
  final String rentalUnit;
  final Set<String> amenities;
  final String description;
  final String suitableFor;
  final DateTime? submittedAt;
  final Map<String, String> optionLabels;
  final File? videoFile;
  final String videoUrl;
  final int? videoDuration;
  final bool removeVideo;
  final bool isVideoPreparing;
  final String country;
  final String neighborhood;
  final String buildingYear;
  final String deposit;
  final bool? smokingAllowed;
  final File? ownershipProofFile;
  final String ownershipProofUrl;
  final bool removeOwnershipProof;
  bool get hasVideo => videoFile != null || videoUrl.trim().isNotEmpty;
  bool get hasOwnershipProof =>
      ownershipProofFile != null || ownershipProofUrl.trim().isNotEmpty;
  bool get isBuildingYearReady =>
      (buildingYear.trim().isEmpty ||
      (int.tryParse(buildingYear) != null &&
          int.parse(buildingYear) >= 1800 &&
          int.parse(buildingYear) <= DateTime.now().year));
  bool get isDepositReady =>
      (deposit.trim().isEmpty ||
      {'none', 'half_month', 'one_month', 'two_months'}.contains(deposit) ||
      (num.tryParse(deposit) != null && num.parse(deposit) >= 0));
  bool get isAdditionalDetailsReady => isBuildingYearReady && isDepositReady;
  String get rentalUnitLabel =>
      optionLabels['price_period:$rentalUnitApiValue'] ?? rentalUnit;
  String get suitableForLabel =>
      optionLabels['suitable_for:$suitableForApiValue'] ?? suitableFor;
  List<String> get amenityLabels => optionLabels.isEmpty
      ? amenities.toList(growable: false)
      : amenityApiValues
            .map((value) => optionLabels['amenity:$value'] ?? value)
            .toList(growable: false);

  int get photoCount => photoDrafts.length;
  List<String> get existingPhotoUrls => photoDrafts
      .where((photo) => photo.isExisting)
      .map((photo) => photo.existingUrl)
      .toList(growable: false);
  List<File> get photos => photoDrafts
      .map((photo) => photo.file)
      .whereType<File>()
      .toList(growable: false);
  bool get isBasicsReady => Validators.isValidPropertyBasics(
    requiredFields: [
      title,
      propertyType,
      governorateId,
      governorate,
      districtId,
      district,
      street,
    ],
    positiveNumbers: [bedrooms, bathrooms, space],
    floor: floor,
    hasValidLocation: isLocationSelected,
  );

  bool get isPhotosReady =>
      Validators.isValidPropertyPhotos(count: photoCount) &&
      photoDrafts.every((photo) => photo.file != null || photo.isExisting) &&
      !isVideoPreparing &&
      (videoFile == null ||
          (videoDuration != null &&
              Validators.validatePropertyVideoDuration(
                    Duration(seconds: videoDuration!),
                  ) ==
                  null));

  bool get isPricingReady =>
      Validators.isValidPropertyPricing(
        monthlyPrice: monthlyPrice,
        rentalDuration: rentalDuration,
        rentalUnit: rentalUnit,
        suitableFor: suitableFor,
        description: description,
      ) &&
      isAdditionalDetailsReady;

  String get locationSummary => '$district، $governorate';

  String get priceSummary {
    final price = EgyptianPound.formatAmount(
      monthlyPrice.trim().isEmpty ? '0' : monthlyPrice,
    );
    return LocaleKeys.ownerAddPropertyMonthlyPrice.replaceAll('{price}', price);
  }

  String get photoSummary => LocaleKeys.ownerAddPropertyPhotoCountSummary
      .replaceAll('{count}', '$photoCount');

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
      AddPropertySummaryContent(
        label: LocaleKeys.ownerPropertyVideoTitle,
        value: hasVideo
            ? LocaleKeys.ownerPropertyVideoSelected
            : LocaleKeys.ownerAddPropertyVideoSkipped,
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
    PropertyLocation? location,
    bool clearLocation = false,
    List<OwnerPropertyPhotoDraft>? photoDrafts,
    String? monthlyPrice,
    String? rentalDuration,
    String? rentalUnit,
    Set<String>? amenities,
    String? description,
    String? suitableFor,
    DateTime? submittedAt,
    Map<String, String>? optionLabels,
    File? videoFile,
    String? videoUrl,
    int? videoDuration,
    bool? removeVideo,
    bool? isVideoPreparing,
    bool clearVideo = false,
    String? country,
    String? neighborhood,
    String? buildingYear,
    String? deposit,
    bool? smokingAllowed,
    bool clearSmokingAllowed = false,
    File? ownershipProofFile,
    String? ownershipProofUrl,
    bool? removeOwnershipProof,
    bool clearOwnershipProof = false,
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
      location: clearLocation ? null : location ?? this.location,
      photoDrafts: photoDrafts ?? this.photoDrafts,
      monthlyPrice: monthlyPrice ?? this.monthlyPrice,
      rentalDuration: rentalDuration ?? this.rentalDuration,
      rentalUnit: rentalUnit ?? this.rentalUnit,
      amenities: amenities ?? this.amenities,
      description: description ?? this.description,
      suitableFor: suitableFor ?? this.suitableFor,
      submittedAt: submittedAt ?? this.submittedAt,
      optionLabels: optionLabels ?? this.optionLabels,
      videoFile: clearVideo ? null : videoFile ?? this.videoFile,
      videoUrl: clearVideo ? '' : videoUrl ?? this.videoUrl,
      videoDuration: clearVideo ? null : videoDuration ?? this.videoDuration,
      removeVideo: removeVideo ?? this.removeVideo,
      isVideoPreparing: isVideoPreparing ?? this.isVideoPreparing,
      country: country ?? this.country,
      neighborhood: neighborhood ?? this.neighborhood,
      buildingYear: buildingYear ?? this.buildingYear,
      deposit: deposit ?? this.deposit,
      smokingAllowed: clearSmokingAllowed
          ? null
          : smokingAllowed ?? this.smokingAllowed,
      ownershipProofFile: clearOwnershipProof
          ? null
          : ownershipProofFile ?? this.ownershipProofFile,
      ownershipProofUrl: clearOwnershipProof
          ? ''
          : ownershipProofUrl ?? this.ownershipProofUrl,
      removeOwnershipProof: removeOwnershipProof ?? this.removeOwnershipProof,
    );
  }

  Map<String, dynamic> toJson({
    bool includeMainImage = true,
    bool isEditing = false,
  }) {
    final Set<String> selectedAmenities = amenities;
    final OwnerPropertyPhotoDraft? mainPhoto = photoDrafts.firstOrNull;
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
      'district': isEditing || neighborhood.trim().isNotEmpty
          ? neighborhood.trim()
          : street.trim(),
      'street': street.trim(),
      'country': country.trim(),
      'building_year': buildingYear.trim(),
      'deposit': deposit.trim(),
      'smoking_allowed': smokingAllowed ?? '',
      if (location?.isValid == true) ...{
        'latitude': location!.latitude,
        'longitude': location!.longitude,
      },
      if (includeMainImage && mainPhoto?.file != null)
        'main_image': mainPhoto!.file,
      if (mainPhoto != null) ...{
        'main_image_name': mainPhoto.name.trim(),
        'main_image_description': mainPhoto.description.trim(),
        if (mainPhoto.isExisting && mainPhoto.existingId.isNotEmpty)
          'main_image_id': mainPhoto.existingId,
      },
      if (isEditing) ...{
        'retained_image_ids': jsonEncode([
          for (final photo in photoDrafts)
            if (photo.isExisting && photo.existingId.isNotEmpty)
              photo.existingId,
        ]),
        'images_metadata': jsonEncode([
          for (final photo in photoDrafts)
            if (photo.isExisting && photo.existingId.isNotEmpty)
              {
                'id': photo.existingId,
                'name': photo.name.trim(),
                'description': photo.description.trim(),
              },
        ]),
      },
      if (videoFile != null) ...{
        'video': videoFile,
        if (videoDuration != null) 'video_duration': videoDuration,
      },
      if (removeVideo) 'remove_video': true,
      if (ownershipProofFile != null) 'ownership_proof': ownershipProofFile,
      if (removeOwnershipProof) 'remove_ownership_proof': true,
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
      'has_electricity_meter': amenityApiValues.contains('electricity_meter'),
      'has_water_meter': amenityApiValues.contains('water_meter'),
      'has_natural_gas': _containsOption(
        selectedAmenities,
        localized: LocaleKeys.ownerAddPropertyNaturalGas,
        apiValue: 'natural_gas',
        arabic: 'غاز طبيعي',
        english: 'Natural gas',
      ),
      'amenities': jsonEncode(
        amenityApiValues.where((value) => value != 'furnished').toList(),
      ),
    };
  }

  String get propertyTypeApiValue => propertyTypeValue.isNotEmpty
      ? propertyTypeValue
      : _propertyTypeValue(propertyType);

  String get rentalUnitApiValue => _rentalUnitValue(rentalUnit);
  String get suitableForApiValue => _suitableForValue(suitableFor);
  Set<String> get amenityApiValues {
    final Map<String, String> labels = {
      'furnished': LocaleKeys.ownerAddPropertyFurnished,
      'wifi': LocaleKeys.ownerAddPropertyWifi,
      'elevator': LocaleKeys.ownerAddPropertyElevator,
      'garage': LocaleKeys.ownerAddPropertyGarage,
      'security': LocaleKeys.ownerAddPropertySecurity,
      'balcony': LocaleKeys.ownerAddPropertyBalcony,
      'air_conditioning': LocaleKeys.ownerAddPropertyAirConditioning,
      'near_metro': LocaleKeys.ownerAddPropertyNearMetro,
      'natural_gas': LocaleKeys.ownerAddPropertyNaturalGas,
      'electricity_meter': LocaleKeys.ownerAddPropertyElectricityMeter,
      'water_meter': LocaleKeys.ownerAddPropertyWaterMeter,
    };
    const Map<String, String> aliases = {
      'مفروش': 'furnished',
      'Furnished': 'furnished',
      'واي فاي': 'wifi',
      'WiFi': 'wifi',
      'أسانسير': 'elevator',
      'Elevator': 'elevator',
      'جراج': 'garage',
      'Garage': 'garage',
      'أمن': 'security',
      'Security': 'security',
      'بلكونة': 'balcony',
      'Balcony': 'balcony',
      'تكييف': 'air_conditioning',
      'Air conditioning': 'air_conditioning',
      'قريب من المترو': 'near_metro',
      'Near the metro': 'near_metro',
      'غاز طبيعي': 'natural_gas',
      'Natural gas': 'natural_gas',
      'عداد كهرباء': 'electricity_meter',
      'Electricity meter': 'electricity_meter',
      'عداد مياه': 'water_meter',
      'Water meter': 'water_meter',
    };
    return {
      for (final value in amenities)
        labels.entries
                .where((entry) => entry.value == value)
                .firstOrNull
                ?.key ??
            aliases[value] ??
            value,
    };
  }

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
