import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_content.dart';

import '../widgets/tenant_search/imports.dart';
import '../widgets/tenant_widgets/imports.dart';

class TenantSearchScreen extends StatelessWidget {
  const TenantSearchScreen({super.key});

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
                AppText(
                  'ابحث عن سكن',
                  color: AppColors.sokoonNavy,
                  fontSize: 20.sp,
                  fontWeight: FontWeight.w900,
                  textAlign: TextAlign.right,
                ),
                14.szH,
                const TenantSearchField(),
                14.szH,
                const SearchCategoryChips(
                  categories: TenantSearchContent.categories,
                ),
                18.szH,
                const SearchSectionTitle('مناطق مقترحة'),
                10.szH,
                const SuggestedAreasGrid(
                  areas: TenantSearchContent.suggestedAreas,
                ),
                18.szH,
                const SearchSectionTitle('بحثت عنها مؤخراً'),
                6.szH,
                for (final search in TenantSearchContent.recentSearches)
                  RecentSearchRow(search: search),
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
