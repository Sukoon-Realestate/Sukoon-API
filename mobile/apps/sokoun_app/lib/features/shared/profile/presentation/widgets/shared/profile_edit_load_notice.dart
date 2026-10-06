part of '../../../imports.dart';

class ProfileEditLoadNotice extends StatelessWidget {
  const ProfileEditLoadNotice.loading({super.key})
    : message = null,
      onRetry = null;

  const ProfileEditLoadNotice.error({
    super.key,
    required this.message,
    required this.onRetry,
  });

  final String? message;
  final Future<void> Function()? onRetry;

  @override
  Widget build(BuildContext context) {
    final bool isLoading = onRetry == null;
    if (isLoading) {
      return ProfileSurfaceCard(child: SizedBox(height: 24.h));
    }
    return ProfileSurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        spacing: 10.h,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            spacing: 10.w,
            children: [
              Icon(
                Icons.error_outline,
                color: context.appColor(AppColors.sokoonRose),
                size: 22.r,
              ),
              Expanded(
                child: AppText(
                  LocaleKeys.profileEditDetailsUnavailable,
                  style: AppTextStyles.bold14.copyWith(
                    color: context.appColor(AppColors.sokoonNavy),
                    fontSize: 14.sp,
                    height: 1.45,
                  ),
                ),
              ),
            ],
          ),
          AppText(
            LocaleKeys.profileEditKnownDetailsHint,
            style: AppTextStyles.regular13.copyWith(
              color: context.appColor(AppColors.sokoonGray),
              fontSize: 13.sp,
              height: 1.45,
            ),
          ),
          if (message?.isNotEmpty == true)
            AppText(
              message!,
              style: AppTextStyles.regular13.copyWith(
                color: context.appColor(AppColors.sokoonRose),
                fontSize: 13.sp,
                height: 1.45,
              ),
            ),
          RetryButton(onRetry: onRetry!),
        ],
      ),
    );
  }
}
