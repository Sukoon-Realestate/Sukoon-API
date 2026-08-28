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
              visit.initial,
              color: AppColors.white,
              fontSize: 15.sp,
              fontWeight: FontWeight.w900,
            ),
          ),
          12.szW,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppText(
                  visit.name,
                  color: AppColors.sokoonNavy,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w800,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                3.szH,
                AppText(
                  visit.time,
                  color: AppColors.sokoonGray,
                  fontSize: 12.sp,
                  fontWeight: FontWeight.w400,
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
              color: isAccepted ? AppColors.green : AppColors.amber,
              fontSize: 11.sp,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}
