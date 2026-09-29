import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/kyc_intro_screen.dart';

import 'chat_verification_warning.dart';

class ChatRestrictedContent extends StatelessWidget {
  const ChatRestrictedContent({super.key});

  void _openVerification() => Go.to(const KycIntroScreen());

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.symmetric(horizontal: 28.w, vertical: 28.h),
      child: Column(
        children: [
          Container(
            width: 80.r,
            height: 80.r,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.orangePale,
              borderRadius: BorderRadius.circular(24.r),
            ),
            child: Icon(
              Icons.lock_outline_rounded,
              color: AppColors.amber,
              size: 34.r,
            ),
          ),
          18.szH,
          AppText(
            LocaleKeys.chatRestrictedTitle,
            color: AppColors.sokoonNavy,
            fontSize: 18.sp,
            fontWeight: FontWeight.w700,
            textAlign: TextAlign.center,
            maxLines: 2,
          ),
          8.szH,
          AppText(
            LocaleKeys.chatRestrictedDescription,
            color: AppColors.sokoonGray,
            fontSize: 14.sp,
            height: 1.55,
            textAlign: TextAlign.center,
            maxLines: 3,
          ),
          18.szH,
          const ChatVerificationWarning(),
          20.szH,
          DefaultButton(
            onTap: _openVerification,
            title: LocaleKeys.chatStartKyc,
            color: AppColors.sokoonTeal,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(16.r),
            width: double.infinity,
            height: 52.h,
            fontSize: 15.sp,
            fontWeight: FontWeight.w800,
          ),
          12.szH,
          DefaultButton(
            onTap: _openVerification,
            title: LocaleKeys.chatLearnMoreVerification,
            color: AppColors.white,
            textColor: AppColors.sokoonNavy,
            borderColor: AppColors.sokoonBorder,
            borderRadius: BorderRadius.circular(16.r),
            width: double.infinity,
            height: 52.h,
            fontSize: 15.sp,
            fontWeight: FontWeight.w800,
          ),
        ],
      ),
    );
  }
}
