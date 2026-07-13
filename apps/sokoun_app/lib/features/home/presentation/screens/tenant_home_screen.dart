import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../widgets/home_widgets.dart';

class TenantHomeScreen extends StatelessWidget {
  const TenantHomeScreen({super.key});

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
                const _TenantHeader(),
                18.szH,
                const HomeSearchBox(),
                16.szH,
                const TenantVisitBanner(),
                18.szH,
                HomeSectionHeader(
                  title: 'مقترح ليك',
                  actionTitle: 'عرض الكل',
                  onActionTap: () {},
                ),
                10.szH,
                const TenantPropertyCard(
                  title: 'شقة مفروشة — مدينة نصر',
                  rating: '4.8',
                  area: '90م²',
                  price: '6,500 ج/شهر',
                  icon: Icons.apartment_rounded,
                ),
                12.szH,
                const TenantPropertyCard(
                  title: 'ستوديو التجمع الخامس',
                  rating: '4.6',
                  area: '55م²',
                  price: '4,200 ج/شهر',
                  icon: Icons.meeting_room_outlined,
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
                icon: Icons.favorite_border_rounded,
                label: 'المحفوظات',
              ),
              HomeBottomNavItemData(
                icon: Icons.chat_bubble_outline_rounded,
                label: 'الشات',
              ),
              HomeBottomNavItemData(
                icon: Icons.notifications_none_rounded,
                label: 'الإشعارات',
              ),
              HomeBottomNavItemData(
                icon: Icons.person_outline_rounded,
                label: 'الحساب',
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TenantHeader extends StatelessWidget {
  const _TenantHeader();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const HomeAvatar(
          icon: Icons.person_outline_rounded,
          backgroundColor: AppColors.mintLight,
          iconColor: AppColors.sokoonTeal,
        ),
        10.szW,
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AppText(
                'أهلاً سارة 👋',
                color: AppColors.sokoonNavy,
                fontSize: 18.sp,
                fontWeight: FontWeight.w900,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              2.szH,
              AppText(
                'دلوقتي في مدينة نصر',
                color: AppColors.sokoonGray,
                fontSize: 12.sp,
                fontWeight: FontWeight.w400,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
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
