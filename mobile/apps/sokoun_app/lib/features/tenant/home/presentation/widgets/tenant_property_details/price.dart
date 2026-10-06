import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class TenantPropertyPrice extends StatelessWidget {
  const TenantPropertyPrice({
    super.key,
    required this.price,
    required this.periodLabel,
  });

  final String price;
  final String periodLabel;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      crossAxisAlignment: WrapCrossAlignment.center,
      spacing: 6.w,
      runSpacing: 4.h,
      children: [
        AppText(
          price,
          style: AppTextStyles.extraBold.copyWith(
            color: context.appColor(AppColors.sokoonTeal),
            fontSize: 24.sp,
          ),
        ),
        AppText(
          periodLabel,
          style: AppTextStyles.medium13.copyWith(
            color: context.appColor(AppColors.sokoonGray),
            fontSize: 13.sp,
            height: 1.45,
          ),
        ),
      ],
    );
  }
}
