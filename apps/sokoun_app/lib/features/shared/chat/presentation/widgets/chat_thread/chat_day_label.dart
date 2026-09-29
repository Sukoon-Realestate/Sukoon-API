import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class ChatDayLabel extends StatelessWidget {
  const ChatDayLabel({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 9.w, vertical: 3.h),
      decoration: BoxDecoration(
        color: AppColors.scaffoldBackground,
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: AppText(
        LocaleKeys.chatToday,
        style: AppTextStyles.regular11.copyWith(
          color: AppColors.sokoonGray,
          fontSize: 11.sp,
          height: 1.45,
        ),
      ),
    ).paddingOnly(top: 10.h, bottom: 2.h);
  }
}
