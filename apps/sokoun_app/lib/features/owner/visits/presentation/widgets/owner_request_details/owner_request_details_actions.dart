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
    Go.to(StartConversationScreen(userId: request.tenant.id));
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
            color: AppColors.greenStrong,
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
                ? const _OwnerActionLoader(color: AppColors.red)
                : null,
            color: AppColors.white,
            textColor: AppColors.red,
            borderColor: AppColors.red,
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
          color: canOpenChat ? AppColors.bluePale : AppColors.grayBackground,
          textColor: canOpenChat ? AppColors.blue : AppColors.sokoonMuted,
          borderRadius: BorderRadius.circular(16.r),
          height: 50.h,
          textStyle: AppTextStyles.bold14.copyWith(
            fontSize: 14.sp,
            height: 1.45,
          ),
        ),
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
      child: CustomLoading.showLoadingView(color: color, size: 20.r),
    );
  }
}
