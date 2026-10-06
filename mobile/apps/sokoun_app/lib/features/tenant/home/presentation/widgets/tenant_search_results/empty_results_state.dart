import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:melos_core/generated/assets.dart';

class EmptyResultsState extends StatelessWidget {
  const EmptyResultsState({super.key, required this.onResetSearchPressed});

  final VoidCallback onResetSearchPressed;

  @override
  Widget build(BuildContext context) {
    final bool reduceMotion = MediaQuery.of(context).disableAnimations;
    return SingleChildScrollView(
      padding: EdgeInsets.symmetric(horizontal: 28.w, vertical: 20.h),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ExcludeSemantics(
            child: Assets.lottie.notFound1.lottie(
              width: 132.r,
              height: 112.r,
              animate: !reduceMotion,
              repeat: false,
              fit: BoxFit.contain,
              package: 'melos_core',
            ),
          ),
          8.szH,
          AppText(
            LocaleKeys.tenantSearchResultsEmptyTitle,
            style: AppTextStyles.bold.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
              fontSize: 17.sp,
            ),
            textAlign: TextAlign.center,
            maxLines: 2,
          ),
          6.szH,
          AppText(
            LocaleKeys.tenantSearchResultsEmptyDescription,
            style: AppTextStyles.medium13.copyWith(
              color: context.appColor(AppColors.sokoonGray),
              fontSize: 13.sp,
              height: 1.45,
            ),
            textAlign: TextAlign.center,
            maxLines: 3,
          ),
          18.szH,
          DefaultButton(
            onTap: onResetSearchPressed,
            title: LocaleKeys.tenantSearchResultsResetSearch,
            color: context.appColor(AppColors.sokoonTeal, surface: true),
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(12.r),
            height: 45.h,
            width: double.infinity,
            textStyle: AppTextStyles.extraBold.copyWith(fontSize: 14.sp),
          ),
        ],
      ),
    ).centerWidget;
  }
}
