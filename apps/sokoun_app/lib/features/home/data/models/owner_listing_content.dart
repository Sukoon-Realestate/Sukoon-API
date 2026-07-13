import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

class OwnerListingStatusContent {
  const OwnerListingStatusContent({
    required this.label,
    required this.icon,
    required this.backgroundColor,
    required this.foregroundColor,
  });

  final String label;
  final IconData icon;
  final Color backgroundColor;
  final Color foregroundColor;
}

class OwnerListingActionContent {
  const OwnerListingActionContent({
    required this.label,
    required this.backgroundColor,
    required this.foregroundColor,
  });

  final String label;
  final Color backgroundColor;
  final Color foregroundColor;
}

class OwnerListingContent {
  const OwnerListingContent({
    required this.title,
    required this.status,
    required this.price,
    required this.views,
    required this.visits,
    required this.icon,
  });

  final String title;
  final OwnerListingStatusContent status;
  final String price;
  final String views;
  final String visits;
  final IconData icon;
}

abstract final class OwnerListingsContent {
  static const verifiedStatus = OwnerListingStatusContent(
    label: 'موثّق',
    icon: Icons.verified_rounded,
    backgroundColor: AppColors.goldPale,
    foregroundColor: AppColors.gold,
  );

  static const pendingStatus = OwnerListingStatusContent(
    label: 'قيد المراجعة',
    icon: Icons.schedule_rounded,
    backgroundColor: AppColors.orangePale,
    foregroundColor: AppColors.amber,
  );

  static const hiddenStatus = OwnerListingStatusContent(
    label: 'مخفي',
    icon: Icons.visibility_off_outlined,
    backgroundColor: AppColors.grayBackground,
    foregroundColor: AppColors.sokoonGray,
  );

  static const actions = [
    OwnerListingActionContent(
      label: 'تعديل',
      backgroundColor: AppColors.bluePale,
      foregroundColor: AppColors.blue,
    ),
    OwnerListingActionContent(
      label: 'إحصاءات',
      backgroundColor: AppColors.mintLight,
      foregroundColor: AppColors.sokoonTeal,
    ),
    OwnerListingActionContent(
      label: 'حذف',
      backgroundColor: AppColors.redPale,
      foregroundColor: AppColors.red,
    ),
  ];

  static const listings = [
    OwnerListingContent(
      title: 'شقة مفروشة — مدينة نصر',
      status: verifiedStatus,
      price: '6,500 ج/شهر',
      views: '142 مشاهدة',
      visits: '3 زيارة',
      icon: Icons.apartment_rounded,
    ),
    OwnerListingContent(
      title: 'ستوديو — التجمع الخامس',
      status: pendingStatus,
      price: '4,200 ج/شهر',
      views: '67 مشاهدة',
      visits: '0 زيارة',
      icon: Icons.meeting_room_outlined,
    ),
    OwnerListingContent(
      title: 'شقة 3 غرف — المهندسين',
      status: hiddenStatus,
      price: '8,800 ج/شهر',
      views: '0 مشاهدة',
      visits: '0 زيارة',
      icon: Icons.home_work_outlined,
    ),
  ];
}
