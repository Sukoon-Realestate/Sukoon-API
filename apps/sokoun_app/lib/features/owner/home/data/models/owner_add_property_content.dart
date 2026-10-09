import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_inventory.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_terms.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_offer.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_accommodation_draft_details.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_scope.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_inventory_validation.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'dart:io';
import 'dart:convert';
import 'property_location.dart';
import '../enums/property_tenant_type.dart';
import '../enums/property_price_period.dart';

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

  static List<String> get rentalUnitOptions =>
      PropertyPricePeriod.values.map((period) => period.label).toList();

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

  static List<String> get suitableForOptions =>
      PropertyTenantType.values.map((type) => type.label).toList();

  static const supportedAmenityValues = {
    'wifi',
    'elevator',
    'garage',
    'security',
    'balcony',
    'air_conditioning',
    'near_metro',
    'natural_gas',
    'electricity_meter',
    'water_meter',
    'furnished',
  };

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
    this.contentFingerprint = '',
    this.draftKey = '',
    this.needsReselection = false,
  });

  final File? file;
  final String existingId;
  final String existingUrl;
  final String name;
  final String description;

  /// Local-only checksum; never part of the property API body.
  final String contentFingerprint;
  final String draftKey;
  final bool needsReselection;
  String get reference => draftKey.isNotEmpty ? draftKey : id;

  bool get isExisting => existingUrl.trim().isNotEmpty;
  bool get canRemove => true;
  String get id => isExisting
      ? (existingId.isNotEmpty ? existingId : existingUrl)
      : file?.path ?? '';
  String get uniquenessKey => contentFingerprint.isNotEmpty
      ? 'sha256:$contentFingerprint'
      : isExisting
      ? 'url:$existingUrl'
      : 'path:${file?.path ?? ''}';

  OwnerPropertyPhotoDraft copyWith({
    File? file,
    String? existingId,
    String? existingUrl,
    String? name,
    String? description,
    String? contentFingerprint,
    String? draftKey,
    bool? needsReselection,
  }) {
    return OwnerPropertyPhotoDraft(
      file: file ?? this.file,
      existingId: existingId ?? this.existingId,
      existingUrl: existingUrl ?? this.existingUrl,
      name: name ?? this.name,
      description: description ?? this.description,
      contentFingerprint: contentFingerprint ?? this.contentFingerprint,
      draftKey: draftKey ?? this.draftKey,
      needsReselection: needsReselection ?? this.needsReselection,
    );
  }
}

class OwnerAddPropertyFormState {
  const OwnerAddPropertyFormState({
    this.rentalInventory,
    this.selectedOfferRef = '',
    this.submissionKey = '',
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
    this.areaDescription = '',
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
      country: 'Egypt',
    );
  }

  final RentalInventory? rentalInventory;
  final String selectedOfferRef;
  RentalOffer? get selectedOffer => selectedOfferRef.isEmpty
      ? rentalInventory?.offers.firstOrNull
      : rentalInventory?.offers
            .where((offer) => offer.reference == selectedOfferRef)
            .firstOrNull;
  RentalScope? get rentalScope => selectedOffer?.scope;
  bool canSaveToServer([
    RentalOfferCapabilities capabilities = RentalOfferCapabilities.configured,
  ]) =>
      !needsOfferCapability ||
      (capabilities.canWrite &&
          submissionInventory?.hasLocalOnlyDetails != true);
  final String submissionKey;
  bool get isPartialOffering => rentalInventory?.isPartial == true;
  bool get needsOfferCapability => rentalInventory != null;
  RentalInventory? get submissionInventory {
    final inventory = rentalInventory;
    if (inventory == null) return null;
    if (inventory.isPartial) {
      final refs = inventory.offers.expand((offer) => offer.roomRefs).toSet();
      final bedRooms = inventory.offers
          .where((offer) => offer.scope == RentalScope.bed)
          .expand((offer) => offer.roomRefs)
          .toSet();
      final bedRefs = inventory.offers
          .where((offer) => offer.scope == RentalScope.bed)
          .map((offer) => offer.bedRef)
          .toSet();
      return inventory.copyWith(
        offers: [
          for (final offer in inventory.offers)
            offer.scope == RentalScope.roomGroup
                ? offer
                : offer.copyWith(draftDetails: const RentalOfferDraftDetails()),
        ],
        rooms: [
          for (final room in inventory.rooms)
            if (room.id.isNotEmpty || refs.contains(room.reference))
              room.copyWith(
                draftDetails: refs.contains(room.reference)
                    ? room.draftDetails
                    : const RentalRoomDraftDetails(),
                beds: [
                  for (final bed in room.beds)
                    if (bed.id.isNotEmpty ||
                        bedRefs.contains(bed.reference) ||
                        (bedRooms.contains(room.reference) &&
                            bed.name.trim().isNotEmpty))
                      bed.copyWith(
                        draftDetails: bedRefs.contains(bed.reference)
                            ? bed.draftDetails
                            : const RentalBedDraftDetails(),
                      ),
                ],
              ),
        ],
      );
    }
    return inventory.copyWith(
      // Hidden partial drafts remain recoverable but cannot block whole mode.
      // Existing room identities remain in edits to retain their dependencies.
      draftDetails: const RentalSharedDraftDetails(),
      rooms: [
        for (final room in inventory.rooms)
          if (room.id.isNotEmpty)
            room.copyWith(
              draftDetails: const RentalRoomDraftDetails(),
              beds: [
                for (final bed in room.beds)
                  if (bed.id.isNotEmpty)
                    bed.copyWith(draftDetails: const RentalBedDraftDetails()),
              ],
            ),
      ],
      offers: [
        for (final offer in inventory.offers)
          offer.copyWith(
            draftDetails: const RentalOfferDraftDetails(),
            inheritedFields: const {},
            terms: RentalTerms(
              price: monthlyPrice,
              pricePeriod: rentalUnitApiValue,
              minimumMonths: int.tryParse(rentalDuration) ?? 0,
              deposit: deposit,
              suitableFor: suitableForApiValue,
              description: description,
              smokingAllowed: smokingAllowed,
              rules: offer.terms.rules,
            ),
          ),
      ],
    );
  }

