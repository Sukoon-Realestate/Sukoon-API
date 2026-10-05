import 'package:flutter/material.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

class PhotoGridSection extends StatelessWidget {
  const PhotoGridSection({
    super.key,
    required this.photos,
    required this.onAddPhotos,
    required this.onRemovePhoto,
    required this.onReplacePhoto,
    required this.onMainPhotoSelected,
  });

  final List<OwnerPropertyPhotoDraft> photos;
  final VoidCallback onAddPhotos;
  final ValueChanged<int> onRemovePhoto;
  final ValueChanged<int> onReplacePhoto;
  final ValueChanged<int> onMainPhotoSelected;

  @override
  Widget build(BuildContext context) {
    final bool canAddMore = Validators.canAddPropertyPhoto(photos.length);
    final bool hasEnoughPhotos = Validators.hasEnoughPropertyPhotos(
      photos.length,
    );

    return Column(
      spacing: 10.h,
      children: [
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: SliverGridDelegateWithMaxCrossAxisExtent(
            maxCrossAxisExtent: 180,
            crossAxisSpacing: 10.w,
            mainAxisSpacing: 10.h,
            childAspectRatio: 1,
          ),
          itemCount: photos.length + (canAddMore ? 1 : 0),
          itemBuilder: (context, index) {
            if (index == photos.length) {
              return PhotoTile(onAddPhotos: onAddPhotos);
            }
            final OwnerPropertyPhotoDraft photo = photos[index];
            return PhotoTile(
              key: ValueKey(photo.id),
              photo: photo,
              onReplacePhoto: () => onReplacePhoto(index),
              onRemovePhoto: photo.canRemove
                  ? () => onRemovePhoto(index)
                  : null,
              isMainPhoto: index == 0,
              onMainPhotoSelected: index == 0
                  ? null
                  : () => onMainPhotoSelected(index),
            );
          },
        ),
        AppText(
          LocaleKeys.ownerAddPropertyPhotosCount
              .replaceAll('{count}', '${photos.length}')
              .replaceAll(
                '{minimum}',
                '${OwnerAddPropertyContent.minimumPhotoCount}',
              ),
          style: AppTextStyles.bold12.copyWith(
            color: hasEnoughPhotos ? AppColors.green : AppColors.sokoonGray,
            fontSize: 12.sp,
            height: 1.45,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}

class PhotoTile extends StatelessWidget {
  const PhotoTile({
    super.key,
    this.photo,
    this.onAddPhotos,
    this.onReplacePhoto,
    this.onRemovePhoto,
    this.isMainPhoto = false,
    this.onMainPhotoSelected,
  });

  final OwnerPropertyPhotoDraft? photo;
  final VoidCallback? onAddPhotos;
  final VoidCallback? onReplacePhoto;
  final VoidCallback? onRemovePhoto;
  final bool isMainPhoto;
  final VoidCallback? onMainPhotoSelected;

  @override
  Widget build(BuildContext context) {
    final OwnerPropertyPhotoDraft? selectedPhoto = photo;
    final bool hasPhoto = selectedPhoto != null;
    return GestureDetector(
      onTap: hasPhoto ? onReplacePhoto : onAddPhotos,
      behavior: HitTestBehavior.opaque,
      child: Container(
        decoration: BoxDecoration(
          color: hasPhoto
              ? AppColors.grayBluePale
              : AppColors.scaffoldBackground,
          borderRadius: BorderRadius.circular(14.r),
          border: Border.all(
            color: hasPhoto ? AppColors.transparent : AppColors.sokoonBorder,
          ),
        ),
        child: Stack(
          children: [
            Positioned.fill(
              child: hasPhoto
                  ? ClipRRect(
                      borderRadius: BorderRadius.circular(14.r),
                      child: selectedPhoto.file != null
                          ? Image.file(selectedPhoto.file!, fit: BoxFit.cover)
                          : Image.network(
                              selectedPhoto.existingUrl,
                              fit: BoxFit.cover,
                              errorBuilder: (context, error, stackTrace) =>
                                  Icon(
                                    Icons.broken_image_outlined,
                                    color: AppColors.sokoonMuted,
                                    size: 24.r,
                                  ),
                            ),
                    )
                  : Column(
                      mainAxisSize: MainAxisSize.min,
                      spacing: 4.h,
                      children: [
                        Icon(
                          Icons.add_rounded,
                          color: AppColors.sokoonMuted,
                          size: 20.r,
                        ),
                        AppText(
                          LocaleKeys.ownerPropertiesAddPhoto,
                          style: AppTextStyles.semiBold.copyWith(
                            color: AppColors.sokoonMuted,
                            fontSize: 10.sp,
                          ),
                        ),
                      ],
                    ).centerWidget,
            ),
            if (onReplacePhoto != null)
              PositionedDirectional(
                bottom: 6.r,
                end: 6.r,
                child: PhotoTileAction(
                  icon: Icons.photo_camera_outlined,
                  label: LocaleKeys.ownerAddPropertyReplacePhoto,
                  onTap: onReplacePhoto!,
                  color: AppColors.sokoonTeal,
                ),
              ),
            if (onRemovePhoto != null)
              PositionedDirectional(
                top: 6.r,
                start: 6.r,
                child: PhotoTileAction(
                  icon: Icons.close_rounded,
                  label: LocaleKeys.ownerPropertiesDelete,
                  onTap: onRemovePhoto!,
                  color: AppColors.red,
                ),
              ),
            if (hasPhoto)
              PositionedDirectional(
                top: 6.r,
                end: 6.r,
                child: Tooltip(
                  message: isMainPhoto
                      ? LocaleKeys.tenantPropertyDetailsMainPhoto
                      : LocaleKeys.ownerAddPropertySetMainPhoto,
                  child: IconButton.filled(
                    onPressed: onMainPhotoSelected,
                    style: IconButton.styleFrom(
                      backgroundColor: AppColors.blackAlpha45,
                      disabledBackgroundColor: AppColors.blackAlpha45,
                      foregroundColor: AppColors.white,
                      disabledForegroundColor: AppColors.sokoonGold,
                    ),
                    icon: Icon(
                      isMainPhoto
                          ? Icons.star_rounded
                          : Icons.star_border_rounded,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class PhotoTileAction extends StatelessWidget {
  const PhotoTileAction({
    super.key,
    required this.icon,
    required this.onTap,
    required this.color,
    required this.label,
  });

  final IconData icon;
  final VoidCallback onTap;
  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) {
    return IconButton.filled(
      tooltip: label,
      onPressed: onTap,
      style: IconButton.styleFrom(
        backgroundColor: color,
        foregroundColor: AppColors.white,
      ),
      icon: Icon(icon, size: 20.r),
    );
  }
}
