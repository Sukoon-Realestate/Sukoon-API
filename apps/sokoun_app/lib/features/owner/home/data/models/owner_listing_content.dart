import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
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
  static OwnerListingStatusContent get verifiedStatus =>
      OwnerListingStatusContent(
        label: LocaleKeys.ownerPropertyStatusVerified,
        icon: Icons.verified_rounded,
        backgroundColor: AppColors.goldPale,
        foregroundColor: AppColors.gold,
      );

  static OwnerListingStatusContent get pendingStatus =>
      OwnerListingStatusContent(
        label: LocaleKeys.ownerPropertyStatusPending,
        icon: Icons.schedule_rounded,
        backgroundColor: AppColors.orangePale,
        foregroundColor: AppColors.amber,
      );

  static OwnerListingStatusContent get hiddenStatus =>
      OwnerListingStatusContent(
        label: LocaleKeys.ownerPropertyStatusHidden,
        icon: Icons.visibility_off_outlined,
        backgroundColor: AppColors.grayBackground,
        foregroundColor: AppColors.sokoonGray,
      );

  static List<OwnerListingActionContent> get actions => [
    OwnerListingActionContent(
      label: LocaleKeys.ownerPropertiesEdit,
      backgroundColor: AppColors.bluePale,
      foregroundColor: AppColors.blue,
    ),
    OwnerListingActionContent(
      label: LocaleKeys.ownerPropertiesAnalytics,
      backgroundColor: AppColors.mintLight,
      foregroundColor: AppColors.sokoonTeal,
    ),
    OwnerListingActionContent(
      label: LocaleKeys.ownerPropertiesDelete,
      backgroundColor: AppColors.redPale,
      foregroundColor: AppColors.red,
    ),
  ];
}
