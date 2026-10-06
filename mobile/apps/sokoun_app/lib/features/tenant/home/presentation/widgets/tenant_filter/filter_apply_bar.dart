import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

class FilterApplyBar extends StatelessWidget {
  const FilterApplyBar({super.key, required this.onApplyPressed});

  final VoidCallback? onApplyPressed;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 16.h),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        border: Border(
          top: BorderSide(color: context.appColor(AppColors.grayPale)),
        ),
      ),
      child: DefaultButton(
        onTap: onApplyPressed,
        title: LocaleKeys.tenantFilterShowResults,
        color: context.appColor(AppColors.sokoonTeal, surface: true),
        textColor: AppColors.white,
        borderRadius: BorderRadius.circular(14.r),
        height: 48.h,
        width: double.infinity,
        textStyle: AppTextStyles.bold14.copyWith(fontSize: 14.sp, height: 1.45),
      ),
    );
  }
}
