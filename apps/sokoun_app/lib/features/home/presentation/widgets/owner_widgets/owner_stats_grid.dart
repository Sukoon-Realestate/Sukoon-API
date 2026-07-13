import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';

import 'owner_stat_card.dart';

class OwnerStatsGrid extends StatelessWidget {
  const OwnerStatsGrid({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          textDirection: TextDirection.ltr,
          children: [
            const Expanded(
              child: OwnerStatCard(
                value: '7',
                label: 'زيارات هذا الأسبوع',
                icon: Icons.calendar_today_outlined,
                iconColor: AppColors.blue,
                iconBackgroundColor: AppColors.bluePale,
              ),
            ),
            12.szW,
            const Expanded(
              child: OwnerStatCard(
                value: '3',
                label: 'عقارات نشطة',
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
            const Expanded(
              child: OwnerStatCard(
                value: '4.9★',
                label: 'التقييم العام',
                icon: Icons.star_outline_rounded,
                iconColor: AppColors.gold,
                iconBackgroundColor: AppColors.goldPale,
              ),
            ),
            12.szW,
            const Expanded(
              child: OwnerStatCard(
                value: '2',
                label: 'طلبات معلقة',
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
