part of '../../../imports.dart';

class OwnerPropertiesHeader extends StatelessWidget {
  const OwnerPropertiesHeader({super.key, required this.onAddPressed});

  final VoidCallback onAddPressed;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: AppText(
            LocaleKeys.ownerPropertiesTitle,
            style: AppTextStyles.bold.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 20.sp,
            ),
            textAlign: TextAlign.start,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
        12.szW,
        DefaultButton(
          onTap: onAddPressed,
          title: LocaleKeys.ownerPropertiesAdd,
          color: AppColors.sokoonTeal,
          textColor: AppColors.white,
          borderRadius: BorderRadius.circular(12.r),
          padding: EdgeInsets.symmetric(horizontal: 12.w),
          width: 124.w,
          height: 40.h,
          textStyle: AppTextStyles.bold12.copyWith(
            fontSize: 12.sp,
            height: 1.45,
          ),
          isFitted: false,
        ),
      ],
    );
  }
}