  bool get isInventoryReady =>
      rentalInventory == null ||
      RentalInventoryValidation.validate(
        submissionInventory!,
        totalBedrooms: (int.tryParse(bedrooms) ?? 0) > 0
            ? int.parse(bedrooms)
            : null,
      ).isEmpty;

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
  final String areaDescription;
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
  bool get isDepositReady {
    if (deposit.trim().isEmpty ||
        {'none', 'half_month', 'one_month', 'two_months'}.contains(deposit)) {
      return true;
    }
    final amount = num.tryParse(deposit);
    return amount != null && amount.isFinite && amount >= 0;
  }

  bool get isAdditionalDetailsReady =>
      isBuildingYearReady &&
      (isPartialOffering || isDepositReady) &&
      !(ownershipProofFile != null && removeOwnershipProof);
  String get rentalUnitLabel =>
      optionLabels['price_period:$rentalUnitApiValue'] ??
      PropertyPricePeriod.fromValue(rentalUnitApiValue)?.label ??
      rentalUnit;
  String get suitableForLabel =>
      optionLabels['suitable_for:$suitableForApiValue'] ??
      PropertyTenantType.fromValue(suitableForApiValue)?.label ??
      suitableFor;
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
  bool get isAccommodationReady =>
      rentalInventory == null ||
      (selectedOffer != null &&
          RentalInventoryValidation.validate(
            submissionInventory!,
            totalBedrooms: (int.tryParse(bedrooms) ?? 0) > 0
                ? int.parse(bedrooms)
                : null,
            includeTerms: false,
          ).isEmpty);
  bool get isBasicsReady =>
      (rentalInventory == null ||
          (isPartialOffering
              ? submissionInventory!.offers.every(
                  (offer) =>
                      submissionInventory!
                          .resolved(offer)
                          .terms
                          .description
                          .trim()
                          .length >=
                      10,
                )
              : Validators.hasMinimumLength(description, 10))) &&
      isAccommodationReady &&
      Validators.isValidPropertyBasics(
        requiredFields: [
          title,
          propertyType,
          governorateId,
          governorate,
          districtId,
          district,
          street,
        ],
        positiveNumbers: isPartialOffering
            ? const []
            : [bedrooms, bathrooms, space],
        floor: floor,
        hasValidLocation: isLocationSelected,
      );

  bool get isVideoReady =>
      hasVideo &&
      !isVideoPreparing &&
      !removeVideo &&
      ((videoFile == null && videoDuration == null) ||
          Validators.validatePropertyVideoDuration(
                Duration(seconds: videoDuration ?? 0),
              ) ==
              null);

  bool get hasDuplicatePhotos =>
      photoDrafts.map((photo) => photo.id).toSet().length != photoCount ||
      photoDrafts.map((photo) => photo.uniquenessKey).toSet().length !=
          photoCount;

  bool get isPhotosReady =>
      Validators.isValidPropertyPhotos(count: photoCount) &&
      !hasDuplicatePhotos &&
      photoDrafts.every(
        (photo) =>
            !photo.needsReselection && (photo.file != null || photo.isExisting),
      ) &&
      isVideoReady;

  bool get isPricingReady =>
      (isPartialOffering
          ? isInventoryReady
          : Validators.isValidPropertyPricing(
                  monthlyPrice: monthlyPrice,
                  rentalDuration: rentalDuration,
                  rentalUnit: rentalUnit,
                  suitableFor: suitableFor,
                  description: description,
                ) &&
                PropertyTenantType.fromValue(suitableForApiValue) != null &&
                PropertyPricePeriod.fromValue(rentalUnitApiValue) != null) &&
      isInventoryReady &&
      unsupportedAmenities.isEmpty &&
      isAdditionalDetailsReady;

