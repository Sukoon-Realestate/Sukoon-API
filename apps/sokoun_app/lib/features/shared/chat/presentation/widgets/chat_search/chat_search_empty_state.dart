import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/generated/assets.dart';

class ChatSearchEmptyState extends StatelessWidget {
  const ChatSearchEmptyState({super.key});

  @override
  Widget build(BuildContext context) {
    final bool reduceMotion = MediaQuery.of(context).disableAnimations;
    return Semantics(
      label: LocaleKeys.chatSearchEmptyTitle,
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 28.h),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ExcludeSemantics(
              child: Assets.lottie.notFound1.lottie(
                width: 116.r,
                height: 100.r,
                package: 'melos_core',
                animate: !reduceMotion,
                repeat: false,
                fit: BoxFit.contain,
              ),
            ),
            12.szH,
            AppText(
              LocaleKeys.chatSearchEmptyTitle,
              style: AppTextStyles.bold.copyWith(
                color: AppColors.sokoonNavy,
                fontSize: 17.sp,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
            ),
            6.szH,
            AppText(
              LocaleKeys.chatSearchEmptyDescription,
              style: AppTextStyles.medium13.copyWith(
                color: AppColors.sokoonGray,
                fontSize: 13.sp,
                height: 1.45,
              ),
              textAlign: TextAlign.center,
              maxLines: 3,
            ),
          ],
        ),
      ),
    );
  }
}
