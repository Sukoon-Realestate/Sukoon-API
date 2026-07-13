import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class OwnerRequestPrivacyBanner extends StatelessWidget {
  const OwnerRequestPrivacyBanner({super.key, required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 10.h),
      decoration: BoxDecoration(
        color: AppColors.bluePale,
        borderRadius: BorderRadius.circular(14.r),
      ),
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          Icon(Icons.privacy_tip_outlined, color: AppColors.blue, size: 16.r),
          8.szW,
          Expanded(
            child: AppText(
              message,
              color: AppColors.blue,
              fontSize: 12.sp,
              fontWeight: FontWeight.w600,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
