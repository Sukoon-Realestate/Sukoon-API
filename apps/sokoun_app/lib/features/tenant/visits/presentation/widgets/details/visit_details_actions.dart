part of '../../../imports.dart';

class VisitDetailsActions extends StatelessWidget {
  const VisitDetailsActions({super.key, required this.status});

  final TenantVisitStatus status;

  void _openChat() {
    Go.to(ChatThreadScreen(conversation: ChatContent.conversations.first));
  }

  @override
  Widget build(BuildContext context) {
    if (status.isRejected) {
      return DefaultButton(
        onTap: () => Go.to(const TenantSearchScreen()),
        title: LocaleKeys.tenantVisitFindAlternative,
        color: AppColors.sokoonTeal,
        textColor: AppColors.white,
        borderRadius: BorderRadius.circular(14.r),
        height: 50.h,
        fontSize: 14.sp,
        fontWeight: FontWeight.w900,
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (status.isAccepted) ...[
          DefaultButton(
            onTap: _openChat,
            title: LocaleKeys.tenantVisitOpenOwnerChat,
            color: AppColors.sokoonTeal,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 50.h,
            fontSize: 14.sp,
            fontWeight: FontWeight.w900,
          ),
          12.szH,
        ],
        DefaultButton(
          onTap: () => Go.back(true),
          title: status.isPending
              ? LocaleKeys.tenantVisitCancelRequest
              : LocaleKeys.tenantVisitCancelVisit,
          color: AppColors.white,
          textColor: AppColors.sokoonNavy,
          borderColor: AppColors.sokoonBorder,
          borderRadius: BorderRadius.circular(14.r),
          height: 50.h,
          fontSize: 14.sp,
          fontWeight: FontWeight.w900,
        ),
      ],
    );
  }
}
