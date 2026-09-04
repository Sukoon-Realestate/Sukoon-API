part of '../../../imports.dart';

class VisitConfirmationContent extends StatelessWidget {
  const VisitConfirmationContent({
    super.key,
    required this.property,
    required this.selectedDay,
    required this.selectedTime,
  });

  final VisitPropertyContent property;
  final VisitDayContent selectedDay;
  final VisitTimeSlotContent selectedTime;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.symmetric(horizontal: 32.w, vertical: 28.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
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
          ).centerWidget,
          20.szH,
          AppText(
            LocaleKeys.tenantVisitConfirmedTitle,
            color: AppColors.sokoonNavy,
            fontSize: 23.sp,
            fontWeight: FontWeight.w900,
            textAlign: TextAlign.center,
            maxLines: 2,
          ),
          8.szH,
          AppText(
            LocaleKeys.tenantVisitConfirmedDescription,
            color: AppColors.sokoonGray,
            fontSize: 14.sp,
            height: 1.5,
            textAlign: TextAlign.center,
            maxLines: 3,
          ),
          24.szH,
          VisitSummaryCard(
            rows: [
              (
                label: LocaleKeys.tenantVisitSummaryProperty,
                value: property.title,
              ),
              (
                label: LocaleKeys.tenantVisitSummaryDay,
                value: selectedDay.fullLabel,
              ),
              (
                label: LocaleKeys.tenantVisitSummaryTime,
                value: selectedTime.label,
              ),
              (
                label: LocaleKeys.tenantVisitSummaryStatus,
                value: LocaleKeys.tenantVisitPendingOwnerResponse,
              ),
            ],
          ),
          24.szH,
          DefaultButton(
            key: const ValueKey('visit-follow-requests'),
            onTap: () => Go.off(const TenantVisitsScreen()),
            title: LocaleKeys.tenantVisitFollowRequests,
            color: AppColors.sokoonTeal,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 50.h,
            fontSize: 15.sp,
            fontWeight: FontWeight.w900,
          ),
          12.szH,
          DefaultButton(
            key: const ValueKey('visit-back-search'),
            onTap: () => Go.off(const TenantSearchScreen()),
            title: LocaleKeys.tenantVisitBackToSearch,
            color: AppColors.white,
            textColor: AppColors.sokoonNavy,
            borderColor: AppColors.sokoonBorder,
            borderRadius: BorderRadius.circular(14.r),
            height: 50.h,
            fontSize: 15.sp,
            fontWeight: FontWeight.w900,
          ),
        ],
      ),
    ).centerWidget;
  }
}
