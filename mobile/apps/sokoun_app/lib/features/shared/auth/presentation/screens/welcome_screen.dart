import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_logo_widget.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/login_screen.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/register_flow_screen.dart';

import '../../data/models/welcome.dart';
import '../widgets/auth_scaffold.dart';
import '../widgets/welcome/welcome_center_card.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final WelcomeScreenContent content = WelcomeScreenContent.account();

    return AuthScaffold(
      showBackButton: false,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          24.szH,
          Container(
            width: 64.r,
            height: 64.r,
            decoration: BoxDecoration(
              color: context.appColor(
                content.headerIconBackgroundColor,
                surface: true,
              ),
              borderRadius: BorderRadius.circular(16.r),
            ),
            child: AppLogoWidget(),
          ).centerWidget,
          18.szH,
          AppText(
            content.title,
            style: AppTextStyles.bold.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
              fontSize: 24.sp,
            ),
            textAlign: TextAlign.center,
          ),
          8.szH,
          AppText(
            content.description,
            style: AppTextStyles.regular14.copyWith(
              color: context.appColor(AppColors.sokoonGray),
              fontSize: 14.sp,
              height: 1.45,
            ),
            textAlign: TextAlign.center,
          ),
          24.szH,
          ..._buildFeatureCards(content.features),
          22.szH,
          DefaultButton(
            onTap: () => Go.to(const RegisterFlowScreen()),
            title: content.primaryButtonTitle,
            color: context.appColor(AppColors.sokoonTeal, surface: true),
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(8.r),
            height: 52.h,
            width: double.infinity,
            textStyle: AppTextStyles.bold16.copyWith(
              fontSize: 16.sp,
              height: 1.45,
            ),
          ),
          14.szH,
          TextButton(
            onPressed: () => Go.to(const LoginScreen()),
            style: TextButton.styleFrom(
              minimumSize: const Size(48, 48),
              padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 6.h),
            ),
            child: AppText(
              content.loginButtonTitle,
              style: AppTextStyles.semiBold.copyWith(
                color: context.appColor(AppColors.sokoonGray),
                fontSize: 14.sp,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
            ),
          ),
          24.szH,
        ],
      ),
    );
  }

  List<Widget> _buildFeatureCards(List<WelcomeFeatureContent> features) {
    final List<Widget> widgets = <Widget>[];

    for (int i = 0; i < features.length; i++) {
      final WelcomeFeatureContent feature = features[i];
      widgets.add(
        WelcomeCenterCard(
          icon: feature.icon,
          iconBackgroundColor: feature.iconBackgroundColor,
          iconColor: feature.iconColor,
          title: feature.title,
          subtitle: feature.subtitle,
        ),
      );

      if (i < features.length - 1) {
        widgets.add(12.szH);
      }
    }

    return widgets;
  }
}
