part of '../../../imports.dart';

class VisitStatusHeader extends StatelessWidget {
  const VisitStatusHeader({super.key, required this.visit});

  final TenantVisitContent visit;

  String get _title {
    if (visit.status.isCompleted || visit.status.isCanceled) {
      return visit.status.label;
    }
    if (visit.status.isAccepted) {
      return LocaleKeys.tenantVisitConfirmedHeading;
    }
    if (visit.status.isPending) {
      return LocaleKeys.tenantVisitPendingHeading;
    }
    return LocaleKeys.tenantVisitRejectedHeading;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 64.r,
          height: 64.r,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: visit.status.backgroundColor,
            shape: BoxShape.circle,
          ),
          child: Icon(
            visit.status.statusIcon,
            color: visit.status.foregroundColor,
            size: 29.r,
          ),
        ),
        12.szH,
        Container(
          padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 6.h),
          decoration: BoxDecoration(
            color: visit.status.backgroundColor,
            borderRadius: BorderRadius.circular(999.r),
          ),
          child: AppText(
            visit.resolvedStatusText,
            style: AppTextStyles.bold13.copyWith(
              color: visit.status.foregroundColor,
              fontSize: 13.sp,
              height: 1.45,
            ),
            maxLines: 1,
          ),
        ),
        8.szH,
        AppText(
          _title,
          style: AppTextStyles.bold.copyWith(
            color: AppColors.sokoonNavy,
            fontSize: 18.sp,
          ),
          textAlign: TextAlign.center,
          maxLines: 2,
        ),
      ],
    ).paddingSymmetric(vertical: 16.h);
  }
}
