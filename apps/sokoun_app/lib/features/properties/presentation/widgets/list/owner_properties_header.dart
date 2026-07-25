part of '../../../imports.dart';

class OwnerPropertiesHeader extends StatelessWidget {
  const OwnerPropertiesHeader({super.key, required this.onAddPressed});

  final VoidCallback onAddPressed;

  @override
  Widget build(BuildContext context) {
    return Row(
      textDirection: TextDirection.ltr,
      children: [
        Material(
          color: AppColors.sokoonTeal,
          borderRadius: BorderRadius.circular(14.r),
          child: InkWell(
            key: const ValueKey('owner-properties-add'),
            onTap: onAddPressed,
            borderRadius: BorderRadius.circular(14.r),
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 10.h),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.add_rounded, color: AppColors.white, size: 18.r),
                  5.szW,
                  AppText(
                    LocaleKeys.ownerPropertiesAdd,
                    color: AppColors.white,
                    fontSize: 13.sp,
                    fontWeight: FontWeight.w900,
                  ),
                ],
              ),
            ),
          ),
        ),
        12.szW,
        Expanded(
          child: AppText(
            LocaleKeys.ownerPropertiesTitle,
            color: AppColors.sokoonNavy,
            fontSize: 20.sp,
            fontWeight: FontWeight.w900,
            textAlign: TextAlign.right,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}
