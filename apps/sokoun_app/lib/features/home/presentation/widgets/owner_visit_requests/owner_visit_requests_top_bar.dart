import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class OwnerVisitRequestsTopBar extends StatelessWidget {
  const OwnerVisitRequestsTopBar({
    super.key,
    required this.onBackPressed,
    required this.onCalendarPressed,
  });

  final VoidCallback onBackPressed;
  final VoidCallback onCalendarPressed;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 52.h,
      padding: EdgeInsets.symmetric(horizontal: 16.w),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.grayPale)),
      ),
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          IconButton(
            key: const ValueKey('owner-requests-back'),
            onPressed: onBackPressed,
            visualDensity: VisualDensity.compact,
            style: IconButton.styleFrom(
              backgroundColor: AppColors.grayBackground,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12.r),
              ),
            ),
            icon: Icon(
              Icons.chevron_left_rounded,
              color: AppColors.sokoonNavy,
              size: 22.r,
            ),
          ),
          const Spacer(),
          AppText(
            LocaleKeys.ownerVisitsTitle,
            color: AppColors.sokoonNavy,
            fontSize: 16.sp,
            fontWeight: FontWeight.w900,
            textAlign: TextAlign.center,
          ),
          const Spacer(),
          IconButton(
            key: const ValueKey('owner-open-calendar'),
            onPressed: onCalendarPressed,
            tooltip: LocaleKeys.ownerCalendarTitle,
            visualDensity: VisualDensity.compact,
            style: IconButton.styleFrom(
              backgroundColor: AppColors.goldPale,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12.r),
              ),
            ),
            icon: Icon(
              Icons.calendar_month_outlined,
              color: AppColors.gold,
              size: 20.r,
            ),
          ),
        ],
      ),
    );
  }
}
