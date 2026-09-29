import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:melos_core/generated/assets.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_add_property_flow_screen.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_screen.dart';

class NotificationsEmptyState extends StatelessWidget {
  const NotificationsEmptyState({super.key, required this.role});

  final NotificationRole role;

  void _exploreProperties() {
    if (role.isOwner) {
      Go.to(const OwnerAddPropertyFlowScreen());
      return;
    }

    Go.to(const TenantSearchScreen());
  }

  @override
  Widget build(BuildContext context) {
    final bool reduceMotion = MediaQuery.of(context).disableAnimations;
    return Semantics(
      label: LocaleKeys.notificationsEmptyTitle,
      child: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 40.w, vertical: 20.h),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ExcludeSemantics(
              child: Assets.lottie.noData.lottie(
                width: 140.r,
                height: 116.r,
                animate: !reduceMotion,
                repeat: false,
                fit: BoxFit.contain,
                package: 'melos_core',
              ),
            ),
            12.szH,
            AppText(
              LocaleKeys.notificationsEmptyTitle,
              color: AppColors.sokoonNavy,
              fontSize: 20.sp,
              fontWeight: FontWeight.w700,
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
              title: role.isOwner
                  ? LocaleKeys.notificationsOwnerAddProperty
                  : LocaleKeys.notificationsExploreProperties,
              color: AppColors.sokoonTeal,
              textColor: AppColors.white,
              borderRadius: BorderRadius.circular(12.r),
              width: double.infinity,
              height: 46.h,
              fontSize: 14.sp,
              fontWeight: FontWeight.w800,
            ),
          ],
        ),
      ).centerWidget,
    );
  }
}