  String get locationSummary => '$district، $governorate';

  String get priceSummary {
    final price = EgyptianPound.formatAmount(
      monthlyPrice.trim().isEmpty ? '0' : monthlyPrice,
    );
    return LocaleKeys.ownerAddPropertyPriceSummary
        .replaceAll('{price}', price)
        .replaceAll('{unit}', rentalUnitLabel);
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
      if (rentalInventory == null)
        AddPropertySummaryContent(
          label: LocaleKeys.ownerAddPropertyPrice,
          value: priceSummary,
        )
      else
        for (final offer in submissionInventory!.offers)
          AddPropertySummaryContent(
            label: offer.name.isEmpty
                ? offer.scope?.label ?? LocaleKeys.rentalUnknownScope
                : offer.name,
            value: [
              EgyptianPound.formatAmount(
                submissionInventory!.resolved(offer).terms.price,
              ),
              PropertyPricePeriod.fromValue(
                    submissionInventory!.resolved(offer).terms.pricePeriod,
                  )?.label ??
                  '',
              offer.scope?.priceBasis ?? LocaleKeys.rentalUnknownScope,
            ].join(' · '),
          ),
      AddPropertySummaryContent(
        label: LocaleKeys.ownerAddPropertyPhotosSummary,
        value: photoSummary,
      ),
      AddPropertySummaryContent(
        label: LocaleKeys.ownerPropertyVideoTitle,
        value: hasVideo
            ? LocaleKeys.ownerPropertyVideoSelected
            : LocaleKeys.ownerPropertyVideoRequired,
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
    RentalInventory? rentalInventory,
    String? selectedOfferRef,
    bool clearRentalInventory = false,
    String? submissionKey,
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
    String? areaDescription,
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
      rentalInventory: clearRentalInventory
          ? null
          : rentalInventory ?? this.rentalInventory,
      selectedOfferRef: clearRentalInventory
          ? ''
          : selectedOfferRef ?? this.selectedOfferRef,
      submissionKey: submissionKey ?? this.submissionKey,
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
      areaDescription: areaDescription ?? this.areaDescription,
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
    RentalOfferCapabilities capabilities = RentalOfferCapabilities.configured,
  }) {
    if (!canSaveToServer(capabilities)) {
      throw StateError('Rental offer persistence is unavailable');
    }
    if (rentalInventory != null && !isInventoryReady) {
      throw StateError('Invalid rental inventory');
    }
    final Set<String> selectedAmenities = amenities;
    final OwnerPropertyPhotoDraft? mainPhoto = photoDrafts.firstOrNull;
    return {
      'title': title.trim(),
      if (!isPartialOffering) ...{
        'description': description.trim(),
        'price': monthlyPrice.trim(),
        'price_period': _rentalUnitValue(rentalUnit),
      },
      if (rentalInventory != null)
        'rental_inventory': jsonEncode(
          submissionInventory!.toRequestJson(
            includeMedia: capabilities.canAssociateMedia,
          ),
        ),
      'property_type': propertyTypeApiValue,
      'is_furnished': _containsOption(
        selectedAmenities,
        localized: LocaleKeys.ownerAddPropertyFurnished,
        apiValue: 'furnished',
        arabic: 'مفروش',
        english: 'Furnished',
      ),
      if (!isPartialOffering || (int.tryParse(bedrooms) ?? 0) > 0)
        'bedrooms': int.parse(bedrooms),
      if (!isPartialOffering || (int.tryParse(bathrooms) ?? 0) > 0)
        'bathrooms': int.parse(bathrooms),
      if (!isPartialOffering || (int.tryParse(space) ?? 0) > 0)
        'area': int.parse(space),
      'space': areaDescription.trim(),
      'floor': floor.trim().isEmpty ? '' : int.parse(floor),
      if (!isPartialOffering) ...{
        'rental_period': int.parse(rentalDuration),
        'suitable_for': _suitableForValue(suitableFor),
      },
      'governorate': governorateId,
      'city': districtId,
      'district': isEditing || neighborhood.trim().isNotEmpty
          ? neighborhood.trim()
          : street.trim(),
      'street': street.trim(),
      'country': country.trim(),
      'building_year': buildingYear.trim(),
      if (!isPartialOffering) ...{
        'deposit': deposit.trim(),
        'smoking_allowed': smokingAllowed ?? '',
      },
      if (location?.isValid == true) ...{
        'latitude': location!.latitude.toStringAsFixed(6),
        'longitude': location!.longitude.toStringAsFixed(6),
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
  Set<String> get unsupportedAmenities => amenityApiValues.difference(
    OwnerAddPropertyContent.supportedAmenityValues,
  );
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
    final PropertyTenantType? type = PropertyTenantType.values
        .where((type) => type.value == value || type.label == value)
        .firstOrNull;
    if (type != null) return type.value;
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
          'Students': 'students',
          'طلاب': 'students',
          'Female students': 'female_students',
          'طالبات': 'female_students',
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
