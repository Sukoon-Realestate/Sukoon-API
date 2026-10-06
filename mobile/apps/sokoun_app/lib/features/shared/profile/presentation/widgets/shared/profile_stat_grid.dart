part of '../../../imports.dart';

class ProfileStat {
  const ProfileStat({required this.value, required this.label});

  final String value;
  final String label;
}

class ProfileStatGrid extends StatelessWidget {
  const ProfileStatGrid({
    super.key,
    required this.stats,
    this.valueColor = AppColors.sokoonNavy,
    this.withCards = false,
  });

  final List<ProfileStat> stats;
  final Color valueColor;
  final bool withCards;

  @override
  Widget build(BuildContext context) {
    return SokounAdaptiveGrid(
      minimumWidth: 72,
      maximumColumns: 3,
      gap: 10.r,
      children: stats
          .map(
            (stat) => Container(
              constraints: BoxConstraints(minHeight: withCards ? 82.h : 54.h),
              padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 10.h),
              decoration: BoxDecoration(
                color: withCards
                    ? context.appColor(AppColors.white, surface: true)
                    : context.appColor(
                        AppColors.scaffoldBackground,
                        surface: true,
                      ),
                borderRadius: BorderRadius.circular(14.r),
                boxShadow: withCards
                    ? const [
                        BoxShadow(
                          color: AppColors.shadowBlack04,
                          blurRadius: 8,
                          offset: Offset(0, 2),
                        ),
                      ]
                    : null,
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                spacing: 3.h,
                children: [
                  AppText(
                    stat.value,
                    style: AppTextStyles.bold.copyWith(
                      color: context.appColor(valueColor),
                      fontSize: withCards ? 22.sp : 16.sp,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  AppText(
                    stat.label,
                    style: AppTextStyles.medium.copyWith(
                      color: context.appColor(AppColors.sokoonGray),
                      fontSize: withCards ? 10.sp : 11.sp,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          )
          .toList(growable: false),
    );
  }
}
