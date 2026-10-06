import 'package:flutter/material.dart';
import 'package:sokoun_app/shared_widgets/sokoun_reveal.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_screen.dart';

import '../widgets/auth_scaffold.dart';
import '../widgets/kyc/kyc_feature_tile.dart';

class KycApprovedScreen extends StatelessWidget {
  const KycApprovedScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return AuthScaffold(
      showBackButton: false,
      padding: EdgeInsets.symmetric(horizontal: 32.w, vertical: 24.h),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SokounReveal(
            beginScale: .88,
            child: Container(
              width: 112.r,
              height: 112.r,
              decoration: BoxDecoration(
                color: context.appColor(AppColors.mintLight, surface: true),
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.shield_outlined,
                color: context.appColor(AppColors.sokoonTeal),
                size: 52.r,
              ),
            ),
          ),
          10.szH,
          Container(
            padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 4.h),
            decoration: BoxDecoration(
              color: context.appColor(AppColors.goldPale, surface: true),
              borderRadius: BorderRadius.circular(999.r),
            ),
            child: AppText(
              LocaleKeys.verified,
              style: AppTextStyles.semiBold.copyWith(
                color: context.appColor(AppColors.brown),
                fontSize: 12.sp,
              ),
            ),
          ).centerWidget,
          12.szH,
          AppText(
            LocaleKeys.kycApprovedTitle,
            style: AppTextStyles.bold.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
              fontSize: 24.sp,
            ),
            textAlign: TextAlign.center,
          ),
          8.szH,
          AppText(
            LocaleKeys.kycApprovedDescription,
            style: AppTextStyles.regular14.copyWith(
              color: context.appColor(AppColors.sokoonGray),
              fontSize: 14.sp,
              height: 1.45,
            ),
            textAlign: TextAlign.center,
          ),
          24.szH,
          KycFeatureTile(
            icon: Icons.chat_bubble_outline_rounded,
            title: LocaleKeys.chatEnabled,
          ),
          10.szH,
          KycFeatureTile(
            icon: Icons.verified_outlined,
            title: LocaleKeys.accountVerifiedBadge,
          ),
          10.szH,
          KycFeatureTile(
            icon: Icons.star_outline_rounded,
            title: LocaleKeys.priorityVisitBooking,
          ),
          24.szH,
          DefaultButton(
            onTap: () => Go.offAll(const TenantSearchScreen()),
            title: LocaleKeys.startHousingSearch,
            color: context.appColor(AppColors.sokoonTeal, surface: true),
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 52.h,
            width: double.infinity,
            textStyle: AppTextStyles.bold16.copyWith(
              fontSize: 16.sp,
              height: 1.45,
            ),
          ),
        ],
      ),
    );
  }
}
