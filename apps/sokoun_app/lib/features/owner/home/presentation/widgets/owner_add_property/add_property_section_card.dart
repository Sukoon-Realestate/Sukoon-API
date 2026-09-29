import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class AddPropertySectionCard extends StatelessWidget {
  const AddPropertySectionCard({
    super.key,
    required this.title,
    required this.child,
    this.subtitle,
  });

  final String title;
  final String? subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: AppColors.grayPale),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(
            title,
            style: AppTextStyles.bold14.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 14.sp,
              height: 1.45,
            ),
            textAlign: TextAlign.start,
          ),
          if (subtitle != null) ...[
            4.szH,
            AppText(
              subtitle!,
              style: AppTextStyles.regular11.copyWith(
                color: AppColors.sokoonGray,
                fontSize: 11.sp,
                height: 1.45,
              ),
              textAlign: TextAlign.start,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
          12.szH,
          child,
        ],
      ),
    );
  }
}
