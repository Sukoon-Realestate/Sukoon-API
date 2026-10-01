part of '../../../imports.dart';

class VisitDetailsActions extends StatelessWidget {
  const VisitDetailsActions({
    super.key,
    required this.visit,
    this.onCancel,
    this.onReview,
  });

  final TenantVisitContent visit;
  final Future<void> Function()? onCancel;
  final Future<void> Function()? onReview;

  void _openChat() {
    if (visit.ownerId.isEmpty) return;
    Go.to(StartConversationScreen(userId: visit.ownerId));
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 12.h,
      children: [
        if (visit.canFindAlternative)
          DefaultButton(
            onTap: () => Go.to(const TenantSearchScreen()),
            title: LocaleKeys.tenantVisitFindAlternative,
            color: AppColors.sokoonTeal,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 50.h,
            textStyle: AppTextStyles.bold14.copyWith(
              fontSize: 14.sp,
              height: 1.45,
            ),
          ),
        if (visit.canChat)
          DefaultButton(
            onTap: visit.ownerId.isEmpty ? null : _openChat,
            title: LocaleKeys.tenantVisitOpenOwnerChat,
            color: AppColors.sokoonTeal,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 50.h,
            textStyle: AppTextStyles.bold14.copyWith(
              fontSize: 14.sp,
              height: 1.45,
            ),
          ),
        if (visit.canReview && onReview != null)
          AppLoadingButton(
            asyncCall: (_) => onReview!(),
            title: LocaleKeys.tenantVisitRateAction,
          ),
        if (visit.canCancel && onCancel != null)
          AppLoadingButton(
            asyncCall: (_) => onCancel!(),
            title: visit.status.isPending
                ? LocaleKeys.tenantVisitCancelRequest
                : LocaleKeys.tenantVisitCancelVisit,
            buttonColor: AppColors.white,
            textColor: AppColors.sokoonRose,
          ),
      ],
    );
  }
}
