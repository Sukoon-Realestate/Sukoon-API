part of '../../../imports.dart';

class OwnerRejectRequestSheet extends StatelessWidget {
  const OwnerRejectRequestSheet({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(24.w, 12.h, 24.w, 28.h),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.vertical(top: Radius.circular(24.r)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const _OwnerSheetHandle(),
          18.szH,
          _OwnerDecisionSheetHeader(
            icon: Icons.close_rounded,
            title: LocaleKeys.ownerRejectTitle,
            subtitle: LocaleKeys.ownerRejectConfirmation,
            iconColor: context.appColor(AppColors.red),
            iconBackgroundColor: context.appColor(
              AppColors.redPale,
              surface: true,
            ),
          ),
          12.szH,
          AppText(
            LocaleKeys.ownerRejectTimingReason,
            style: AppTextStyles.regular14,
          ),
          22.szH,
          DefaultButton(
            onTap: () => Go.back(true),
            title: LocaleKeys.ownerRejectConfirm,
            color: context.appColor(AppColors.red, surface: true),
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 52.h,
            textStyle: AppTextStyles.bold15.copyWith(
              fontSize: 15.sp,
              height: 1.45,
            ),
          ),
        ],
      ),
    );
  }
}
