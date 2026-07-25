import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/notifications/presentation/screens/notifications_screen.dart';

import '../widgets/owner_widgets/imports.dart';

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
                OwnerHeader(
                  onNotificationsPressed: () => Go.to(
                    const NotificationsScreen(role: NotificationRole.owner),
                  ),
                ),
                18.szH,
                const OwnerStatsGrid(),
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
