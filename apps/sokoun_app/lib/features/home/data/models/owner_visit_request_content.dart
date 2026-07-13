import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

class OwnerVisitRequestSummaryContent {
  const OwnerVisitRequestSummaryContent({
    required this.label,
    required this.value,
    required this.backgroundColor,
    required this.borderColor,
    required this.valueColor,
  });

  final String label;
  final String value;
  final Color backgroundColor;
  final Color borderColor;
  final Color valueColor;
}

class OwnerVisitRequestFilterContent {
  const OwnerVisitRequestFilterContent({
    required this.label,
    this.count,
    this.isSelected = false,
  });

  final String label;
  final String? count;
  final bool isSelected;
}

class OwnerVisitRequestContent {
  const OwnerVisitRequestContent({
    required this.initial,
    required this.name,
    required this.property,
    required this.time,
    this.isVerified = false,
    this.showActions = false,
    this.acceptedLabel,
  });

  final String initial;
  final String name;
  final String property;
  final String time;
  final bool isVerified;
  final bool showActions;
  final String? acceptedLabel;
}

abstract final class OwnerVisitRequestsContent {
  static const summaries = [
    OwnerVisitRequestSummaryContent(
      label: 'إجمالي الطلبات',
      value: '6',
      backgroundColor: AppColors.tealAlpha07,
      borderColor: AppColors.tealAlpha19,
      valueColor: AppColors.sokoonTeal,
    ),
    OwnerVisitRequestSummaryContent(
      label: 'بانتظار الرد',
      value: '3',
      backgroundColor: AppColors.goldAlpha15,
      borderColor: AppColors.goldAlpha15,
      valueColor: AppColors.gold,
    ),
  ];

  static const filters = [
    OwnerVisitRequestFilterContent(label: 'الكل', count: '6', isSelected: true),
    OwnerVisitRequestFilterContent(label: 'جديد', count: '3'),
    OwnerVisitRequestFilterContent(label: 'مقبول', count: '2'),
    OwnerVisitRequestFilterContent(label: 'مرفوض', count: '1'),
    OwnerVisitRequestFilterContent(label: 'مكتمل'),
  ];

  static const requests = [
    OwnerVisitRequestContent(
      initial: 'أ',
      name: 'أحمد السيد',
      property: 'شقة 3 غرف — الرياض',
      time: 'غداً 10:00 ص',
      isVerified: true,
      showActions: true,
    ),
    OwnerVisitRequestContent(
      initial: 'س',
      name: 'سارة محمد',
      property: 'استوديو — جدة',
      time: 'الأحد 2:00 م',
      isVerified: true,
      acceptedLabel: 'تم القبول',
    ),
    OwnerVisitRequestContent(
      initial: 'خ',
      name: 'خالد عبدالله',
      property: 'غرفة — الدمام',
      time: 'الإثنين 11:00 ص',
      showActions: true,
    ),
  ];
}
