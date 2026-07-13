import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/auth/presentation/screens/login_screen.dart';
import 'package:sokoun_app/features/auth/presentation/screens/register_screen.dart';
import '../../data/models/welcome.dart';
import '../widgets/welcome/welcome_center_card.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final currentRole = UserTypeHelper.instance.currentUserType;
    final WelcomeScreenContent content = WelcomeScreenContent.fromRole(currentRole);
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
                          color: content.headerIconBackgroundColor,
                          borderRadius: BorderRadius.circular(16.r),
                        ),
                        child: Icon(
                          content.headerIcon,
                          color: content.headerIconColor,
                          size: 30.r,
                        ),
                      ).centerWidget,
                      18.szH,
                      AppText(
                        content.title,
                        color: AppColors.sokoonNavy,
                        fontSize: 24.sp,
                        fontWeight: FontWeight.w900,
                        textAlign: TextAlign.center,
                      ),
                      8.szH,
                      AppText(
                        content.description,
                        color: AppColors.sokoonGray,
                        fontSize: 14.sp,
                        fontWeight: FontWeight.w400,
                        textAlign: TextAlign.center,
                        height: 1.45,
                      ),
                      24.szH,
                      ..._buildFeatureCards(content.features),
                      22.szH,
                      DefaultButton(
                        onTap: () => Go.to(const RegisterScreen()),
                        title: content.primaryButtonTitle,
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
                        onPressed: () => Go.to(const LoginScreen()),
                        style: TextButton.styleFrom(
                          minimumSize: Size.zero,
                          padding: EdgeInsets.symmetric(
                            horizontal: 8.w,
                            vertical: 6.h,
                          ),
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ),
                        child: AppText(
                          content.loginButtonTitle,
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
