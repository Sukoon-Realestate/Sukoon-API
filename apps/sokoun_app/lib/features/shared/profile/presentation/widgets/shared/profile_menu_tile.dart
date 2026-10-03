part of '../../../imports.dart';

class ProfileMenuTile extends StatelessWidget {
  const ProfileMenuTile({
    super.key,
    required this.icon,
    required this.label,
    required this.iconColor,
    required this.iconBackgroundColor,
    this.subtitle,
    this.value,
    this.onTap,
    this.showDivider = false,
  });

  final IconData icon;
  final String label;
  final String? subtitle;
  final String? value;
  final Color iconColor;
  final Color iconBackgroundColor;
  final VoidCallback? onTap;
  final bool showDivider;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14.r),
      child: Container(
        padding: EdgeInsets.symmetric(vertical: 12.h),
        decoration: BoxDecoration(
          border: showDivider
              ? const Border(bottom: BorderSide(color: AppColors.sokoonBorder))
              : null,
        ),
        child: Row(
          children: [
            Container(
              width: 40.r,
              height: 40.r,
              decoration: BoxDecoration(
                color: iconBackgroundColor,
                borderRadius: BorderRadius.circular(12.r),
              ),
              alignment: Alignment.center,
              child: Icon(icon, color: iconColor, size: 18.r),
            ),
            12.szW,
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: 2.h,
                children: [
                  AppText(
                    label,
                    style: AppTextStyles.bold14.copyWith(
                      color: AppColors.sokoonNavy,
                      fontSize: 14.sp,
                      height: 1.45,
                    ),
                  ),
                  if (subtitle != null)
                    AppText(
                      subtitle!,
                      style: AppTextStyles.regular11.copyWith(
                        color: AppColors.sokoonGray,
                        fontSize: 11.sp,
                        height: 1.45,
                      ),
                    ),
                ],
              ),
            ),
            if (value != null) ...[
              AppText(
                value!,
                style: AppTextStyles.regular12.copyWith(
                  color: AppColors.sokoonGray,
                  fontSize: 12.sp,
                  height: 1.45,
                ),
              ),
              8.szW,
            ],
            if (onTap != null)
              Icon(
                Directionality.of(context) == TextDirection.rtl
                    ? Icons.chevron_left_rounded
                    : Icons.chevron_right_rounded,
                color: AppColors.sokoonGray,
                size: 15.r,
              ),
          ],
        ),
      ),
    );
  }
}
