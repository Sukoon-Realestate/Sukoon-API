import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../widgets/home_widgets.dart';

class OwnerHomeScreen extends StatelessWidget {
  const OwnerHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: SingleChildScrollView(
            padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const _OwnerHeader(),
                18.szH,
                const _OwnerStatsGrid(),
                18.szH,
                const HomeSectionHeader(title: 'طلبات انتظار الرد'),
                10.szH,
                const OwnerRequestCard(
                  name: 'سارة أحمد',
                  details: 'شقة مدينة نصر · النهارده 3م',
                ),
                12.szH,
                const OwnerRequestCard(
                  name: 'محمد علي',
                  details: 'شقة مدينة نصر · غداً 12م',
                ),
                24.szH,
              ],
            ),
          ),
        ),
        bottomNavigationBar: const SafeArea(
          top: false,
          child: HomeBottomNav(
            items: [
              HomeBottomNavItemData(
                icon: Icons.home_outlined,
                label: 'الرئيسية',
                isActive: true,
              ),
              HomeBottomNavItemData(
                icon: Icons.apartment_rounded,
                label: 'عقاراتي',
              ),
              HomeBottomNavItemData(
                icon: Icons.assignment_outlined,
                label: 'الطلبات',
              ),
              HomeBottomNavItemData(
                icon: Icons.chat_bubble_outline_rounded,
                label: 'الشات',
              ),
              HomeBottomNavItemData(
                icon: Icons.more_horiz_rounded,
                label: 'المزيد',
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _OwnerHeader extends StatelessWidget {
  const _OwnerHeader();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const HomeAvatar(
          icon: Icons.key_rounded,
          backgroundColor: AppColors.goldPale,
          iconColor: AppColors.gold,
        ),
        10.szW,
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AppText(
                'أهلاً أحمد 👋',
                color: AppColors.sokoonNavy,
                fontSize: 18.sp,
                fontWeight: FontWeight.w900,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              4.szH,
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
                decoration: BoxDecoration(
                  color: AppColors.goldPale,
                  borderRadius: BorderRadius.circular(999.r),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.verified_rounded,
                      color: AppColors.gold,
                      size: 12.r,
                    ),
                    3.szW,
                    AppText(
                      'موثّق',
                      color: AppColors.gold,
                      fontSize: 12.sp,
                      fontWeight: FontWeight.w600,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        10.szW,
        const HomeCircleButton(
          icon: Icons.notifications_none_rounded,
          iconColor: AppColors.sokoonNavy,
          showBadge: true,
        ),
      ],
    );
  }
}

class _OwnerStatsGrid extends StatelessWidget {
  const _OwnerStatsGrid();

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
