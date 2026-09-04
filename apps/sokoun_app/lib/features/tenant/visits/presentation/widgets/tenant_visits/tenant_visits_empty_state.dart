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
              color: AppColors.sokoonNavy,
              fontSize: 17.sp,
              fontWeight: FontWeight.w900,
              textAlign: TextAlign.center,
              maxLines: 2,
            ),
            6.szH,
            AppText(
              description,
              color: AppColors.sokoonGray,
              fontSize: 13.sp,
              fontWeight: FontWeight.w500,
              textAlign: TextAlign.center,
              maxLines: 3,
            ),
            18.szH,
            DefaultButton(
              key: const ValueKey('tenant-visits-empty-action'),
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
              fontSize: 14.sp,
              fontWeight: FontWeight.w800,
            ),
          ],
        ),
      ).centerWidget,
    );
  }
}
