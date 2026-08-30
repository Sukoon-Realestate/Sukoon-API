part of '../../../imports.dart';

class OwnerPropertiesEmptyState extends StatelessWidget {
  const OwnerPropertiesEmptyState({super.key, required this.onAddPressed});

  final VoidCallback onAddPressed;

  @override
  Widget build(BuildContext context) {
    final bool reduceMotion = MediaQuery.of(context).disableAnimations;
    return Center(
      child: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 36.w, vertical: 24.h),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ExcludeSemantics(
              child: Assets.lottie.emptyBox.lottie(
                width: 144.r,
                height: 118.r,
                animate: !reduceMotion,
                repeat: false,
                fit: BoxFit.contain,
                package: 'melos_core',
              ),
            ),
            10.szH,
            AppText(
              LocaleKeys.ownerPropertiesEmptyTitle,
              color: AppColors.sokoonNavy,
              fontSize: 18.sp,
              fontWeight: FontWeight.w900,
              textAlign: TextAlign.center,
              maxLines: 2,
            ),
            7.szH,
            AppText(
              LocaleKeys.ownerPropertiesEmptyDescription,
              color: AppColors.sokoonGray,
              fontSize: 13.sp,
              fontWeight: FontWeight.w500,
              textAlign: TextAlign.center,
              maxLines: 3,
            ),
            20.szH,
            DefaultButton(
              onTap: onAddPressed,
              title: LocaleKeys.ownerPropertiesAdd,
              color: AppColors.sokoonTeal,
              textColor: AppColors.white,
              borderRadius: BorderRadius.circular(12.r),
              height: 46.h,
              width: double.infinity,
              fontSize: 14.sp,
              fontWeight: FontWeight.w800,
            ),
          ],
        ),
      ),
    );
  }
}
