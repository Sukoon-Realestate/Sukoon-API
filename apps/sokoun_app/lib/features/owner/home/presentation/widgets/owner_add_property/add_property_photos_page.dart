import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

import 'add_property_info_banner.dart';
import 'add_property_section_card.dart';
import 'add_property_step_shell.dart';

class AddPropertyPhotosPage extends StatelessWidget {
  const AddPropertyPhotosPage({
    super.key,
    required this.photos,
    required this.isReady,
    required this.onAddPhotos,
    required this.onRemovePhoto,
    required this.onReplacePhoto,
    required this.onPhotoNameChanged,
    required this.onPhotoDescriptionChanged,
    required this.onNext,
    required this.onBack,
  });

  final List<OwnerPropertyPhotoDraft> photos;
  final bool isReady;
  final VoidCallback onAddPhotos;
  final ValueChanged<int> onRemovePhoto;
  final ValueChanged<int> onReplacePhoto;
  final void Function(int index, String value) onPhotoNameChanged;
  final void Function(int index, String value) onPhotoDescriptionChanged;
  final VoidCallback onNext;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    final int remaining =
        OwnerAddPropertyContent.minimumPhotoCount - photos.length;
    final bool hasEnoughPhotos = remaining <= 0;

    return AddPropertyStepShell(
      title: LocaleKeys.ownerPropertiesPhotos,
      activeSegments: 2,
      segmentCount: 5,
      progressSubtitle: LocaleKeys.ownerAddPropertyPhotosProgress,
      primaryLabel: LocaleKeys.ownerAddPropertyNextVideo,
      onPrimaryTap: isReady ? onNext : null,
      onBack: onBack,
      children: [
        AddPropertyInfoBanner(
          title: isReady ? LocaleKeys.ownerAddPropertyPhotosReady : null,
          text: isReady
              ? LocaleKeys.ownerAddPropertyPhotosReadyDescription
              : hasEnoughPhotos
              ? LocaleKeys.ownerAddPropertyPhotoMetadataRequired
              : LocaleKeys.ownerAddPropertyPhotosRemaining.replaceAll(
                  '{count}',
                  '$remaining',
                ),
          backgroundColor: isReady ? AppColors.greenPale : AppColors.orangePale,
          borderColor: isReady ? AppColors.greenAlpha19 : AppColors.goldAlpha15,
          iconColor: isReady ? AppColors.green : AppColors.brown,
          textColor: isReady ? AppColors.sokoonNavy : AppColors.brown,
          icon: isReady
              ? Icons.check_circle_outline_rounded
              : Icons.warning_amber_rounded,
        ),
        _PhotoGridSection(
          photos: photos,
          onAddPhotos: onAddPhotos,
          onRemovePhoto: onRemovePhoto,
          onReplacePhoto: onReplacePhoto,
        ),
        if (photos.isNotEmpty)
          _PhotoMetadataSection(
            photos: photos,
            onPhotoNameChanged: onPhotoNameChanged,
            onPhotoDescriptionChanged: onPhotoDescriptionChanged,
          ),
        const _PhotoTipsSection(),
      ],
    );
  }
}

