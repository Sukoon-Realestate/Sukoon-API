import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';
import 'package:sokoun_app/shared_widgets/sokoun_selection_feedback.dart';

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
      child: AnimatedContainer(
        duration: SokounMotion.duration(context, milliseconds: 280),
        curve: SokounMotion.curve,
        decoration: BoxDecoration(
          color: hasPhoto
              ? context.appColor(AppColors.grayBluePale, surface: true)
              : context.appColor(AppColors.scaffoldBackground, surface: true),
          borderRadius: BorderRadius.circular(14.r),
          border: Border.all(
            color: isMainPhoto
                ? AppColors.sokoonGold
                : hasPhoto
                ? AppColors.transparent
                : context.appColor(AppColors.sokoonBorder),
            width: isMainPhoto ? 2 : 1,
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
                                    color: context.appColor(
                                      AppColors.sokoonMuted,
                                    ),
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
                          color: context.appColor(AppColors.sokoonMuted),
                          size: 20.r,
                        ),
                        AppText(
                          LocaleKeys.ownerPropertiesAddPhoto,
                          style: AppTextStyles.semiBold.copyWith(
                            color: context.appColor(AppColors.sokoonMuted),
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
                  color: context.appColor(AppColors.sokoonTeal),
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
                  color: context.appColor(AppColors.red),
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
                  child: SokounSelectionFeedback(
                    selected: isMainPhoto,
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
        backgroundColor: context.appColor(color, surface: true),
        foregroundColor: AppColors.white,
      ),
      icon: Icon(icon, size: 20.r),
    );
  }
}
