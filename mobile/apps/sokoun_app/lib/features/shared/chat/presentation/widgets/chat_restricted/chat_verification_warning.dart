import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/kyc_intro_screen.dart';

class ChatVerificationWarning extends StatelessWidget {
  const ChatVerificationWarning({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 12.h),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.orangePale, surface: true),
        borderRadius: BorderRadius.circular(16.r),
      ),
      child: Row(
        children: [
          Icon(
            Icons.warning_amber_rounded,
            color: context.appColor(AppColors.amber),
            size: 16.r,
          ),
          8.szW,
          Expanded(
            child: AppText(
              LocaleKeys.chatVerifiedOnlyBanner,
              style: AppTextStyles.medium12.copyWith(
                color: context.appColor(AppColors.brown),
                fontSize: 12.sp,
                height: 1.45,
              ),
              maxLines: 2,
            ),
          ),
          TextButton(
            onPressed: () => Go.to(const KycIntroScreen()),
            child: AppText(
              LocaleKeys.chatVerifyNow,
              style: AppTextStyles.extraBold.copyWith(
                color: context.appColor(AppColors.sokoonTeal),
                fontSize: 12.sp,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
