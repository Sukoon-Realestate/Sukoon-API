import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../config/res/config_imports.dart';
import '../../extensions/padding_extension.dart';
import '../../extensions/sized_box_helper.dart';
import '../app_text.dart';

class PermissionBenefitRow extends StatelessWidget {
  const PermissionBenefitRow({
    super.key,
    required this.title,
    required this.description,
    required this.color,
    this.backgroundColor,
  });

  final String title;
  final String description;
  final Color color;

  /// A colored tile for notification benefits; location benefits use a dot.
  final Color? backgroundColor;

  @override
  Widget build(BuildContext context) {
    final Widget dot = Container(
      width: backgroundColor == null ? 6.r : 8.r,
      height: backgroundColor == null ? 6.r : 8.r,
      decoration: BoxDecoration(color: color, shape: BoxShape.circle),
    );

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ExcludeSemantics(
          child: backgroundColor == null
              ? dot.paddingOnly(top: 6.h)
              : Container(
                  width: 32.r,
                  height: 32.r,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: backgroundColor,
                    borderRadius: BorderRadius.circular(8.r),
                  ),
                  child: dot,
                ),
        ),
        10.szW,
        Expanded(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AppText(
                title,
                color: context.appColor(AppColors.sokoonNavy),
                fontSize: 13.sp,
                fontWeight: FontWeight.w700,
                height: 1.5,
              ),
              AppText(
                description,
                color: context.appColor(AppColors.sokoonGray),
                fontSize: 12.sp,
                height: 1.5,
              ),
            ],
          ),
        ),
      ],
    );
  }
}
