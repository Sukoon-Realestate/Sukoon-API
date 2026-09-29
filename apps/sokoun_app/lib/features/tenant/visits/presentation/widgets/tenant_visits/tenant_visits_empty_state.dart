part of '../../../imports.dart';

class TenantVisitsEmptyState extends StatelessWidget {
  const TenantVisitsEmptyState({
    super.key,
    required this.isFiltered,
    required this.onClearFiltersPressed,
  });

  final bool isFiltered;
  final VoidCallback onClearFiltersPressed;

  @override
  Widget build(BuildContext context) {
    final bool reduceMotion = MediaQuery.of(context).disableAnimations;
    final String title = isFiltered
        ? LocaleKeys.tenantVisitsNoResults
        : LocaleKeys.tenantVisitsEmptyTitle;
    final String description = isFiltered
        ? LocaleKeys.tenantVisitsFilterEmptyDescription
        : LocaleKeys.tenantVisitsEmptyDescription;

    return Semantics(
      label: title,
      child: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 28.w, vertical: 20.h),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ExcludeSemantics(
              child: Assets.lottie.emptyBox.lottie(
                package: 'melos_core',
                width: 132.r,
                height: 112.r,
                animate: !reduceMotion,
                repeat: false,
                fit: BoxFit.contain,
              ),
            ),
            8.szH,
            AppText(
              title,
              style: AppTextStyles.bold.copyWith(
                color: AppColors.sokoonNavy,
                fontSize: 17.sp,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
            ),
            6.szH,
            AppText(
              description,
              style: AppTextStyles.medium13.copyWith(
                color: AppColors.sokoonGray,
                fontSize: 13.sp,
                height: 1.45,
              ),
              textAlign: TextAlign.center,
              maxLines: 3,
            ),
            18.szH,
            DefaultButton(
              onTap: isFiltered
                  ? onClearFiltersPressed
                  : () => Go.to(const TenantSearchScreen()),
              title: isFiltered
                  ? LocaleKeys.tenantVisitsShowAll
                  : LocaleKeys.tenantVisitsBrowseProperties,
              color: AppColors.sokoonTeal,
              textColor: AppColors.white,
              borderRadius: BorderRadius.circular(12.r),
              height: 45.h,
              width: double.infinity,
              textStyle: AppTextStyles.extraBold.copyWith(fontSize: 14.sp),
            ),
          ],
        ),
      ).centerWidget,
    );
  }
}
