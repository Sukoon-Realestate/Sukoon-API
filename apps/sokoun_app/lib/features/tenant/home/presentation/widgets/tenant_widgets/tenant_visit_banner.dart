import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart' hide TextDirection;
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/features/tenant/visits/data/visit_schedule_rules.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';

class TenantVisitBanner extends StatelessWidget {
  const TenantVisitBanner({super.key, required this.banner});

  final HomeVisitBannerModel banner;

  String _scheduleLabel(BuildContext context) {
    final DateTime? date = VisitScheduleRules.date(banner.visitDate.trim());
    final ({int hour, int minute, int second})? slot = VisitScheduleRules.time(
      banner.visitTime.trim(),
    );
    final String dateLabel = date == null
        ? banner.visitDate.trim()
        : DateFormat.yMMMd(context.locale.toString()).format(date);
    final String timeLabel = slot == null
        ? banner.visitTime.trim()
        : MaterialLocalizations.of(context).formatTimeOfDay(
            TimeOfDay(hour: slot.hour, minute: slot.minute),
            alwaysUse24HourFormat: MediaQuery.alwaysUse24HourFormatOf(context),
          );
    return [
      dateLabel,
      timeLabel,
    ].where((value) => value.isNotEmpty).join(' · ');
  }

  @override
  Widget build(BuildContext context) {
    final String propertyLabel = [
      banner.propertyTitle.trim(),
      banner.propertyDistrict.trim(),
    ].where((value) => value.isNotEmpty).join(' · ');
    final String scheduleLabel = _scheduleLabel(context);
    return Semantics(
      button: true,
      child: GestureDetector(
        onTap: () => Go.to(const TenantVisitsScreen(useRequestEndpoint: false)),
        behavior: HitTestBehavior.opaque,
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 13.h),
          decoration: BoxDecoration(
            color: context.appColor(AppColors.mintLight, surface: true),
            borderRadius: BorderRadius.circular(16.r),
            border: Border.all(color: AppColors.tealAlpha19),
          ),
          child: Row(
            children: [
              Container(
                width: 34.r,
                height: 34.r,
                decoration: const BoxDecoration(
                  color: AppColors.whiteAlpha60,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.calendar_today_outlined,
                  color: context.appColor(AppColors.sokoonTeal),
                  size: 17.r,
                ),
              ),
              12.szW,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  spacing: 3.h,
                  children: [
                    AppText(
                      banner.isToday
                          ? LocaleKeys.tenantVisitBannerTitle
                          : LocaleKeys.tenantVisitBannerUpcoming,
                      style: AppTextStyles.bold14.copyWith(
                        color: context.appColor(AppColors.sokoonTeal),
                        fontSize: 14.sp,
                        height: 1.45,
                      ),
                    ),
                    if (propertyLabel.isNotEmpty)
                      AppText(
                        propertyLabel,
                        style: AppTextStyles.medium12.copyWith(
                          color: context.appColor(AppColors.sokoonNavy),
                          fontSize: 12.sp,
                          height: 1.45,
                        ),
                      ),
                    if (scheduleLabel.isNotEmpty)
                      AppText(
                        scheduleLabel,
                        style: AppTextStyles.medium12.copyWith(
                          color: context.appColor(AppColors.sokoonGray),
                          fontSize: 12.sp,
                          height: 1.45,
                        ),
                      ),
                  ],
                ),
              ),
              Icon(
                Directionality.of(context) == TextDirection.rtl
                    ? Icons.chevron_left_rounded
                    : Icons.chevron_right_rounded,
                color: context.appColor(AppColors.sokoonTeal),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
