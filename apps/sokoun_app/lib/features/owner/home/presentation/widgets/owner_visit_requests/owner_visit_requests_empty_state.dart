import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/generated/assets.dart';

class OwnerVisitRequestsEmptyState extends StatelessWidget {
  const OwnerVisitRequestsEmptyState({super.key});

  @override
  Widget build(BuildContext context) {
    final bool reduceMotion = MediaQuery.of(context).disableAnimations;
    return Center(
      child: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 36.w, vertical: 24.h),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ExcludeSemantics(
              child: Assets.lottie.noData.lottie(
                width: 140.r,
                height: 116.r,
                animate: !reduceMotion,
                repeat: false,
                fit: BoxFit.contain,
                package: 'melos_core',
              ),
            ),
            10.szH,
            AppText(
              LocaleKeys.ownerVisitsNoRequests,
              color: AppColors.sokoonNavy,
              fontSize: 17.sp,
              fontWeight: FontWeight.w900,
              textAlign: TextAlign.center,
              maxLines: 2,
            ),
            7.szH,
            AppText(
              LocaleKeys.ownerVisitsEmptyDescription,
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
