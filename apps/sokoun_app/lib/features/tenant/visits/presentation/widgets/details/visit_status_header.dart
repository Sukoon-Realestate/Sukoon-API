part of '../../../imports.dart';

class VisitStatusHeader extends StatelessWidget {
  const VisitStatusHeader({super.key, required this.visit});

  final TenantVisitContent visit;

  Color get _foregroundColor {
    if (visit.status.isAccepted) return AppColors.green;
    if (visit.status.isPending) return AppColors.amber;
    return AppColors.red;
  }

  Color get _backgroundColor {
    if (visit.status.isAccepted) return AppColors.greenPale;
    if (visit.status.isPending) return AppColors.amberPale;
    return AppColors.redPale;
  }

  IconData get _icon {
    if (visit.status.isAccepted) return Icons.check_circle_outline_rounded;
    if (visit.status.isPending) return Icons.schedule_rounded;
    return Icons.cancel_outlined;
  }

  String get _title {
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
            color: _backgroundColor,
            shape: BoxShape.circle,
          ),
          child: Icon(_icon, color: _foregroundColor, size: 29.r),
        ),
        12.szH,
        Container(
          padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 6.h),
          decoration: BoxDecoration(
            color: _backgroundColor,
            borderRadius: BorderRadius.circular(999.r),
          ),
          child: AppText(
            visit.resolvedStatusText,
            color: _foregroundColor,
            fontSize: 13.sp,
            fontWeight: FontWeight.w900,
            maxLines: 1,
          ),
        ),
        8.szH,
        AppText(
          _title,
          color: AppColors.sokoonNavy,
          fontSize: 18.sp,
          fontWeight: FontWeight.w900,
          textAlign: TextAlign.center,
          maxLines: 2,
        ),
      ],
    ).paddingSymmetric(vertical: 16.h);
  }
}
