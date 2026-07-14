import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_property_content.dart';

import '../widgets/tenant_visit_confirmed/imports.dart';

class TenantVisitConfirmedScreen extends StatelessWidget {
  const TenantVisitConfirmedScreen({
    super.key,
    required this.property,
    required this.selectedDay,
    required this.selectedTime,
  });

  final TenantPropertyDetailsContent property;
  final TenantVisitDayContent selectedDay;
  final String selectedTime;

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 32.w),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Center(
                  child: Container(
                    width: 96.r,
                    height: 96.r,
                    alignment: Alignment.center,
                    decoration: const BoxDecoration(
                      color: AppColors.greenPale,
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      Icons.check_circle_outline_rounded,
                      color: AppColors.green,
                      size: 44.r,
                    ),
                  ),
                ),
                20.szH,
                AppText(
                  'تم إرسال طلب الزيارة!',
                  color: AppColors.sokoonNavy,
                  fontSize: 23.sp,
                  fontWeight: FontWeight.w900,
                  textAlign: TextAlign.center,
                ),
                8.szH,
                AppText(
                  'المالك سيرد عليك خلال 24 ساعة. هتلاقي تحديثات في الإشعارات.',
                  color: AppColors.sokoonGray,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w500,
                  textAlign: TextAlign.center,
                  maxLines: 2,
                ),
                24.szH,
                VisitSummaryCard(
                  rows: [
                    VisitSummaryRowData(
                      label: 'العقار',
                      value: property.shortTitle,
                    ),
                    VisitSummaryRowData(
                      label: 'اليوم',
                      value:
                          '${selectedDay.weekday} ${selectedDay.day} ${selectedDay.month}',
                    ),
                    VisitSummaryRowData(label: 'الوقت', value: selectedTime),
                    const VisitSummaryRowData(
                      label: 'الحالة',
                      value: 'بانتظار رد المالك',
                    ),
                  ],
                ),
                24.szH,
                VisitActionButton(label: 'متابعة طلباتي', onTap: () {}),
                12.szH,
                VisitActionButton(
                  label: 'ارجع للبحث',
                  isOutline: true,
                  onTap: () =>
                      Navigator.of(context).popUntil((route) => route.isFirst),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
