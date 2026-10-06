import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../config/res/config_imports.dart';
import '../../extensions/align_helper.dart';
import '../../extensions/sized_box_helper.dart';
import '../app_text.dart';

class PermissionHeader extends StatelessWidget {
  const PermissionHeader({
    super.key,
    required this.icon,
    required this.color,
    required this.backgroundColor,
    required this.title,
    required this.description,
  });

  final IconData icon;
  final Color color;
  final Color backgroundColor;
  final String title;
  final String description;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ExcludeSemantics(
          child: Container(
            width: 72.r,
            height: 72.r,
            decoration: BoxDecoration(
              color: backgroundColor,
              borderRadius: BorderRadius.circular(29.r),
            ),
            child: Icon(icon, size: 32.r, color: color),
          ),
        ).centerWidget,
        20.szH,
        Semantics(
          header: true,
          child: AppText(
            title,
            textAlign: TextAlign.center,
            color: context.appColor(AppColors.sokoonNavy),
            fontSize: 17.sp,
            fontWeight: FontWeight.w900,
            height: 1.5,
          ),
        ),
        8.szH,
        AppText(
          description,
          textAlign: TextAlign.center,
          color: context.appColor(AppColors.sokoonGray),
          fontSize: 13.sp,
          height: 1.75,
        ),
      ],
    );
  }
}
