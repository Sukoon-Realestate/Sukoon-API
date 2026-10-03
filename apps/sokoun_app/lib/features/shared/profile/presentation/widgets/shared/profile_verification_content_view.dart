part of '../../../imports.dart';

class ProfileVerificationContentView extends StatelessWidget {
  const ProfileVerificationContentView({
    super.key,
    required this.content,
    required this.workspace,
  });
  final ProfileVerificationContent content;
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) {
    final ProfileVerificationStatus status = content.status;
    final Color accent = status.isApproved
        ? AppColors.green
        : status.isRejected
        ? AppColors.sokoonRose
        : status.isPending
        ? AppColors.amber
        : workspace.isOwner
        ? AppColors.sokoonGold
        : AppColors.sokoonTeal;
    final String title = switch (status) {
      ProfileVerificationStatus.approved => LocaleKeys.kycApprovedTitle,
      ProfileVerificationStatus.pending => LocaleKeys.kycPendingTitle,
      ProfileVerificationStatus.rejected =>
        LocaleKeys.profileVerificationRejected,
      ProfileVerificationStatus.incomplete => LocaleKeys.verifyIdentityAndStart,
      ProfileVerificationStatus.unknown =>
        LocaleKeys.profileVerificationUnknown,
    };
    return ListView(
      padding: EdgeInsets.all(24.r),
      children: [
        Container(
          padding: EdgeInsets.all(24.r),
          decoration: BoxDecoration(
            color: accent.withValues(alpha: .08),
            borderRadius: BorderRadius.circular(20.r),
          ),
          child: Column(
            spacing: 16.h,
            children: [
              Icon(
                status.isApproved
                    ? Icons.verified_outlined
                    : status.isPending
                    ? Icons.hourglass_empty_rounded
                    : status.isRejected
                    ? Icons.error_outline_rounded
                    : Icons.badge_outlined,
                size: 48.r,
                color: accent,
              ),
              AppText(
                title,
                textAlign: TextAlign.center,
                style: AppTextStyles.bold16.copyWith(
                  color: AppColors.sokoonNavy,
                ),
              ),
              AppText(
                status.isApproved
                    ? LocaleKeys.kycApprovedDescription
                    : status.isPending
                    ? LocaleKeys.kycPendingDescription
                    : status.isRejected
                    ? LocaleKeys.profileVerificationRejectedDescription
                    : status == ProfileVerificationStatus.unknown
                    ? LocaleKeys.profileVerificationUnknownDescription
                    : LocaleKeys.kycIntroDescription,
                textAlign: TextAlign.center,
                style: AppTextStyles.regular14.copyWith(
                  color: AppColors.sokoonGray,
                  height: 1.6,
                ),
              ),
            ],
          ),
        ),
        24.szH,
        if (content.fullName.isNotEmpty)
          AppText(
            content.fullName,
            style: AppTextStyles.bold16,
          ).paddingOnly(bottom: 12),
        if (content.submittedAt.isNotEmpty)
          AppText(
            '${LocaleKeys.submittedAt}: ${profileDate(content.submittedAt, context, showTime: true)}',
            style: AppTextStyles.regular14,
          ).paddingOnly(bottom: 12),
        if (content.rejectionReason.isNotEmpty)
          ProfileVerificationBanner(
            title: LocaleKeys.profileVerificationReason,
            description: content.rejectionReason,
            isPrivacy: true,
          ).paddingOnly(bottom: 20),
        if (status.canSubmit)
          DefaultButton(
            title: LocaleKeys.uploadDocuments,
            onTap: () async {
              await Go.to(const KycIntroScreen());
              if (context.mounted) {
                context.read<ProfileVerificationCubit>().load();
              }
            },
          ),
      ],
    );
  }
}
