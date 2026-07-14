import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class TenantLocationTopBar extends StatelessWidget {
  const TenantLocationTopBar({super.key, required this.onBack});

  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 54.h,
      padding: EdgeInsets.symmetric(horizontal: 16.w),
      child: Row(
        children: [
          GestureDetector(
            onTap: onBack,
            behavior: HitTestBehavior.opaque,
            child: Icon(
              Icons.arrow_back_ios_new_rounded,
              color: AppColors.sokoonNavy,
              size: 19.r,
            ),
          ),
          12.szW,
          AppText(
            'الموقع التقريبي',
            color: AppColors.sokoonNavy,
            fontSize: 18.sp,
            fontWeight: FontWeight.w900,
          ),
        ],
      ),
    );
  }
}
