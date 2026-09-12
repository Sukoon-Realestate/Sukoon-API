import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_listings_screen.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_screen.dart';

class NotificationsEmptyState extends StatelessWidget {
  const NotificationsEmptyState({super.key, required this.role});

  final NotificationRole role;

  void _exploreProperties() {
    if (role.isOwner) {
      Go.off(const OwnerListingsScreen());
      return;
    }

    Go.off(const TenantSearchScreen());
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Container(
          width: 88.r,
          height: 88.r,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: AppColors.sokoonBorder,
            borderRadius: BorderRadius.circular(28.r),
          ),
          child: Icon(
            Icons.notifications_none_rounded,
            color: AppColors.sokoonGray,
            size: 40.r,
          ),
        ),
        24.szH,
        AppText(
          LocaleKeys.notificationsEmptyTitle,
          color: AppColors.sokoonNavy,
          fontSize: 20.sp,
          fontWeight: FontWeight.w900,
          textAlign: TextAlign.center,
          maxLines: 2,
        ),
        10.szH,
        AppText(
          LocaleKeys.notificationsEmptyDescription,
          color: AppColors.sokoonGray,
          fontSize: 14.sp,
          height: 1.7,
          textAlign: TextAlign.center,
          maxLines: 4,
        ),
        28.szH,
        DefaultButton(
          onTap: _exploreProperties,
          title: LocaleKeys.notificationsExploreProperties,
          color: AppColors.white,
          textColor: AppColors.sokoonNavy,
          borderColor: AppColors.sokoonBorder,
          borderRadius: BorderRadius.circular(16.r),
          width: double.infinity,
          height: 50.h,
          fontSize: 14.sp,
          fontWeight: FontWeight.w800,
        ),
      ],
    ).paddingSymmetric(horizontal: 40.w);
  }
}
