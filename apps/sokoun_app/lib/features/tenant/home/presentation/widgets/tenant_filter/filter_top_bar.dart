import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class FilterTopBar extends StatelessWidget {
  const FilterTopBar({
    super.key,
    required this.activeCount,
    required this.onReset,
  });

  final int activeCount;
  final VoidCallback onReset;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 56.h,
      padding: EdgeInsets.symmetric(horizontal: 16.w),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.grayPale)),
      ),
      child: Row(
        children: [
          Container(
            width: 22.r,
            height: 22.r,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              color: AppColors.sokoonTeal,
              shape: BoxShape.circle,
            ),
            child: AppText(
              '$activeCount',
              style: AppTextStyles.bold12.copyWith(
                color: AppColors.white,
                fontSize: 12.sp,
                height: 1.45,
              ),
            ),
          ),
          8.szW,
          AppText(
            LocaleKeys.tenantFilterTitle,
            style: AppTextStyles.bold.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 17.sp,
            ),
          ),
          const Spacer(),
          GestureDetector(
            onTap: onReset,
            behavior: HitTestBehavior.opaque,
            child: AppText(
              LocaleKeys.tenantFilterReset,
              style: AppTextStyles.extraBold13.copyWith(
                color: AppColors.sokoonTeal,
                fontSize: 13.sp,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
