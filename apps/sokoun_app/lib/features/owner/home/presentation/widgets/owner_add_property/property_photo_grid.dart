import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
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
  });

  final List<OwnerPropertyPhotoDraft> photos;
  final VoidCallback onAddPhotos;
  final ValueChanged<int> onRemovePhoto;
  final ValueChanged<int> onReplacePhoto;

  @override
  Widget build(BuildContext context) {
    final bool canAddMore =
        photos.length < OwnerAddPropertyContent.maxPhotoCount;
    final bool hasEnoughPhotos =
        photos.length >= OwnerAddPropertyContent.minimumPhotoCount;

    return Column(
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
              photo: photo,
              onReplacePhoto: photo.isExisting
                  ? null
                  : () => onReplacePhoto(index),
              onRemovePhoto: photo.canRemove
                  ? () => onRemovePhoto(index)
                  : null,
            );
          },
        ),
        10.szH,
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
  });

  final OwnerPropertyPhotoDraft? photo;
  final VoidCallback? onAddPhotos;
  final VoidCallback? onReplacePhoto;
  final VoidCallback? onRemovePhoto;

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
                      children: [
                        Icon(
                          Icons.add_rounded,
                          color: AppColors.sokoonMuted,
                          size: 20.r,
                        ),
                        4.szH,
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
                  onTap: onRemovePhoto!,
                  color: AppColors.red,
                ),
              ),
            if (selectedPhoto?.isExisting ?? false)
              PositionedDirectional(
                bottom: 6.r,
                end: 6.r,
                child: Container(
                  width: 24.r,
                  height: 24.r,
                  decoration: const BoxDecoration(
                    color: AppColors.blackAlpha45,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    Icons.lock_outline_rounded,
                    color: AppColors.white,
                    size: 14.r,
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
  });

  final IconData icon;
  final VoidCallback onTap;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        width: 24.r,
        height: 24.r,
        alignment: Alignment.center,
        decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        child: Icon(icon, color: AppColors.white, size: 14.r),
      ),
    );
  }
}
