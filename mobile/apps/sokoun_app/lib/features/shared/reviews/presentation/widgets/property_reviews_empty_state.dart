import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/generated/assets.dart';

class PropertyReviewsEmptyState extends StatelessWidget {
  const PropertyReviewsEmptyState({super.key});
  @override
  Widget build(BuildContext context) => Center(
    child: SingleChildScrollView(
      padding: EdgeInsets.all(24.r),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ExcludeSemantics(
            child: Assets.lottie.noData.lottie(
              width: 144.r,
              height: 120.r,
              package: 'melos_core',
              repeat: false,
              animate:
                  !MediaQuery.disableAnimationsOf(context) &&
                  !MediaQuery.accessibleNavigationOf(context),
            ),
          ),
          12.szH,
          AppText(
            LocaleKeys.propertyReviewsEmptyTitle,
            textAlign: TextAlign.center,
            style: AppTextStyles.bold16.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
            ),
          ),
          8.szH,
          AppText(
            LocaleKeys.propertyReviewsEmptyDescription,
            textAlign: TextAlign.center,
            style: AppTextStyles.regular14.copyWith(
              color: context.appColor(AppColors.sokoonGray),
            ),
          ),
        ],
      ),
    ),
  );
}
