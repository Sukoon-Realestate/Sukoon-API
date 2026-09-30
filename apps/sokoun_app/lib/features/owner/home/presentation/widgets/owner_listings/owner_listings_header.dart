import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class OwnerListingsHeader extends StatelessWidget {
  const OwnerListingsHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          height: 38.h,
          padding: EdgeInsets.symmetric(horizontal: 12.w),
          decoration: BoxDecoration(
            color: AppColors.sokoonTeal,
            borderRadius: BorderRadius.circular(14.r),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            spacing: 5.w,
            children: [
              Icon(Icons.add_rounded, color: AppColors.white, size: 18.r),
              AppText(
                LocaleKeys.ownerPropertiesAdd,
                style: AppTextStyles.bold13.copyWith(
                  color: AppColors.white,
                  fontSize: 13.sp,
                  height: 1.45,
                ),
              ),
            ],
          ),
        ),
        const Spacer(),
        AppText(
          LocaleKeys.ownerPropertiesTitle,
          style: AppTextStyles.bold.copyWith(
            color: AppColors.sokoonNavy,
            fontSize: 20.sp,
          ),
          textAlign: TextAlign.start,
        ),
      ],
    );
  }
}
