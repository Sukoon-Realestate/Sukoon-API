part of '../../../imports.dart';

class VisitConfirmationContent extends StatelessWidget {
  const VisitConfirmationContent({
    super.key,
    this.message = '',
    required this.property,
    required this.selectedDay,
    required this.selectedTime,
  });

  final String message;
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
          SokounReveal(
            beginScale: .88,
            child: Container(
              width: 96.r,
              height: 96.r,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: context.appColor(AppColors.greenPale, surface: true),
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.check_circle_outline_rounded,
                color: context.appColor(AppColors.green),
                size: 44.r,
              ),
            ),
          ).centerWidget,
          20.szH,
          AppText(
            message,
            style: AppTextStyles.bold.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
              fontSize: 23.sp,
            ),
            textAlign: TextAlign.center,
            maxLines: 2,
          ),
          8.szH,
          AppText(
            LocaleKeys.tenantVisitConfirmedDescription,
            style: AppTextStyles.regular14.copyWith(
              color: context.appColor(AppColors.sokoonGray),
              fontSize: 14.sp,
              height: 1.5,
            ),
            textAlign: TextAlign.center,
            maxLines: 3,
          ),
          24.szH,
          SokounReveal(
            delay: const Duration(milliseconds: 80),
            child: VisitSummaryCard(
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
          ),
          24.szH,
          DefaultButton(
            onTap: () => WorkspaceNavigation.open(
              workspace: AppWorkspace.tenant,
              tab: WorkspaceTab.visits,
            ),
            title: LocaleKeys.tenantVisitFollowRequests,
            color: context.appColor(AppColors.sokoonTeal, surface: true),
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 50.h,
            textStyle: AppTextStyles.bold15.copyWith(
              fontSize: 15.sp,
              height: 1.45,
            ),
          ),
          12.szH,
          DefaultButton(
            onTap: () => Go.tryBackUntil(
              (route) =>
                  route.isFirst ||
                  route.settings.name == '$TenantSearchResultsScreen' ||
                  route.settings.name == '$TenantSearchScreen',
            ),
            title: LocaleKeys.tenantVisitBackToSearch,
            color: context.appColor(AppColors.white, surface: true),
            textColor: context.appColor(AppColors.sokoonNavy),
            borderColor: context.appColor(AppColors.sokoonBorder),
            borderRadius: BorderRadius.circular(14.r),
            height: 50.h,
            textStyle: AppTextStyles.bold15.copyWith(
              fontSize: 15.sp,
              height: 1.45,
            ),
          ),
        ],
      ),
    ).centerWidget;
  }
}
