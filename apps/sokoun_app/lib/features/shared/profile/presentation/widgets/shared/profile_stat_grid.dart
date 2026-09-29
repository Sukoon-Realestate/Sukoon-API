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
    return Row(
      children: stats
          .map(
            (stat) => Expanded(
              child: Container(
                constraints: BoxConstraints(minHeight: withCards ? 82.h : 54.h),
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 10.h),
                decoration: BoxDecoration(
                  color: withCards
                      ? AppColors.white
                      : AppColors.scaffoldBackground,
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
                  children: [
                    AppText(
                      stat.value,
                      style: AppTextStyles.bold.copyWith(
                        color: valueColor,
                        fontSize: withCards ? 22.sp : 16.sp,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    3.szH,
                    AppText(
                      stat.label,
                      style: AppTextStyles.medium.copyWith(
                        color: AppColors.sokoonGray,
                        fontSize: withCards ? 10.sp : 11.sp,
                      ),
                      textAlign: TextAlign.center,
                      maxLines: 2,
                    ),
                  ],
                ),
              ),
            ),
          )
          .toList(growable: false)
          .joinWith(10.szW),
    );
  }
}
