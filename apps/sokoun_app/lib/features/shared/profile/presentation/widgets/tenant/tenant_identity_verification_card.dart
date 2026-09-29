part of '../../../imports.dart';

class TenantIdentityVerificationCard extends StatelessWidget {
  const TenantIdentityVerificationCard({super.key, required this.verification});

  final TenantIdentityVerificationContent verification;

  @override
  Widget build(BuildContext context) {
    final bool isVerified = verification.isVerified;
    final Color accentColor = isVerified
        ? AppColors.green
        : AppColors.sokoonTeal;
    final Color backgroundColor = isVerified
        ? AppColors.greenPale
        : AppColors.mintLight;

    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(14.r),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            isVerified ? Icons.verified_outlined : Icons.badge_outlined,
            color: accentColor,
            size: 22.r,
          ),
          10.szW,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: AppText(
                        verification.title.isNotEmpty
                            ? verification.title
                            : LocaleKeys.profileIdentityVerification,
                        style: AppTextStyles.extraBold13.copyWith(
                          color: accentColor,
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
                            color: accentColor,
                            fontSize: 10.sp,
                            height: 1.45,
                          ),
                        ),
                      ),
                  ],
                ),
                3.szH,
                AppText(
                  verification.subtitle,
                  style: AppTextStyles.regular11.copyWith(
                    color: AppColors.sokoonGray,
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
