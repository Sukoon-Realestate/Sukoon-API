part of '../../../imports.dart';

class OwnerRequestDetailsActions extends StatelessWidget {
  const OwnerRequestDetailsActions({
    super.key,
    required this.request,
    required this.isAccepting,
    required this.isRejecting,
    required this.onAcceptPressed,
    required this.onRejectPressed,
  });

  final OwnerVisitRequestDetailsContent request;
  final bool isAccepting;
  final bool isRejecting;
  final VoidCallback onAcceptPressed;
  final VoidCallback onRejectPressed;

  void _openChat() {
    if (request.tenant.id.isEmpty) return;
    Go.to(
      StartConversationScreen(
        userId: request.tenant.id,
        rentalContext: request.rentalSelection,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final bool isUpdating = isAccepting || isRejecting;
    final bool canOpenChat =
        request.actions.canChat && request.tenant.id.isNotEmpty;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (request.actions.canAccept)
          DefaultButton(
            onTap: isUpdating ? null : onAcceptPressed,
            title: LocaleKeys.ownerVisitAcceptWithCheck,
            customChild: isAccepting
                ? const _OwnerActionLoader(color: AppColors.white)
                : null,
            color: context.appColor(AppColors.greenStrong, surface: true),
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(16.r),
            height: 52.h,
            textStyle: AppTextStyles.bold15.copyWith(
              fontSize: 15.sp,
              height: 1.45,
            ),
          ),
        if (request.actions.canAccept && request.actions.canReject) 12.szH,
        if (request.actions.canReject)
          DefaultButton(
            onTap: isUpdating ? null : onRejectPressed,
            title: LocaleKeys.ownerVisitRejectRequest,
            customChild: isRejecting
                ? _OwnerActionLoader(color: context.appColor(AppColors.red))
                : null,
            color: context.appColor(AppColors.white, surface: true),
            textColor: context.appColor(AppColors.red),
            borderColor: context.appColor(AppColors.red),
            borderRadius: BorderRadius.circular(16.r),
            height: 50.h,
            textStyle: AppTextStyles.bold14.copyWith(
              fontSize: 14.sp,
              height: 1.45,
            ),
          ),
        if (request.actions.canAccept || request.actions.canReject) 12.szH,
        DefaultButton(
          onTap: isUpdating || !canOpenChat ? null : _openChat,
          title: LocaleKeys.ownerVisitOpenChat,
          color: canOpenChat
              ? context.appColor(AppColors.bluePale, surface: true)
              : context.appColor(AppColors.grayBackground, surface: true),
          textColor: canOpenChat
              ? context.appColor(AppColors.blue)
              : context.appColor(AppColors.sokoonMuted),
          borderRadius: BorderRadius.circular(16.r),
          height: 50.h,
          textStyle: AppTextStyles.bold14.copyWith(
            fontSize: 14.sp,
            height: 1.45,
          ),
        ),
        if (request.property.id.isNotEmpty && request.tenant.id.isNotEmpty) ...[
          12.szH,
          TenancyInviteEntry(
            propertyId: request.property.id,
            propertyTitle: request.displayProperty,
            tenantId: request.tenant.id,
            tenantName: request.tenant.name,
            enabled: !isUpdating,
          ),
        ],
      ],
    );
  }
}

class _OwnerActionLoader extends StatelessWidget {
  const _OwnerActionLoader({required this.color});

  final Color color;

  @override
  Widget build(BuildContext context) {
    return SizedBox.square(
      dimension: 20.r,
      child: CustomLoading.showLoadingView(
        color: context.appColor(color),
        size: 20.r,
      ),
    );
  }
}
