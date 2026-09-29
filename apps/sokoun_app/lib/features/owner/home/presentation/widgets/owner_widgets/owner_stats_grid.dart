import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';

import 'owner_stat_card.dart';

class OwnerStatsGrid extends StatelessWidget {
  const OwnerStatsGrid({
    super.key,
    required this.visitsThisWeek,
    required this.activeProperties,
    required this.overallRating,
    required this.pendingRequests,
  });

  final int visitsThisWeek;
  final int activeProperties;
  final double overallRating;
  final int pendingRequests;

  String get _overallRatingLabel {
    final bool isWholeNumber =
        overallRating == overallRating.truncateToDouble();
    return isWholeNumber
        ? overallRating.toInt().toString()
        : overallRating.toStringAsFixed(1);
  }

  @override
  Widget build(BuildContext context) {
    return SokounAdaptiveGrid(
      minimumWidth: 144,
      maximumColumns: 4,
      gap: 12,
      children: [
        OwnerStatCard(
          value: '$pendingRequests',
          label: LocaleKeys.ownerDashboardPendingRequests,
          icon: Icons.schedule_rounded,
          iconColor: AppColors.amber,
          iconBackgroundColor: AppColors.orangePale,
        ),
        OwnerStatCard(
          value: '$visitsThisWeek',
          label: LocaleKeys.ownerDashboardVisitsThisWeek,
          icon: Icons.calendar_today_outlined,
          iconColor: AppColors.blue,
          iconBackgroundColor: AppColors.bluePale,
        ),
        OwnerStatCard(
          value: '$activeProperties',
          label: LocaleKeys.ownerDashboardActiveProperties,
          icon: Icons.apartment_rounded,
          iconColor: AppColors.sokoonTeal,
          iconBackgroundColor: AppColors.mintLight,
        ),
        OwnerStatCard(
          value: _overallRatingLabel,
          label: LocaleKeys.ownerDashboardOverallRating,
          icon: Icons.star_outline_rounded,
          iconColor: AppColors.gold,
          iconBackgroundColor: AppColors.goldPale,
        ),
      ],
    );
  }
}