class _PhotoGridSection extends StatelessWidget {
  const _PhotoGridSection({
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
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 3,
            crossAxisSpacing: 10.w,
            mainAxisSpacing: 10.h,
            childAspectRatio: 1,
          ),
          itemCount: photos.length + (canAddMore ? 1 : 0),
          itemBuilder: (context, index) {
            if (index == photos.length) {
              return _PhotoTile(onAddPhotos: onAddPhotos);
            }
            final OwnerPropertyPhotoDraft photo = photos[index];
            return _PhotoTile(
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
          color: hasEnoughPhotos ? AppColors.green : AppColors.sokoonGray,
          fontSize: 12.sp,
          fontWeight: FontWeight.w700,
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}

class _PhotoTile extends StatelessWidget {
  const _PhotoTile({
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
                          color: AppColors.sokoonMuted,
                          fontSize: 10.sp,
                          fontWeight: FontWeight.w600,
                        ),
                      ],
                    ).centerWidget,
            ),
            if (onReplacePhoto != null)
              PositionedDirectional(
                bottom: 6.r,
                end: 6.r,
                child: _PhotoTileAction(
                  icon: Icons.photo_camera_outlined,
                  onTap: onReplacePhoto!,
                  color: AppColors.sokoonTeal,
                ),
              ),
            if (onRemovePhoto != null)
              PositionedDirectional(
                top: 6.r,
                start: 6.r,
                child: _PhotoTileAction(
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

class _PhotoTileAction extends StatelessWidget {
  const _PhotoTileAction({
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

class _PhotoMetadataSection extends StatelessWidget {
  const _PhotoMetadataSection({
    required this.photos,
    required this.onPhotoNameChanged,
    required this.onPhotoDescriptionChanged,
  });

  final List<OwnerPropertyPhotoDraft> photos;
  final void Function(int index, String value) onPhotoNameChanged;
  final void Function(int index, String value) onPhotoDescriptionChanged;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (int index = 0; index < photos.length; index++) ...[
          _PhotoMetadataCard(
            photo: photos[index],
            index: index,
            onNameChanged: (value) => onPhotoNameChanged(index, value),
            onDescriptionChanged: (value) =>
                onPhotoDescriptionChanged(index, value),
          ),
          if (index < photos.length - 1) 10.szH,
        ],
      ],
    );
  }
}

class _PhotoMetadataCard extends StatelessWidget {
  const _PhotoMetadataCard({
    required this.photo,
    required this.index,
    required this.onNameChanged,
    required this.onDescriptionChanged,
  });

  final OwnerPropertyPhotoDraft photo;
  final int index;
  final ValueChanged<String> onNameChanged;
  final ValueChanged<String> onDescriptionChanged;

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: LocaleKeys.ownerAddPropertyPhotoNumber.replaceAll(
        '{number}',
        '${index + 1}',
      ),
      child: photo.isExisting
          ? Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (photo.name.trim().isNotEmpty)
                  AppText(
                    photo.name,
                    color: AppColors.sokoonNavy,
                    fontSize: 13.sp,
                    fontWeight: FontWeight.w800,
                    textAlign: TextAlign.start,
                  ),
                if (photo.description.trim().isNotEmpty) ...[
                  4.szH,
                  AppText(
                    photo.description,
                    color: AppColors.sokoonGray,
                    fontSize: 12.sp,
                    textAlign: TextAlign.start,
                  ),
                ],
                if (photo.name.trim().isNotEmpty ||
                    photo.description.trim().isNotEmpty)
                  8.szH,
                AppText(
                  LocaleKeys.ownerAddPropertyExistingPhotoPreserved,
                  color: AppColors.sokoonGray,
                  fontSize: 11.sp,
                  textAlign: TextAlign.start,
                ),
              ],
            )
          : Column(
              children: [
                _PhotoMetadataField(
                  key: ValueKey('photo-name-${photo.id}'),
                  label: LocaleKeys.ownerAddPropertyPhotoName,
                  hint: LocaleKeys.ownerAddPropertyPhotoNameHint,
                  initialValue: photo.name,
                  errorText: photo.name.trim().isEmpty
                      ? LocaleKeys.ownerAddPropertyPhotoNameRequired
                      : null,
                  onChanged: onNameChanged,
                ),
                10.szH,
                _PhotoMetadataField(
                  key: ValueKey('photo-description-${photo.id}'),
                  label: LocaleKeys.ownerAddPropertyPhotoDescription,
                  hint: LocaleKeys.ownerAddPropertyPhotoDescriptionHint,
                  initialValue: photo.description,
                  errorText: photo.description.trim().isEmpty
                      ? LocaleKeys.ownerAddPropertyPhotoDescriptionRequired
                      : null,
                  onChanged: onDescriptionChanged,
                  maxLines: 3,
                ),
              ],
            ),
    );
  }
}

class _PhotoMetadataField extends StatelessWidget {
  const _PhotoMetadataField({
    super.key,
    required this.label,
    required this.hint,
    required this.initialValue,
    required this.onChanged,
    this.errorText,
    this.maxLines = 1,
  });

  final String label;
  final String hint;
  final String initialValue;
  final ValueChanged<String> onChanged;
  final String? errorText;
  final int maxLines;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(
          label,
          color: AppColors.sokoonGray,
          fontSize: 12.sp,
          fontWeight: FontWeight.w600,
          textAlign: TextAlign.start,
        ),
        6.szH,
        TextFormField(
          initialValue: initialValue,
          onChanged: onChanged,
          maxLines: maxLines,
          minLines: maxLines == 1 ? 1 : 2,
          style: TextStyle(
            color: AppColors.sokoonNavy,
            fontSize: 13.sp,
            fontWeight: FontWeight.w500,
          ),
          decoration: InputDecoration(
            hintText: hint,
            errorText: errorText,
            filled: true,
            fillColor: AppColors.white,
            contentPadding: EdgeInsets.symmetric(
              horizontal: 14.w,
              vertical: 12.h,
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12.r),
              borderSide: const BorderSide(color: AppColors.sokoonBorder),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12.r),
              borderSide: const BorderSide(color: AppColors.sokoonTeal),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12.r),
              borderSide: const BorderSide(color: AppColors.red),
            ),
            focusedErrorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12.r),
              borderSide: const BorderSide(color: AppColors.red),
            ),
          ),
        ),
      ],
    );
  }
}

class _PhotoTipsSection extends StatelessWidget {
  const _PhotoTipsSection();

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: LocaleKeys.ownerAddPropertyPhotoTips,
      child: Column(
        children: [
          for (
            int index = 0;
            index < OwnerAddPropertyContent.photoTips.length;
            index++
          ) ...[
            _TipRow(text: OwnerAddPropertyContent.photoTips[index]),
            if (index < OwnerAddPropertyContent.photoTips.length - 1)
              const Divider(color: AppColors.sokoonBorder),
          ],
        ],
      ),
    );
  }
}

class _TipRow extends StatelessWidget {
  const _TipRow({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          Icons.check_circle_outline_rounded,
          color: AppColors.sokoonTeal,
          size: 16.r,
        ),
        8.szW,
        Expanded(
          child: AppText(
            text,
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            fontWeight: FontWeight.w400,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    ).paddingSymmetric(vertical: 4.h);
  }
}
