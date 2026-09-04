part of '../../../imports.dart';

class ProfileVerifiedBadge extends StatelessWidget {
  const ProfileVerifiedBadge({super.key, this.text});

  final String? text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
      decoration: BoxDecoration(
        color: AppColors.goldPale,
        borderRadius: BorderRadius.circular(999.r),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.check_circle_outline_rounded,
            color: AppColors.sokoonGold,
            size: 11.r,
          ),
          4.szW,
          Flexible(
            child: AppText(
              text ?? LocaleKeys.verified,
              color: AppColors.sokoonGold,
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
