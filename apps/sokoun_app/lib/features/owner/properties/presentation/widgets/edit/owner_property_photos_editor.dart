part of '../../../imports.dart';

class OwnerPropertyPhotosEditor extends StatelessWidget {
  const OwnerPropertyPhotosEditor({
    super.key,
    required this.photoCount,
    required this.onAddPressed,
    required this.onRemovePressed,
  });

  final int photoCount;
  final VoidCallback onAddPressed;
  final VoidCallback onRemovePressed;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 8.h,
      children: [
        Row(
          children: [
            AppText(
              LocaleKeys.ownerPropertiesPhotos,
              style: AppTextStyles.extraBold13.copyWith(
                color: AppColors.sokoonNavy,
                fontSize: 13.sp,
                height: 1.45,
              ),
            ),
            const Spacer(),
            AppText(
              '$photoCount ${LocaleKeys.ownerPropertiesPhotoUnit}',
              style: AppTextStyles.regular12.copyWith(
                color: AppColors.sokoonGray,
                fontSize: 12.sp,
                height: 1.45,
              ),
            ),
          ],
        ),
        SizedBox(
          height: 82.h,
          child: ListView(
            scrollDirection: Axis.horizontal,
            children: [
              if (photoCount > 0)
                Stack(
                  children: [
                    _PhotoTile(
                      icon: Icons.apartment_rounded,
                      backgroundColor: AppColors.grayBluePale,
                      foregroundColor: AppColors.blueGray,
                    ),
                    PositionedDirectional(
                      top: 4.h,
                      end: 4.w,
                      child: GestureDetector(
                        onTap: onRemovePressed,
                        child: Container(
                          width: 24.r,
                          height: 24.r,
                          decoration: const BoxDecoration(
                            color: AppColors.red,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            Icons.close_rounded,
                            size: 15.r,
                            color: AppColors.white,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              if (photoCount > 0) 8.szW,
              for (int index = 1; index < photoCount.clamp(1, 4); index++) ...[
                const _PhotoTile(
                  icon: Icons.image_outlined,
                  backgroundColor: AppColors.grayBackground,
                  foregroundColor: AppColors.blueGrayLight,
                ),
                8.szW,
              ],
              GestureDetector(
                onTap: onAddPressed,
                child: _PhotoTile(
                  icon: Icons.add_photo_alternate_outlined,
                  backgroundColor: AppColors.mintPale,
                  foregroundColor: AppColors.sokoonTeal,
                  label: LocaleKeys.ownerPropertiesAddPhoto,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _PhotoTile extends StatelessWidget {
  const _PhotoTile({
    required this.icon,
    required this.backgroundColor,
    required this.foregroundColor,
    this.label,
  });

  final IconData icon;
  final Color backgroundColor;
  final Color foregroundColor;
  final String? label;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 82.r,
      height: 82.r,
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(14.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        spacing: 3.h,
        children: [
          Icon(icon, color: foregroundColor, size: 25.r),
          if (label != null)
            AppText(
              label!,
              style: AppTextStyles.bold10.copyWith(
                color: foregroundColor,
                fontSize: 10.sp,
                height: 1.45,
              ),
            ),
        ],
      ),
    );
  }
}
