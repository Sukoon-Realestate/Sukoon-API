import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/generated/assets.dart';

class OwnerPendingRequestsEmptyState extends StatelessWidget {
  const OwnerPendingRequestsEmptyState({super.key});

  @override
  Widget build(BuildContext context) {
    final bool reduceMotion = MediaQuery.of(context).disableAnimations;
    return Semantics(
      label: LocaleKeys.ownerDashboardNoPendingTitle,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ExcludeSemantics(
            child: Assets.lottie.noData.lottie(
              width: 112.r,
              height: 92.r,
              animate: !reduceMotion,
              repeat: false,
              fit: BoxFit.contain,
              package: 'melos_core',
            ),
          ),
          6.szH,
          AppText(
            LocaleKeys.ownerDashboardNoPendingTitle,
            color: AppColors.sokoonNavy,
            fontSize: 15.sp,
            fontWeight: FontWeight.w900,
            textAlign: TextAlign.center,
            maxLines: 2,
          ),
          5.szH,
          AppText(
            LocaleKeys.ownerDashboardNoPendingDescription,
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            fontWeight: FontWeight.w500,
            textAlign: TextAlign.center,
            maxLines: 3,
          ),
        ],
      ).paddingSymmetric(horizontal: 24.w, vertical: 8.h),
    );
  }
}
