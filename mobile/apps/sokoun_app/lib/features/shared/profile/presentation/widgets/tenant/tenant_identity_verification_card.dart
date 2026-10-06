part of '../../../imports.dart';

class TenantIdentityVerificationCard extends StatelessWidget {
  const TenantIdentityVerificationCard({super.key, required this.verification});

  final TenantIdentityVerificationContent verification;

  @override
  Widget build(BuildContext context) {
    final bool isVerified = verification.isVerified;
    final Color accentColor = isVerified
        ? context.appColor(AppColors.green)
        : context.appColor(AppColors.sokoonTeal);
    final Color backgroundColor = isVerified
        ? context.appColor(AppColors.greenPale, surface: true)
        : context.appColor(AppColors.mintLight, surface: true);

    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
      decoration: BoxDecoration(
        color: context.appColor(backgroundColor, surface: true),
        borderRadius: BorderRadius.circular(14.r),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        spacing: 10.w,
        children: [
          Icon(
            isVerified ? Icons.verified_outlined : Icons.badge_outlined,
            color: context.appColor(accentColor),
            size: 22.r,
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              spacing: 3.h,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: AppText(
                        verification.title.isNotEmpty
                            ? verification.title
                            : LocaleKeys.profileIdentityVerification,
                        style: AppTextStyles.extraBold13.copyWith(
                          color: context.appColor(accentColor),
                          fontSize: 13.sp,
                          height: 1.45,
                        ),
                      ),
                    ),
                    if (verification.statusLabel.isNotEmpty)
                      Container(
                        padding: EdgeInsets.symmetric(
                          horizontal: 8.w,
                          vertical: 3.h,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.whiteAlpha60,
                          borderRadius: BorderRadius.circular(99.r),
                        ),
                        child: AppText(
                          verification.statusLabel,
                          style: AppTextStyles.bold10.copyWith(
                            color: context.appColor(accentColor),
                            fontSize: 10.sp,
                            height: 1.45,
                          ),
                        ),
                      ),
                  ],
                ),
                AppText(
                  verification.subtitle,
                  style: AppTextStyles.regular11.copyWith(
                    color: context.appColor(AppColors.sokoonGray),
                    fontSize: 11.sp,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
