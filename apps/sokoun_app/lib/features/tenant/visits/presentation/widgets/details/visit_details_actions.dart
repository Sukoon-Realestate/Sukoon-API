part of '../../../imports.dart';

class VisitDetailsActions extends StatelessWidget {
  const VisitDetailsActions({super.key, required this.visit});

  final TenantVisitContent visit;

  void _openChat() {
    if (visit.ownerId.isEmpty) return;
    Go.to(StartConversationScreen(userId: visit.ownerId));
  }

  @override
  Widget build(BuildContext context) {
    if (visit.status.isRejected) {
      return DefaultButton(
        onTap: () => Go.to(const TenantSearchScreen()),
        title: LocaleKeys.tenantVisitFindAlternative,
        color: AppColors.sokoonTeal,
        textColor: AppColors.white,
        borderRadius: BorderRadius.circular(14.r),
        height: 50.h,
        textStyle: AppTextStyles.bold14.copyWith(fontSize: 14.sp, height: 1.45),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 12.h,
      children: [
        if (visit.status.isAccepted)
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
        DefaultButton(
          onTap: () => Go.back(true),
          title: visit.status.isPending
              ? LocaleKeys.tenantVisitCancelRequest
              : LocaleKeys.tenantVisitCancelVisit,
          color: AppColors.white,
          textColor: AppColors.sokoonNavy,
          borderColor: AppColors.sokoonBorder,
          borderRadius: BorderRadius.circular(14.r),
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
