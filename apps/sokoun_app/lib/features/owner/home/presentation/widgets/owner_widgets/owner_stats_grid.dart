import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';

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
    final String value = isWholeNumber
        ? overallRating.toInt().toString()
        : overallRating.toStringAsFixed(1);
    return '$value★';
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          textDirection: TextDirection.ltr,
          children: [
            Expanded(
              child: OwnerStatCard(
                value: '$visitsThisWeek',
                label: LocaleKeys.ownerDashboardVisitsThisWeek,
                icon: Icons.calendar_today_outlined,
                iconColor: AppColors.blue,
                iconBackgroundColor: AppColors.bluePale,
              ),
            ),
            12.szW,
            Expanded(
              child: OwnerStatCard(
                value: '$activeProperties',
                label: LocaleKeys.ownerDashboardActiveProperties,
                icon: Icons.apartment_rounded,
                iconColor: AppColors.sokoonTeal,
                iconBackgroundColor: AppColors.mintLight,
              ),
            ),
          ],
        ),
        12.szH,
        Row(
          textDirection: TextDirection.ltr,
          children: [
            Expanded(
              child: OwnerStatCard(
                value: _overallRatingLabel,
                label: LocaleKeys.ownerDashboardOverallRating,
                icon: Icons.star_outline_rounded,
                iconColor: AppColors.gold,
                iconBackgroundColor: AppColors.goldPale,
              ),
            ),
            12.szW,
            Expanded(
              child: OwnerStatCard(
                value: '$pendingRequests',
                label: LocaleKeys.ownerDashboardPendingRequests,
                icon: Icons.schedule_rounded,
                iconColor: AppColors.amber,
                iconBackgroundColor: AppColors.orangePale,
              ),
            ),
          ],
        ),
      ],
    );
  }
}
