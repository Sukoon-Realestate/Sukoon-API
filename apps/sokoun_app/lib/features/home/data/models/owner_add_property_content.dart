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

  static const pricingFields = [
    AddPropertyFieldContent(
      label: 'السعر',
      value: '2500',
      isFocused: true,
      textAlign: TextAlign.right,
    ),
    AddPropertyFieldContent(label: 'تأمين الشقة', value: 'شهر واحد'),
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

  static const smokingOptions = [
    AddPropertyChipContent(label: 'مسموح'),
    AddPropertyChipContent(label: 'ممنوع', isSelected: true),
    AddPropertyChipContent(label: 'حسب الاتفاق'),
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
}
