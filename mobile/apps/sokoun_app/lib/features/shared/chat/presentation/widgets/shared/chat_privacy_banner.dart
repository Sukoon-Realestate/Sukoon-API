import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class ChatPrivacyBanner extends StatelessWidget {
  const ChatPrivacyBanner({super.key, required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 11.h),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.bluePale, surface: true),
        borderRadius: BorderRadius.circular(16.r),
      ),
      child: Row(
        spacing: 8.w,
        children: [
          Icon(
            Icons.lock_outline_rounded,
            color: context.appColor(AppColors.blue),
            size: 14.r,
          ),
          Expanded(
            child: AppText(
              text,
              style: AppTextStyles.medium12.copyWith(
                color: context.appColor(AppColors.blue),
                fontSize: 12.sp,
                height: 1.45,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
