import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';

class OwnerVisitRequestsTopBar extends StatelessWidget {
  const OwnerVisitRequestsTopBar({
    super.key,
    required this.showBackButton,
    required this.ownerPropertyId,
  });

  final bool showBackButton;
  final String ownerPropertyId;

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
        children: [
          SizedBox(
            width: 36.r,
            height: 36.r,
            child: !showBackButton
                ? null
                : IconButton(
                    onPressed: Go.back,
                    visualDensity: VisualDensity.compact,
                    style: IconButton.styleFrom(
                      backgroundColor: AppColors.grayBackground,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(999.r),
                      ),
                    ),
                    icon: Icon(
                      Icons.arrow_back_ios_new_rounded,
                      color: AppColors.sokoonNavy,
                      size: 20.r,
                    ),
                  ),
          ),
          const Spacer(),
          AppText(
            LocaleKeys.ownerVisitsTitle,
            color: AppColors.sokoonNavy,
            fontSize: 16.sp,
            fontWeight: FontWeight.w700,
            textAlign: TextAlign.center,
          ),
          const Spacer(),
          SizedBox.square(
            dimension: 36.r,
            child: IconButton(
              onPressed: () => Go.to(
                OwnerRequestsCalendarScreen(ownerPropertyId: ownerPropertyId),
              ),
              tooltip: LocaleKeys.ownerCalendarTitle,
              padding: EdgeInsets.zero,
              visualDensity: VisualDensity.compact,
              style: IconButton.styleFrom(
                minimumSize: Size.square(36.r),
                maximumSize: Size.square(36.r),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
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
          ),
        ],
      ),
    );
  }
}
