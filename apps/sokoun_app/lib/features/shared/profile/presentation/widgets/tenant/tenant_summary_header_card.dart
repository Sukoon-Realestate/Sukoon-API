part of '../../../imports.dart';

class TenantSummaryHeaderCard extends StatelessWidget {
  const TenantSummaryHeaderCard({super.key, required this.user});

  final TenantAccountSummaryUserContent user;

  @override
  Widget build(BuildContext context) {
    final String userName = user.fullName.trim().isNotEmpty
        ? user.fullName
        : user.initial.trim().isNotEmpty
        ? user.initial
        : LocaleKeys.profileFallbackName;
    final String membership = [
      user.roleLabel,
      user.memberSinceLabel,
    ].where((value) => value.isNotEmpty).join(' · ');
    final double completion =
        (user.profileCompletionPercentage.clamp(0, 100)) / 100;

    return Container(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 22.h),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: AlignmentDirectional.topStart,
          end: AlignmentDirectional.bottomEnd,
          colors: [context.appColor(AppColors.sokoonTeal), AppColors.tealDark],
        ),
        borderRadius: BorderRadius.circular(20.r),
      ),
      child: Column(
        children: [
          Row(
            spacing: 14.w,
            children: [
              ProfileAvatar(
                name: userName,
                avatarUrl: user.avatar,
                accentColor: context.appColor(AppColors.sokoonTeal),
                backgroundColor: AppColors.whiteAlpha10,
                size: 56,
                useInitial: true,
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  spacing: 3.h,
                  children: [
                    AppText(
                      userName,
                      style: AppTextStyles.bold.copyWith(
                        color: AppColors.white,
                        fontSize: 18.sp,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    AppText(
                      membership.isNotEmpty
                          ? membership
                          : LocaleKeys.workspaceTenant,
                      style: AppTextStyles.regular12.copyWith(
                        color: AppColors.whiteAlpha60,
                        fontSize: 12.sp,
                        height: 1.45,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          16.szH,
          Row(
            children: [
              AppText(
                user.profileCompletionLabel.isNotEmpty
                    ? user.profileCompletionLabel
                    : LocaleKeys.profileCompletion,
                style: AppTextStyles.regular12.copyWith(
                  color: AppColors.whiteAlpha60,
                  fontSize: 12.sp,
                  height: 1.45,
                ),
              ),
              const Spacer(),
              AppText(
                '${user.profileCompletionPercentage.clamp(0, 100)}%',
                style: AppTextStyles.extraBold.copyWith(
                  color: AppColors.white,
                  fontSize: 12.sp,
                ),
              ),
            ],
          ),
          7.szH,
          ClipRRect(
            borderRadius: BorderRadius.circular(99.r),
            child: LinearProgressIndicator(
              value: completion,
              minHeight: 6.h,
              color: AppColors.white,
              backgroundColor: AppColors.whiteAlpha40,
            ),
          ),
        ],
      ),
    );
  }
}
