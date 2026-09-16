import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
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
            color: AppColors.sokoonNavy,
            fontSize: 14.sp,
            fontWeight: FontWeight.w900,
            textAlign: TextAlign.start,
          ),
          if (subtitle != null) ...[
            4.szH,
            AppText(
              subtitle!,
              color: AppColors.sokoonGray,
              fontSize: 11.sp,
              fontWeight: FontWeight.w400,
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
