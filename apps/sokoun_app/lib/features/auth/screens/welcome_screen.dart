import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/auth/screens/widgets/welcome/welcome_center_card.dart';
import 'package:sokoun_app/features/auth/screens/widgets/welcome/welcome_page_indicator.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key, this.onStartSearch, this.onLogin});

  final VoidCallback? onStartSearch;
  final VoidCallback? onLogin;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight),
                child: Padding(
                  padding: EdgeInsets.symmetric(horizontal: 24.w),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      24.szH,
                      Container(
                        width: 64.r,
                        height: 64.r,
                        decoration: BoxDecoration(
                          color: AppColors.mintLight,
                          borderRadius: BorderRadius.circular(16.r),
                        ),
                        child: Icon(
                          Icons.shield_outlined,
                          color: AppColors.sokoonTeal,
                          size: 30.r,
                        ),
                      ).centerWidget,
                      18.szH,
                      AppText(
                        LocaleKeys.welcomeToSokoon,
                        color: AppColors.sokoonNavy,
                        fontSize: 24.sp,
                        fontWeight: FontWeight.w900,
                        textAlign: TextAlign.center,
                      ),
                      8.szH,
                      AppText(
                        LocaleKeys.sokoonWelcomeDescription,
                        color: AppColors.sokoonGray,
                        fontSize: 14.sp,
                        fontWeight: FontWeight.w400,
                        textAlign: TextAlign.center,
                        height: 1.45,
                      ),
                      24.szH,
                      WelcomeCenterCard(
                        icon: Icons.search_rounded,
                        iconBackgroundColor: AppColors.mintLight,
                        iconColor: AppColors.sokoonTeal,
                        title: LocaleKeys.searchEasily,
                        subtitle: LocaleKeys.thousandsPropertiesAcrossEgypt,
                      ),
                      12.szH,
                      WelcomeCenterCard(
                        icon: Icons.verified_user_outlined,
                        iconBackgroundColor: AppColors.greenPale,
                        iconColor: AppColors.green,
                        title: LocaleKeys.safetyAndReliability,
                        subtitle: LocaleKeys.verifiedOwnersReviewedProperties,
                      ),
                      12.szH,
                      WelcomeCenterCard(
                        icon: Icons.chat_bubble_outline_rounded,
                        iconBackgroundColor: AppColors.bluePale,
                        iconColor: AppColors.blue,
                        title: LocaleKeys.directContact,
                        subtitle:
                            LocaleKeys.directChatWithOwnersAfterVerification,
                      ),
                      26.szH,
                      const WelcomePageIndicator(),
                      22.szH,
                      DefaultButton(
                        onTap: onStartSearch,
                        title: LocaleKeys.startHousingSearch,
                        color: AppColors.sokoonTeal,
                        textColor: AppColors.white,
                        borderRadius: BorderRadius.circular(8.r),
                        height: 52.h,
                        width: double.infinity,
                        fontSize: 16.sp,
                        fontWeight: FontWeight.w700,
                      ),
                      14.szH,
                      TextButton(
                        onPressed: onLogin,
                        style: TextButton.styleFrom(
                          minimumSize: Size.zero,
                          padding: EdgeInsets.symmetric(
                            horizontal: 8.w,
                            vertical: 6.h,
                          ),
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ),
                        child: AppText(
                          LocaleKeys.haveAccountLogin,
                          color: AppColors.sokoonGray,
                          fontSize: 14.sp,
                          fontWeight: FontWeight.w600,
                          textAlign: TextAlign.center,
                          maxLines: 2,
                        ),
                      ),
                      24.szH,
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
