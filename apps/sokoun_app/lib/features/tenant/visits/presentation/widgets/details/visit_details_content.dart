part of '../../../imports.dart';

class VisitDetailsContent extends StatelessWidget {
  const VisitDetailsContent({
    super.key,
    required this.visit,
    required this.onOpenChatPressed,
    required this.onCancelVisitPressed,
  });

  final TenantVisitContent visit;
  final VoidCallback onOpenChatPressed;
  final VoidCallback onCancelVisitPressed;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 24.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: EdgeInsets.symmetric(vertical: 16.h),
            child: Column(
              children: [
                Container(
                  width: 64.r,
                  height: 64.r,
                  alignment: Alignment.center,
                  decoration: const BoxDecoration(
                    color: AppColors.greenPale,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    Icons.check_circle_outline_rounded,
                    color: AppColors.green,
                    size: 29.r,
                  ),
                ),
                12.szH,
                Container(
                  padding: EdgeInsets.symmetric(
                    horizontal: 12.w,
                    vertical: 6.h,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.greenPale,
                    borderRadius: BorderRadius.circular(999.r),
                  ),
                  child: AppText(
                    LocaleKeys.tenantVisitStatusAcceptedWithCheck,
                    color: AppColors.green,
                    fontSize: 13.sp,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                8.szH,
                AppText(
                  LocaleKeys.tenantVisitConfirmedHeading,
                  color: AppColors.sokoonNavy,
                  fontSize: 18.sp,
                  fontWeight: FontWeight.w900,
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
          VisitSummaryCard(
            rows: [
              (
                label: LocaleKeys.tenantVisitSummaryProperty,
                value: visit.propertyTitle,
              ),
              (
                label: LocaleKeys.tenantVisitSummaryDay,
                value: visit.detailDate,
              ),
              (label: LocaleKeys.tenantVisitSummaryTime, value: visit.time),
              (label: LocaleKeys.tenantVisitOwnerLabel, value: visit.ownerName),
            ],
          ),
          12.szH,
          _VisitContactCard(visit: visit),
          14.szH,
          DefaultButton(
            key: const ValueKey('visit-details-open-chat'),
            onTap: onOpenChatPressed,
            title: LocaleKeys.tenantVisitOpenOwnerChat,
            color: AppColors.sokoonTeal,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 50.h,
            fontSize: 14.sp,
            fontWeight: FontWeight.w900,
          ),
          12.szH,
          DefaultButton(
            key: const ValueKey('visit-details-cancel'),
            onTap: onCancelVisitPressed,
            title: LocaleKeys.tenantVisitCancelVisit,
            color: AppColors.white,
            textColor: AppColors.sokoonNavy,
            borderColor: AppColors.sokoonBorder,
            borderRadius: BorderRadius.circular(14.r),
            height: 50.h,
            fontSize: 14.sp,
            fontWeight: FontWeight.w900,
          ),
        ],
      ),
    );
  }
}

class _VisitContactCard extends StatelessWidget {
  const _VisitContactCard({required this.visit});

  final TenantVisitContent visit;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(
            LocaleKeys.tenantVisitContactInfo,
            color: AppColors.sokoonNavy,
            fontSize: 14.sp,
            fontWeight: FontWeight.w900,
          ),
          10.szH,
          Container(
            padding: EdgeInsets.symmetric(horizontal: 13.w, vertical: 11.h),
            decoration: BoxDecoration(
              color: AppColors.greenPale,
              borderRadius: BorderRadius.circular(14.r),
            ),
            child: Row(
              children: [
                Icon(Icons.phone_outlined, color: AppColors.green, size: 16.r),
                9.szW,
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      AppText(
                        LocaleKeys.tenantVisitOwnerPhoneConfirmed,
                        color: AppColors.green,
                        fontSize: 11.sp,
                        fontWeight: FontWeight.w800,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      3.szH,
                      AppText(
                        visit.ownerPhone,
                        color: AppColors.green,
                        fontSize: 15.sp,
                        fontWeight: FontWeight.w900,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
