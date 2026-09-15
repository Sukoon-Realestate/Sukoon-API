import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
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
        color: AppColors.orangePale,
        borderRadius: BorderRadius.circular(16.r),
      ),
      child: Row(
        children: [
          Icon(Icons.warning_amber_rounded, color: AppColors.amber, size: 16.r),
          8.szW,
          Expanded(
            child: AppText(
              LocaleKeys.chatVerifiedOnlyBanner,
              color: AppColors.brown,
              fontSize: 12.sp,
              fontWeight: FontWeight.w500,
              maxLines: 2,
            ),
          ),
          TextButton(
            onPressed: () => Go.to(const KycIntroScreen()),
            child: AppText(
              LocaleKeys.chatVerifyNow,
              color: AppColors.sokoonTeal,
              fontSize: 12.sp,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}
