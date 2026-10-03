part of '../../../imports.dart';

class OwnerCalendarVisitCard extends StatelessWidget {
  const OwnerCalendarVisitCard({super.key, required this.visit});

  final OwnerCalendarVisitContent visit;

  @override
  Widget build(BuildContext context) {
    final bool isAccepted = visit.status.isAccepted;
    final Color statusColor = isAccepted || visit.status.isCompleted
        ? AppColors.greenStrong
        : visit.status.isRejected
        ? AppColors.sokoonRose
        : visit.status.canDecide
        ? AppColors.brown
        : AppColors.sokoonGray;
    final Color statusBackground = isAccepted || visit.status.isCompleted
        ? AppColors.greenPale
        : visit.status.isRejected
        ? AppColors.redPale
        : visit.status.canDecide
        ? AppColors.amberPale
        : AppColors.grayBackground;

    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(14.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Row(
        children: [
          OwnerTenantAvatar(
            name: visit.tenant.name,
            initial: visit.tenantInitial,
            avatarUrl: visit.tenant.avatar,
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
                  visit.timeFormatted.trim().isNotEmpty
                      ? visit.timeFormatted
                      : _formatOwnerCalendarVisitTime(context, visit.visitTime),
                  style: AppTextStyles.regular12.copyWith(
                    color: AppColors.sokoonGray,
                    fontSize: 12.sp,
                    height: 1.45,
                  ),
                ),
                Container(
                  padding: EdgeInsets.symmetric(
                    horizontal: 10.w,
                    vertical: 5.h,
                  ),
                  decoration: BoxDecoration(
                    color: statusBackground,
                    borderRadius: BorderRadius.circular(999.r),
                  ),
                  child: AppText(
                    visit.statusLabel.trim().isNotEmpty
                        ? visit.statusLabel
                        : isAccepted
                        ? LocaleKeys.ownerCalendarConfirmed
                        : visit.status.label,
                    style: AppTextStyles.extraBold.copyWith(
                      color: statusColor,
                      fontSize: 12.sp,
                    ),
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
