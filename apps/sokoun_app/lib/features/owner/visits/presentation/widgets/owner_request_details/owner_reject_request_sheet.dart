part of '../../../imports.dart';

class OwnerRejectRequestSheet extends StatelessWidget {
  const OwnerRejectRequestSheet({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(24.w, 12.h, 24.w, 28.h),
      decoration: BoxDecoration(
        color: AppColors.white,
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
            iconColor: AppColors.red,
            iconBackgroundColor: AppColors.redPale,
          ),
          22.szH,
          DefaultButton(
            onTap: () => Go.back(true),
            title: LocaleKeys.ownerRejectConfirm,
            color: AppColors.red,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 52.h,
            fontSize: 15.sp,
            fontWeight: FontWeight.w900,
          ),
        ],
      ),
    );
  }
}
