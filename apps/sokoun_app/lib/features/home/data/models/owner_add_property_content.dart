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

  static const governorateOptions = [
    'القاهرة',
    'الجيزة',
    'الإسكندرية',
    'الدقهلية',
  ];

  static const districtOptionsByGovernorate = {
    'القاهرة': ['مدينة نصر', 'التجمع الخامس', 'المعادي', 'مصر الجديدة'],
    'الجيزة': ['الدقي', 'المهندسين', '6 أكتوبر', 'الشيخ زايد'],
    'الإسكندرية': ['سموحة', 'سيدي جابر', 'ميامي', 'العجمي'],
    'الدقهلية': ['المنصورة', 'طلخا', 'ميت غمر', 'السنبلاوين'],
  };

  static const propertyTypes = [
    AddPropertyChipContent(label: 'شقة', isSelected: true),
    AddPropertyChipContent(label: 'غرفة'),
    AddPropertyChipContent(label: 'استوديو'),
    AddPropertyChipContent(label: 'فيلا'),
    AddPropertyChipContent(label: 'دور'),
    AddPropertyChipContent(label: 'روف'),
  ];

  static const addressFields = [
    AddPropertyFieldContent(label: 'المحافظة', value: 'القاهرة'),
    AddPropertyFieldContent(label: 'المنطقة', value: 'مدينة نصر'),
    AddPropertyFieldContent(label: 'الشارع', value: 'شارع النصر'),
  ];

  static const detailFields = [
    AddPropertyFieldContent(
      label: 'عدد الغرف',
      value: '3',
      textAlign: TextAlign.center,
    ),
    AddPropertyFieldContent(
      label: 'المساحة (م²)',
      value: '90',
      textAlign: TextAlign.center,
    ),
    AddPropertyFieldContent(
      label: 'الدور',
      value: '3',
      textAlign: TextAlign.center,
    ),
    AddPropertyFieldContent(
      label: 'سنة البناء',
      value: '2020',
      textAlign: TextAlign.center,
    ),
  ];

  static const photoTips = [
    'صوّر كل الغرف: صالة، غرف نوم، مطبخ، حمام',
    'استخدم إضاءة طبيعية',
    'تأكد من خلو الصور من أي أرقام هواتف أو معلومات شخصية',
    'الحد الأدنى 10 صور، الأفضل 15-20',
  ];

  static const minimumPhotoCount = 10;
  static const maxPhotoCount = 12;

  static const depositOptions = ['بدون تأمين', 'نصف شهر', 'شهر واحد', 'شهرين'];

  static const rentalUnitOptions = ['يوم', 'أسبوع', 'شهر', 'سنة'];

  static const pricingFields = [
    AddPropertyFieldContent(
      label: 'السعر',
      value: '2500',
      isFocused: true,
      textAlign: TextAlign.right,
    ),
    AddPropertyFieldContent(label: 'تأمين الشقة', value: 'شهر واحد'),
  ];

  static const amenityOptions = [
    'واي فاي',
    'مكيف',
    'غسالة',
    'ثلاجة',
    'مفروش',
    'بوتوجاز',
    'جراج',
    'أسانسير',
    'حارس',
    'بلكونة',
    'تكييف',
    'غاز طبيعي',
    'عداد كهرباء',
    'عداد مياه',
    'قريب من المترو',
  ];

  static const amenities = [
    AddPropertyChipContent(label: 'واي فاي', isSelected: true),
    AddPropertyChipContent(label: 'مكيف', isSelected: true),
    AddPropertyChipContent(label: 'غسالة', isSelected: true),
    AddPropertyChipContent(label: 'ثلاجة', isSelected: true),
    AddPropertyChipContent(label: 'مفروش', isSelected: true),
    AddPropertyChipContent(label: 'بوتوجاز'),
    AddPropertyChipContent(label: 'جراج'),
    AddPropertyChipContent(label: 'أسانسير'),
    AddPropertyChipContent(label: 'حارس'),
    AddPropertyChipContent(label: 'بلكونة'),
    AddPropertyChipContent(label: 'تكييف'),
    AddPropertyChipContent(label: 'غاز طبيعي'),
    AddPropertyChipContent(label: 'عداد كهرباء'),
    AddPropertyChipContent(label: 'عداد مياه'),
    AddPropertyChipContent(label: 'قريب من المترو'),
  ];

  static const smokingOptionLabels = ['مسموح', 'ممنوع', 'حسب الاتفاق'];

  static const smokingOptions = [
    AddPropertyChipContent(label: 'مسموح'),
    AddPropertyChipContent(label: 'ممنوع', isSelected: true),
    AddPropertyChipContent(label: 'حسب الاتفاق'),
  ];

  static const suitableForOptions = [
    'الكل',
    'ولاد فقط',
    'بنات فقط',
    'عائلات',
    'أفراد',
    'مشاركة',
  ];

  static const suitableFor = [
    AddPropertyChipContent(label: 'الكل'),
    AddPropertyChipContent(label: 'ولاد فقط'),
    AddPropertyChipContent(label: 'بنات فقط'),
    AddPropertyChipContent(label: 'عائلات', isSelected: true),
    AddPropertyChipContent(label: 'أفراد'),
    AddPropertyChipContent(label: 'مشاركة'),
  ];

  static const proofStates = [
    AddPropertyChipContent(label: 'فارغ', isSelected: true),
    AddPropertyChipContent(label: 'يرفع'),
    AddPropertyChipContent(label: 'مرفوع'),
    AddPropertyChipContent(label: 'خطأ'),
  ];

  static const submittedSummary = [
    AddPropertySummaryContent(label: 'نوع العقار', value: 'شقة مفروشة'),
    AddPropertySummaryContent(label: 'المنطقة', value: 'مدينة نصر، القاهرة'),
    AddPropertySummaryContent(label: 'السعر', value: '6,500 ج/شهر'),
    AddPropertySummaryContent(label: 'الصور', value: '12 صورة'),
    AddPropertySummaryContent(label: 'وقت الإرسال', value: 'النهارده 10:30 ص'),
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

class OwnerAddPropertyFormState {
  const OwnerAddPropertyFormState({
    required this.propertyType,
    required this.governorate,
    required this.district,
    required this.street,
    required this.bedrooms,
    required this.space,
    required this.floor,
    required this.buildingYear,
    required this.mapQuery,
    required this.isLocationSelected,
    required this.photoCount,
    required this.monthlyPrice,
    required this.deposit,
    required this.rentalDuration,
    required this.rentalUnit,
    required this.amenities,
    required this.description,
    required this.smokingPolicy,
    required this.suitableFor,
    required this.proofStatus,
    this.submittedAt,
  });

  factory OwnerAddPropertyFormState.initial() {
    return const OwnerAddPropertyFormState(
      propertyType: 'شقة',
      governorate: 'القاهرة',
      district: 'مدينة نصر',
      street: 'شارع النصر',
      bedrooms: '3',
      space: '90',
      floor: '3',
      buildingYear: '2020',
      mapQuery: 'مدينة نصر، القاهرة',
      isLocationSelected: true,
      photoCount: 4,
      monthlyPrice: '6500',
      deposit: 'شهر واحد',
      rentalDuration: '6',
      rentalUnit: 'شهر',
      amenities: {'واي فاي', 'مكيف', 'غسالة', 'ثلاجة', 'مفروش'},
      description:
          'شقة مفروشة بالكامل قريبة من الخدمات والمواصلات، مناسبة للإيجار الشهري.',
      smokingPolicy: 'ممنوع',
      suitableFor: 'عائلات',
      proofStatus: 'فارغ',
    );
  }

  final String propertyType;
  final String governorate;
  final String district;
  final String street;
  final String bedrooms;
  final String space;
  final String floor;
  final String buildingYear;
  final String mapQuery;
  final bool isLocationSelected;
  final int photoCount;
  final String monthlyPrice;
  final String deposit;
  final String rentalDuration;
  final String rentalUnit;
  final Set<String> amenities;
  final String description;
  final String smokingPolicy;
  final String suitableFor;
  final String proofStatus;
  final DateTime? submittedAt;

  bool get isProofUploaded => proofStatus == 'مرفوع';

  bool get isBasicsReady {
    return propertyType.trim().isNotEmpty &&
        governorate.trim().isNotEmpty &&
        district.trim().isNotEmpty &&
        street.trim().isNotEmpty &&
        _hasPositiveNumber(bedrooms) &&
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

  String get proofFileName => 'ownership-proof-${district.hashCode.abs()}.pdf';

  List<AddPropertySummaryContent> get submittedSummary {
    return [
      AddPropertySummaryContent(label: 'نوع العقار', value: propertyType),
      AddPropertySummaryContent(label: 'المنطقة', value: locationSummary),
      AddPropertySummaryContent(label: 'السعر', value: priceSummary),
      AddPropertySummaryContent(label: 'الصور', value: photoSummary),
      AddPropertySummaryContent(label: 'إثبات الملكية', value: proofStatus),
      AddPropertySummaryContent(
        label: 'وقت الإرسال',
        value: _formatSubmittedAt(submittedAt ?? DateTime.now()),
      ),
    ];
  }

  OwnerAddPropertyFormState copyWith({
    String? propertyType,
    String? governorate,
    String? district,
    String? street,
    String? bedrooms,
    String? space,
    String? floor,
    String? buildingYear,
    String? mapQuery,
    bool? isLocationSelected,
    int? photoCount,
    String? monthlyPrice,
    String? deposit,
    String? rentalDuration,
    String? rentalUnit,
    Set<String>? amenities,
    String? description,
    String? smokingPolicy,
    String? suitableFor,
    String? proofStatus,
    DateTime? submittedAt,
  }) {
    return OwnerAddPropertyFormState(
      propertyType: propertyType ?? this.propertyType,
      governorate: governorate ?? this.governorate,
      district: district ?? this.district,
      street: street ?? this.street,
      bedrooms: bedrooms ?? this.bedrooms,
      space: space ?? this.space,
      floor: floor ?? this.floor,
      buildingYear: buildingYear ?? this.buildingYear,
      mapQuery: mapQuery ?? this.mapQuery,
      isLocationSelected: isLocationSelected ?? this.isLocationSelected,
      photoCount: photoCount ?? this.photoCount,
      monthlyPrice: monthlyPrice ?? this.monthlyPrice,
      deposit: deposit ?? this.deposit,
      rentalDuration: rentalDuration ?? this.rentalDuration,
      rentalUnit: rentalUnit ?? this.rentalUnit,
      amenities: amenities ?? this.amenities,
      description: description ?? this.description,
      smokingPolicy: smokingPolicy ?? this.smokingPolicy,
      suitableFor: suitableFor ?? this.suitableFor,
      proofStatus: proofStatus ?? this.proofStatus,
      submittedAt: submittedAt ?? this.submittedAt,
    );
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
