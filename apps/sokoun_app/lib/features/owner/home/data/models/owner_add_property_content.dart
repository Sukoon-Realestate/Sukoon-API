import 'dart:io';

import 'package:flutter/material.dart';
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
  static const propertyTypeOptions = [
    'شقة',
    'غرفة',
    'استوديو',
    'فيلا',
    'دور',
    'روف',
  ];

  static const photoTips = [
    'صوّر كل الغرف: صالة، غرف نوم، مطبخ، حمام',
    'استخدم إضاءة طبيعية',
    'تأكد من خلو الصور من أي أرقام هواتف أو معلومات شخصية',
    'الحد الأدنى 10 صور، وتقدر ترفع لحد 25 صورة',
  ];

  static const minimumPhotoCount = 10;
  static const maxPhotoCount = 25;

  static const depositOptions = ['بدون تأمين', 'نصف شهر', 'شهر واحد', 'شهرين'];

  static const rentalUnitOptions = ['يوم', 'أسبوع', 'شهر', 'سنة'];

  static const amenityOptions = [
    'واي فاي',
    'مفروش',
    'جراج',
    'أسانسير',
    'أمن',
    'بلكونة',
    'تكييف',
    'غاز طبيعي',
    'عداد كهرباء',
    'عداد مياه',
    'قريب من المترو',
  ];

  static const smokingOptionLabels = ['مسموح', 'ممنوع', 'حسب الاتفاق'];

  static const suitableForOptions = [
    'الكل',
    'ولاد فقط',
    'بنات فقط',
    'عائلات',
    'أفراد',
    'مشاركة',
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

class OwnerAddPropertyFormState {
  const OwnerAddPropertyFormState({
    required this.title,
    required this.propertyType,
    required this.governorate,
    required this.district,
    required this.street,
    required this.bedrooms,
    required this.bathrooms,
    required this.space,
    required this.floor,
    required this.buildingYear,
    required this.mapQuery,
    required this.isLocationSelected,
    required this.existingPhotoUrls,
    required this.photos,
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
      governorate: '',
      district: '',
      street: '',
      bedrooms: '',
      bathrooms: '',
      space: '',
      floor: '',
      buildingYear: '',
      mapQuery: '',
      isLocationSelected: false,
      existingPhotoUrls: [],
      photos: [],
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
  final String governorate;
  final String district;
  final String street;
  final String bedrooms;
  final String bathrooms;
  final String space;
  final String floor;
  final String buildingYear;
  final String mapQuery;
  final bool isLocationSelected;
  final List<String> existingPhotoUrls;
  final List<File> photos;
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

  int get photoCount => existingPhotoUrls.length + photos.length;
  bool get isProofUploaded =>
      ownershipProof != null || ownershipProofUrl.isNotEmpty;

  bool get isBasicsReady {
    return title.trim().isNotEmpty &&
        propertyType.trim().isNotEmpty &&
        governorate.trim().isNotEmpty &&
        district.trim().isNotEmpty &&
        street.trim().isNotEmpty &&
        _hasPositiveNumber(bedrooms) &&
        _hasPositiveNumber(bathrooms) &&
        _hasPositiveNumber(space) &&
        floor.trim().isNotEmpty &&
        _hasPositiveNumber(buildingYear) &&
        isLocationSelected;
  }

  bool get isPhotosReady =>
      photoCount >= OwnerAddPropertyContent.minimumPhotoCount;

  bool get isPricingReady {
    return _hasPositiveNumber(monthlyPrice) &&
        deposit.trim().isNotEmpty &&
        _hasPositiveNumber(rentalDuration) &&
        rentalUnit.trim().isNotEmpty &&
        amenities.isNotEmpty &&
        description.trim().length >= 10;
  }

  bool get isExtraDetailsReady {
    return smokingPolicy.trim().isNotEmpty &&
        suitableFor.trim().isNotEmpty &&
        isProofUploaded;
  }

  String get locationSummary => '$district، $governorate';

  String get priceSummary {
    final price = monthlyPrice.trim().isEmpty ? '0' : monthlyPrice.trim();
    return '$price ر.س/شهر';
  }

  String get photoSummary => '$photoCount صورة';

  String get videoSummary {
    final OwnerPropertyVideoSelection? selectedVideo = video;
    return selectedVideo == null
        ? 'تم تخطي الفيديو'
        : 'تم رفع الفيديو (${selectedVideo.formattedDuration})';
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
      AddPropertySummaryContent(label: 'نوع العقار', value: propertyType),
      AddPropertySummaryContent(label: 'المنطقة', value: locationSummary),
      AddPropertySummaryContent(label: 'السعر', value: priceSummary),
      AddPropertySummaryContent(label: 'الصور', value: photoSummary),
      AddPropertySummaryContent(label: 'الفيديو', value: videoSummary),
      AddPropertySummaryContent(label: 'إثبات الملكية', value: proofFileName),
      AddPropertySummaryContent(
        label: 'وقت الإرسال',
        value: _formatSubmittedAt(submittedAt ?? DateTime.now()),
      ),
    ];
  }

  OwnerAddPropertyFormState copyWith({
    String? title,
    String? propertyType,
    String? governorate,
    String? district,
    String? street,
    String? bedrooms,
    String? bathrooms,
    String? space,
    String? floor,
    String? buildingYear,
    String? mapQuery,
    bool? isLocationSelected,
    List<String>? existingPhotoUrls,
    List<File>? photos,
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
      governorate: governorate ?? this.governorate,
      district: district ?? this.district,
      street: street ?? this.street,
      bedrooms: bedrooms ?? this.bedrooms,
      bathrooms: bathrooms ?? this.bathrooms,
      space: space ?? this.space,
      floor: floor ?? this.floor,
      buildingYear: buildingYear ?? this.buildingYear,
      mapQuery: mapQuery ?? this.mapQuery,
      isLocationSelected: isLocationSelected ?? this.isLocationSelected,
      existingPhotoUrls: existingPhotoUrls ?? this.existingPhotoUrls,
      photos: photos ?? this.photos,
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

  Map<String, dynamic> toRequestBody() {
    final Set<String> selectedAmenities = amenities;
    return {
      'title': title.trim(),
      'description': description.trim(),
      'price': monthlyPrice.trim(),
      'price_period': _rentalUnitValue(rentalUnit),
      'property_type': _propertyTypeValue(propertyType),
      'is_furnished': selectedAmenities.contains('مفروش'),
      'bedrooms': int.parse(bedrooms),
      'bathrooms': int.parse(bathrooms),
      'area': int.parse(space),
      'space': space.trim(),
      'floor': int.parse(floor),
      'rental_period': int.parse(rentalDuration),
      'suitable_for': _suitableForValue(suitableFor),
      'smoking_allowed': smokingPolicy == 'مسموح',
      'country': 'Egypt',
      'city': governorate,
      'district': district,
      'street': street.trim(),
      'building_year': int.parse(buildingYear),
      'deposit': _depositValue(deposit),
      'location': mapQuery.trim(),
      'has_wifi': selectedAmenities.contains('واي فاي'),
      'has_elevator': selectedAmenities.contains('أسانسير'),
      'has_garage': selectedAmenities.contains('جراج'),
      'has_security': selectedAmenities.contains('أمن'),
      'has_balcony': selectedAmenities.contains('بلكونة'),
      'has_air_conditioning': selectedAmenities.contains('تكييف'),
      'near_metro': selectedAmenities.contains('قريب من المترو'),
      'has_natural_gas': selectedAmenities.contains('غاز طبيعي'),
      'has_electricity_meter': selectedAmenities.contains('عداد كهرباء'),
      'has_water_meter': selectedAmenities.contains('عداد مياه'),
      if (photos.isNotEmpty) 'main_image': photos.first,
      if (photos.length > 1) 'images': photos.skip(1).toList(growable: false),
      if (video != null) 'video': video!.file,
      if (video != null) 'video_duration': video!.duration.inSeconds,
      if (ownershipProof != null) 'ownership_proof': ownershipProof,
    };
  }

  static String _propertyTypeValue(String value) {
    return const {
          'شقة': 'apartment',
          'غرفة': 'room',
          'استوديو': 'studio',
          'فيلا': 'villa',
          'دور': 'floor',
          'روف': 'roof',
        }[value] ??
        value;
  }

  static String _rentalUnitValue(String value) {
    return const {
          'يوم': 'daily',
          'أسبوع': 'weekly',
          'شهر': 'monthly',
          'سنة': 'yearly',
        }[value] ??
        value;
  }

  static String _suitableForValue(String value) {
    return const {
          'الكل': 'all',
          'ولاد فقط': 'males_only',
          'بنات فقط': 'females_only',
          'عائلات': 'families',
          'أفراد': 'individuals',
          'مشاركة': 'shared',
        }[value] ??
        value;
  }

  static String _depositValue(String value) {
    return const {
          'بدون تأمين': 'none',
          'نصف شهر': 'half_month',
          'شهر واحد': 'one_month',
          'شهرين': 'two_months',
        }[value] ??
        value;
  }

  static bool _hasPositiveNumber(String value) {
    final parsed = num.tryParse(value.trim());
    return parsed != null && parsed > 0;
  }

  static String _formatSubmittedAt(DateTime value) {
    final hour12 = value.hour % 12 == 0 ? 12 : value.hour % 12;
    final minute = value.minute.toString().padLeft(2, '0');
    final suffix = value.hour >= 12 ? 'م' : 'ص';
    return 'اليوم $hour12:$minute $suffix';
  }
}
