import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

import '../widgets/auth_scaffold.dart';
import '../widgets/kyc/kyc_feature_tile.dart';

class KycApprovedScreen extends StatelessWidget {
  const KycApprovedScreen({super.key, this.onStartSearch});

  final VoidCallback? onStartSearch;

  @override
  Widget build(BuildContext context) {
    return AuthScaffold(
      showBackButton: false,
      padding: EdgeInsets.symmetric(horizontal: 32.w, vertical: 24.h),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            width: 112.r,
            height: 112.r,
            decoration: const BoxDecoration(
              color: AppColors.mintLight,
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.shield_outlined,
              color: AppColors.sokoonTeal,
              size: 52.r,
            ),
          ),
          10.szH,
          Center(
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 4.h),
              decoration: BoxDecoration(
                color: AppColors.goldPale,
                borderRadius: BorderRadius.circular(999.r),
              ),
              child: AppText(
                LocaleKeys.verified,
                color: AppColors.sokoonGold,
                fontSize: 12.sp,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          12.szH,
          AppText(
            LocaleKeys.kycApprovedTitle,
            color: AppColors.sokoonNavy,
            fontSize: 24.sp,
            fontWeight: FontWeight.w900,
            textAlign: TextAlign.center,
          ),
          8.szH,
          AppText(
            LocaleKeys.kycApprovedDescription,
            color: AppColors.sokoonGray,
            fontSize: 14.sp,
            fontWeight: FontWeight.w400,
            textAlign: TextAlign.center,
            height: 1.45,
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
            onTap: onStartSearch,
            title: LocaleKeys.startHousingSearch,
            color: AppColors.sokoonTeal,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 52.h,
            width: double.infinity,
            fontSize: 16.sp,
            fontWeight: FontWeight.w700,
          ),
        ],
      ),
    );
  }
}
