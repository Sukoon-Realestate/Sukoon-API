part of '../../../imports.dart';

class OwnerAcceptRequestSheet extends StatelessWidget {
  const OwnerAcceptRequestSheet({super.key, required this.request});

  final OwnerVisitRequestContent request;

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
            icon: Icons.check_circle_outline_rounded,
            title: LocaleKeys.ownerAcceptTitle,
            subtitle: LocaleKeys.ownerAcceptSubtitle,
            iconColor: context.appColor(AppColors.green),
            iconBackgroundColor: context.appColor(
              AppColors.greenPale,
              surface: true,
            ),
          ),
          18.szH,
          _OwnerAcceptSummary(request: request),
          20.szH,
          DefaultButton(
            onTap: () => Go.back(true),
            title: LocaleKeys.ownerAcceptConfirm,
            color: context.appColor(AppColors.greenStrong, surface: true),
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 52.h,
            textStyle: AppTextStyles.bold15.copyWith(
              fontSize: 15.sp,
              height: 1.45,
            ),
          ),
          12.szH,
          DefaultButton(
            onTap: () => Go.back(false),
            title: LocaleKeys.ownerRequestCancel,
            color: context.appColor(AppColors.white, surface: true),
            textColor: context.appColor(AppColors.sokoonNavy),
            borderColor: context.appColor(AppColors.sokoonBorder),
            borderRadius: BorderRadius.circular(14.r),
            height: 48.h,
            textStyle: AppTextStyles.extraBold.copyWith(fontSize: 14.sp),
          ),
        ],
      ),
    );
  }
}

class _OwnerAcceptSummary extends StatelessWidget {
  const _OwnerAcceptSummary({required this.request});

  final OwnerVisitRequestContent request;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.grayBackground, surface: true),
        borderRadius: BorderRadius.circular(14.r),
      ),
      child: Column(
        spacing: 10.h,
        children: [
          _OwnerAcceptSummaryRow(
            label: LocaleKeys.ownerVisitTenantLabel,
            value: request.name,
          ),
          _OwnerAcceptSummaryRow(
            label: LocaleKeys.ownerVisitRequestDate,
            value: request.detailDate,
          ),
          _OwnerAcceptSummaryRow(
            label: LocaleKeys.ownerVisitRequestTime,
            value: request.time,
          ),
        ],
      ),
    );
  }
}

class _OwnerAcceptSummaryRow extends StatelessWidget {
  const _OwnerAcceptSummaryRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Row(
      spacing: 12.w,
      children: [
        AppText(
          label,
          style: AppTextStyles.regular13.copyWith(
            color: context.appColor(AppColors.sokoonGray),
            fontSize: 13.sp,
            height: 1.45,
          ),
        ),
        Expanded(
          child: AppText(
            value,
            style: AppTextStyles.extraBold13.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
              fontSize: 13.sp,
              height: 1.45,
            ),
            textAlign: TextAlign.end,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}

class _OwnerSheetHandle extends StatelessWidget {
  const _OwnerSheetHandle();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 36.w,
      height: 4.h,
      decoration: BoxDecoration(
        color: context.appColor(AppColors.grayPale, surface: true),
        borderRadius: BorderRadius.circular(2.r),
      ),
    ).centerWidget;
  }
}

class _OwnerDecisionSheetHeader extends StatelessWidget {
  const _OwnerDecisionSheetHeader({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.iconColor,
    required this.iconBackgroundColor,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final Color iconColor;
  final Color iconBackgroundColor;

  @override
  Widget build(BuildContext context) {
    return Row(
      spacing: 10.w,
      children: [
        Container(
          width: 40.r,
          height: 40.r,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: context.appColor(iconBackgroundColor, surface: true),
            borderRadius: BorderRadius.circular(12.r),
          ),
          child: Icon(icon, color: context.appColor(iconColor), size: 22.r),
        ),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            spacing: 3.h,
            children: [
              AppText(
                title,
                style: AppTextStyles.bold16.copyWith(
                  color: context.appColor(AppColors.sokoonNavy),
                  fontSize: 16.sp,
                  height: 1.45,
                ),
              ),
              AppText(
                subtitle,
                style: AppTextStyles.regular12.copyWith(
                  color: context.appColor(AppColors.sokoonGray),
                  fontSize: 12.sp,
                  height: 1.45,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
