import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class ChatVerifiedBadge extends StatelessWidget {
  const ChatVerifiedBadge({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 7.w, vertical: 3.h),
      decoration: BoxDecoration(
        color: AppColors.goldPale,
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        spacing: 4.w,
        children: [
          Icon(
            Icons.check_circle_outline_rounded,
            color: AppColors.sokoonGold,
            size: 11.r,
          ),
          AppText(
            LocaleKeys.verified,
            style: AppTextStyles.bold10.copyWith(
              color: AppColors.sokoonGold,
              fontSize: 10.sp,
              height: 1.45,
            ),
            maxLines: 1,
          ),
        ],
      ),
    );
  }
}
