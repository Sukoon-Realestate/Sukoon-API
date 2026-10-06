import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class ChatDayLabel extends StatelessWidget {
  const ChatDayLabel({super.key, required this.date});

  final DateTime date;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 9.w, vertical: 3.h),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.scaffoldBackground, surface: true),
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: AppText(
        DateUtils.isSameDay(date, DateTime.now())
            ? LocaleKeys.chatToday
            : MaterialLocalizations.of(context).formatMediumDate(date),
        style: AppTextStyles.regular11.copyWith(
          color: context.appColor(AppColors.sokoonGray),
          fontSize: 12.sp,
          height: 1.45,
        ),
      ),
    ).paddingOnly(top: 10.h, bottom: 2.h);
  }
}
