import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

class FilterApplyBar extends StatelessWidget {
  const FilterApplyBar({super.key, required this.onApplyPressed});

  final VoidCallback? onApplyPressed;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 16.h),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(top: BorderSide(color: AppColors.grayPale)),
      ),
      child: DefaultButton(
        onTap: onApplyPressed,
        title: LocaleKeys.tenantFilterShowResults,
        color: AppColors.sokoonTeal,
        textColor: AppColors.white,
        borderRadius: BorderRadius.circular(14.r),
        height: 48.h,
        width: double.infinity,
        fontSize: 14.sp,
        fontWeight: FontWeight.w700,
      ),
    );
  }
}
