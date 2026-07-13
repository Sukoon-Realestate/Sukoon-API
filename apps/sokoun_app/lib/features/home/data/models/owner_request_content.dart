import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

class OwnerRequestTabContent {
  const OwnerRequestTabContent({required this.label, this.isSelected = false});

  final String label;
  final bool isSelected;
}

class OwnerRequestStatusContent {
  const OwnerRequestStatusContent({
    required this.label,
    required this.backgroundColor,
    required this.foregroundColor,
  });

  final String label;
  final Color backgroundColor;
  final Color foregroundColor;
}

class OwnerRequestActionContent {
  const OwnerRequestActionContent({
    required this.label,
    required this.backgroundColor,
    required this.foregroundColor,
  });

  final String label;
  final Color backgroundColor;
  final Color foregroundColor;
}

class OwnerRequestContent {
  const OwnerRequestContent({
    required this.name,
    required this.details,
    required this.status,
    this.isVerified = false,
    this.showActions = false,
    this.privacyMessage,
  });

  final String name;
  final String details;
  final OwnerRequestStatusContent status;
  final bool isVerified;
  final bool showActions;
  final String? privacyMessage;
}

abstract final class OwnerRequestsContent {
  static const tabs = [
    OwnerRequestTabContent(label: 'الجديدة (2)', isSelected: true),
    OwnerRequestTabContent(label: 'قيد الانتظار'),
    OwnerRequestTabContent(label: 'المقبولة'),
    OwnerRequestTabContent(label: 'المرفوضة'),
  ];

  static const newStatus = OwnerRequestStatusContent(
    label: 'جديد',
    backgroundColor: AppColors.mintLight,
    foregroundColor: AppColors.sokoonTeal,
  );

  static const pendingStatus = OwnerRequestStatusContent(
    label: 'انتظار',
    backgroundColor: AppColors.orangePale,
    foregroundColor: AppColors.amber,
  );

  static const acceptedStatus = OwnerRequestStatusContent(
    label: 'مقبول',
    backgroundColor: AppColors.greenPale,
    foregroundColor: AppColors.emerald,
  );

  static const actions = [
    OwnerRequestActionContent(
      label: 'قبول',
      backgroundColor: AppColors.emerald,
      foregroundColor: AppColors.white,
    ),
    OwnerRequestActionContent(
      label: 'رفض',
      backgroundColor: AppColors.redPale,
      foregroundColor: AppColors.red,
    ),
    OwnerRequestActionContent(
      label: 'شات',
      backgroundColor: AppColors.bluePale,
      foregroundColor: AppColors.blue,
    ),
  ];

  static const requests = [
    OwnerRequestContent(
      name: 'سارة أحمد',
      details: 'شقة مدينة نصر · النهارده 3م',
      status: newStatus,
      isVerified: true,
      showActions: true,
    ),
    OwnerRequestContent(
      name: 'محمد علي',
      details: 'شقة مدينة نصر · غداً 12م',
      status: newStatus,
      isVerified: true,
      showActions: true,
    ),
    OwnerRequestContent(
      name: 'نورا كمال',
      details: 'ستوديو التجمع · الخميس 5م',
      status: pendingStatus,
      privacyMessage: 'هذا المستأجر لم يوثق هويته بعد',
    ),
    OwnerRequestContent(
      name: 'كريم سالم',
      details: 'شقة المهندسين · الجمعة 4م',
      status: acceptedStatus,
      isVerified: true,
    ),
  ];
}
