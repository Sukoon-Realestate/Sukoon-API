part of '../../../imports.dart';

class OwnerCalendarVisitCard extends StatelessWidget {
  const OwnerCalendarVisitCard({super.key, required this.visit});

  final OwnerCalendarVisitContent visit;

  @override
  Widget build(BuildContext context) {
    final bool isAccepted = visit.status.isAccepted;

    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(14.r),
        boxShadow: const [
          BoxShadow(
            color: AppColors.shadowBlack04,
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 40.r,
            height: 40.r,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              color: AppColors.sokoonTeal,
              shape: BoxShape.circle,
            ),
            child: AppText(
              visit.tenantInitial,
              style: AppTextStyles.bold15.copyWith(
                color: AppColors.white,
                fontSize: 15.sp,
                height: 1.45,
              ),
            ),
          ),
          12.szW,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              spacing: 3.h,
              children: [
                AppText(
                  visit.tenant.name,
                  style: AppTextStyles.extraBold.copyWith(
                    color: AppColors.sokoonNavy,
                    fontSize: 14.sp,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                AppText(
                  visit.property.title,
                  style: AppTextStyles.medium12.copyWith(
                    color: AppColors.sokoonGray,
                    fontSize: 12.sp,
                    height: 1.45,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                AppText(
                  _formatOwnerCalendarVisitTime(context, visit.visitTime),
                  style: AppTextStyles.regular12.copyWith(
                    color: AppColors.sokoonGray,
                    fontSize: 12.sp,
                    height: 1.45,
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 5.h),
            decoration: BoxDecoration(
              color: isAccepted ? AppColors.greenPale : AppColors.amberPale,
              borderRadius: BorderRadius.circular(999.r),
            ),
            child: AppText(
              isAccepted
                  ? LocaleKeys.ownerCalendarConfirmed
                  : LocaleKeys.ownerCalendarPending,
              style: AppTextStyles.extraBold.copyWith(
                color: isAccepted ? AppColors.green : AppColors.amber,
                fontSize: 11.sp,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

String _formatOwnerCalendarVisitTime(BuildContext context, String value) {
  final List<String> parts = value.split(':');
  if (parts.length < 2) {
    return value;
  }
  final int? hour = int.tryParse(parts[0]);
  final int? minute = int.tryParse(parts[1]);
  if (hour == null || minute == null) {
    return value;
  }
  return MaterialLocalizations.of(
    context,
  ).formatTimeOfDay(TimeOfDay(hour: hour, minute: minute));
}
