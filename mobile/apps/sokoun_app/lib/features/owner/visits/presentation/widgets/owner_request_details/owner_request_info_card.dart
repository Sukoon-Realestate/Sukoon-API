part of '../../../imports.dart';

class OwnerRequestInfoCard extends StatelessWidget {
  const OwnerRequestInfoCard({super.key, required this.request});

  final OwnerVisitRequestDetailsContent request;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
      ),
      child: Column(
        children: [
          Row(
            spacing: 12.w,
            children: [
              OwnerTenantAvatar(
                name: request.tenant.name,
                avatarUrl: request.tenant.avatar,
                size: 56,
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      spacing: 7.w,
                      children: [
                        Flexible(
                          child: AppText(
                            request.tenant.name,
                            style: AppTextStyles.bold16.copyWith(
                              color: context.appColor(AppColors.sokoonNavy),
                              fontSize: 16.sp,
                              height: 1.45,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (request.tenant.isVerified)
                          const OwnerVerifiedBadge(),
                      ],
                    ),
                    4.szH,
                    if (request.tenant.membershipLabel.isNotEmpty)
                      AppText(
                        request.tenant.membershipLabel,
                        style: AppTextStyles.regular12.copyWith(
                          color: context.appColor(AppColors.sokoonGray),
                          fontSize: 12.sp,
                          height: 1.45,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                  ],
                ),
              ),
            ],
          ),
          12.szH,
          _OwnerRequestInfoRow(
            label: LocaleKeys.ownerVisitRequestedProperty,
            value: request.displayProperty,
          ),
          _OwnerRequestInfoRow(
            label: LocaleKeys.ownerVisitRequestDate,
            value: request.displayDate,
          ),
          _OwnerRequestInfoRow(
            label: LocaleKeys.ownerVisitRequestTime,
            value: request.displayTime,
            showDivider: false,
          ),
          8.szH,
          _OwnerRequestStatusPill(request: request),
        ],
      ),
    );
  }
}

class _OwnerRequestStatusPill extends StatelessWidget {
  const _OwnerRequestStatusPill({required this.request});

  final OwnerVisitRequestDetailsContent request;

  Color get _backgroundColor {
    if (request.status.isAccepted || request.status.isCompleted) {
      return AppColors.greenPale;
    }
    if (request.status.isRejected) return AppColors.redPale;
    if (request.status.isPending || request.status.isNewRequest) {
      return AppColors.amberPale;
    }
    return AppColors.grayBackground;
  }

  Color get _foregroundColor {
    if (request.status.isAccepted || request.status.isCompleted) {
      return AppColors.greenStrong;
    }
    if (request.status.isRejected) return AppColors.sokoonRose;
    if (request.status.isPending || request.status.isNewRequest) {
      return AppColors.brown;
    }
    return AppColors.sokoonGray;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 9.h),
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: context.appColor(_backgroundColor, surface: true),
        borderRadius: BorderRadius.circular(10.r),
      ),
      child: AppText(
        request.displayStatus,
        style: AppTextStyles.extraBold13.copyWith(
          color: context.appColor(_foregroundColor),
          fontSize: 13.sp,
          height: 1.45,
        ),
        textAlign: TextAlign.center,
        maxLines: 2,
      ),
    );
  }
}

class _OwnerRequestInfoRow extends StatelessWidget {
  const _OwnerRequestInfoRow({
    required this.label,
    required this.value,
    this.showDivider = true,
  });

  final String label;
  final String value;
  final bool showDivider;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(vertical: 10.h),
      decoration: BoxDecoration(
        border: showDivider
            ? Border(
                bottom: BorderSide(
                  color: context.appColor(AppColors.sokoonBorder),
                ),
              )
            : null,
      ),
      child: Row(
        spacing: 12.w,
        children: [
          AppText(
            label,
            style: AppTextStyles.regular12.copyWith(
              color: context.appColor(AppColors.sokoonGray),
              fontSize: 12.sp,
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
              maxLines: 2,
            ),
          ),
        ],
      ),
    );
  }
}
