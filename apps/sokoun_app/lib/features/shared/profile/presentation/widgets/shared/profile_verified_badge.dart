part of '../../../imports.dart';

class ProfileVerifiedBadge extends StatelessWidget {
  const ProfileVerifiedBadge({super.key, this.text, this.isVerified = true});

  final String? text;
  final bool isVerified;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
      decoration: BoxDecoration(
        color: isVerified ? AppColors.goldPale : AppColors.grayBackground,
        borderRadius: BorderRadius.circular(999.r),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            isVerified
                ? Icons.check_circle_outline_rounded
                : Icons.shield_outlined,
            color: isVerified ? AppColors.sokoonGold : AppColors.sokoonGray,
            size: 11.r,
          ),
          4.szW,
          Flexible(
            child: AppText(
              text ?? LocaleKeys.verified,
              color: isVerified ? AppColors.sokoonGold : AppColors.sokoonGray,
              fontSize: 10.sp,
              fontWeight: FontWeight.w700,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
