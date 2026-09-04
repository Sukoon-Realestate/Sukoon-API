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
        key: const ValueKey('visit-details-find-alternative'),
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
            key: const ValueKey('visit-details-open-chat'),
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
          key: const ValueKey('visit-details-cancel'),
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
