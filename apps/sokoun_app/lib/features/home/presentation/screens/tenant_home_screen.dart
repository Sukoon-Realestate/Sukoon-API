import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/chat/presentation/screens/tenant_chat_list_screen.dart';
import 'package:sokoun_app/features/favorites/presentation/screens/favorites_screen.dart';

import '../widgets/tenant_widgets/imports.dart';

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
                const TenantHeader(),
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
        bottomNavigationBar: SafeArea(
          top: false,
          child: HomeBottomNav(
            items: [
              const HomeBottomNavItemData(
                icon: Icons.home_outlined,
                label: 'الرئيسية',
                isActive: true,
              ),
              HomeBottomNavItemData(
                icon: Icons.favorite_border_rounded,
                label: 'المحفوظات',
                onTap: () => Go.to(const FavoritesScreen()),
              ),
              HomeBottomNavItemData(
                icon: Icons.chat_bubble_outline_rounded,
                label: 'الشات',
                onTap: () => Go.to(const TenantChatListScreen()),
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
