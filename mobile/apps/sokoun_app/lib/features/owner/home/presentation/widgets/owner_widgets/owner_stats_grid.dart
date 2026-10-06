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
          iconColor: context.appColor(AppColors.amber),
          iconBackgroundColor: context.appColor(
            AppColors.orangePale,
            surface: true,
          ),
        ),
        OwnerStatCard(
          value: '$visitsThisWeek',
          label: LocaleKeys.ownerDashboardVisitsThisWeek,
          icon: Icons.calendar_today_outlined,
          iconColor: context.appColor(AppColors.blue),
          iconBackgroundColor: context.appColor(
            AppColors.bluePale,
            surface: true,
          ),
        ),
        OwnerStatCard(
          value: '$activeProperties',
          label: LocaleKeys.ownerDashboardActiveProperties,
          icon: Icons.apartment_rounded,
          iconColor: context.appColor(AppColors.sokoonTeal),
          iconBackgroundColor: context.appColor(
            AppColors.mintLight,
            surface: true,
          ),
        ),
        OwnerStatCard(
          value: _overallRatingLabel,
          label: LocaleKeys.ownerDashboardOverallRating,
          icon: Icons.star_outline_rounded,
          iconColor: AppColors.gold,
          iconBackgroundColor: context.appColor(
            AppColors.goldPale,
            surface: true,
          ),
        ),
      ],
    );
  }
}
