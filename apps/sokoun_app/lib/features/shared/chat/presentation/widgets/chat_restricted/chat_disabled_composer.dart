import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class ChatDisabledComposer extends StatelessWidget {
  const ChatDisabledComposer({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 12.h),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(top: BorderSide(color: AppColors.sokoonBorder)),
      ),
      child: SafeArea(
        top: false,
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 12.h),
          decoration: BoxDecoration(
            color: AppColors.scaffoldBackground,
            borderRadius: BorderRadius.circular(16.r),
          ),
          child: Row(
            children: [
              Icon(
                Icons.lock_outline_rounded,
                color: AppColors.sokoonMuted,
                size: 16.r,
              ),
              8.szW,
              Expanded(
                child: AppText(
                  LocaleKeys.chatTypingDisabled,
                  color: AppColors.sokoonMuted,
                  fontSize: 13.sp,
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
