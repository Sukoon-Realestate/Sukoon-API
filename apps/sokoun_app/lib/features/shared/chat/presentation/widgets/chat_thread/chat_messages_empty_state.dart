import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/generated/assets.dart';

class ChatMessagesEmptyState extends StatelessWidget {
  const ChatMessagesEmptyState({super.key});

  @override
  Widget build(BuildContext context) {
    final bool reduceMotion = MediaQuery.of(context).disableAnimations;
    return Semantics(
      label: LocaleKeys.chatMessagesEmptyTitle,
      child: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 20.h),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ExcludeSemantics(
              child: Assets.lottie.emptyBox.lottie(
                width: 108.r,
                height: 92.r,
                package: 'melos_core',
                animate: !reduceMotion,
                repeat: false,
                fit: BoxFit.contain,
              ),
            ),
            10.szH,
            AppText(
              LocaleKeys.chatMessagesEmptyTitle,
              color: AppColors.sokoonNavy,
              fontSize: 16.sp,
              fontWeight: FontWeight.w900,
              textAlign: TextAlign.center,
              maxLines: 2,
            ),
            6.szH,
            AppText(
              LocaleKeys.chatMessagesEmptyDescription,
              color: AppColors.sokoonGray,
              fontSize: 13.sp,
              fontWeight: FontWeight.w500,
              textAlign: TextAlign.center,
              maxLines: 3,
            ),
          ],
        ),
      ),
    );
  }
}
