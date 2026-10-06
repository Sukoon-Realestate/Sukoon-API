import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class ChatUnavailableIndicator extends StatelessWidget {
  const ChatUnavailableIndicator({
    super.key,
    required this.message,
    this.icon = Icons.lock_outline_rounded,
  });

  final String message;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 12.h),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        border: Border(
          top: BorderSide(color: context.appColor(AppColors.sokoonBorder)),
        ),
      ),
      child: SafeArea(
        top: false,
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 12.h),
          decoration: BoxDecoration(
            color: context.appColor(
              AppColors.scaffoldBackground,
              surface: true,
            ),
            borderRadius: BorderRadius.circular(16.r),
          ),
          child: Row(
            spacing: 8.w,
            children: [
              Icon(
                icon,
                color: context.appColor(AppColors.sokoonMuted),
                size: 16.r,
              ),
              Expanded(
                child: AppText(
                  message,
                  style: AppTextStyles.regular13.copyWith(
                    color: context.appColor(AppColors.sokoonMuted),
                    fontSize: 13.sp,
                    height: 1.45,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
