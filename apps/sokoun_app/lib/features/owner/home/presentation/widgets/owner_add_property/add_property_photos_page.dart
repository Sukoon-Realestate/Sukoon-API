import 'dart:io';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

import 'add_property_info_banner.dart';
import 'property_selection_field.dart';
import 'add_property_step_shell.dart';

import 'property_photo_grid.dart';
import 'property_photo_metadata.dart';
import 'property_photo_tips.dart';
import 'property_video_picker.dart';

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
    required this.onMainPhotoSelected,
    required this.form,
    required this.onVideoSelected,
    required this.onVideoRemoved,
    required this.onVideoPreparingChanged,
  });

  final List<OwnerPropertyPhotoDraft> photos;
  final bool isReady;
  final VoidCallback onAddPhotos;
  final ValueChanged<int> onRemovePhoto;
  final ValueChanged<int> onReplacePhoto;
  final void Function(int index, String value) onPhotoNameChanged;
  final void Function(int index, String value) onPhotoDescriptionChanged;
  final VoidCallback onNext;
  final ValueChanged<int> onMainPhotoSelected;
  final OwnerAddPropertyFormState form;
  final void Function(File file, int durationSeconds) onVideoSelected;
  final VoidCallback onVideoRemoved;
  final ValueChanged<bool> onVideoPreparingChanged;

  @override
  Widget build(BuildContext context) {
    final int remaining =
        OwnerAddPropertyContent.minimumPhotoCount - photos.length;
    final bool hasEnoughPhotos = remaining <= 0;

    return AddPropertyStepShell(
      activeSegments: 2,
      segmentCount: 3,
      progressSubtitle: LocaleKeys.ownerAddPropertyPhotosProgress,
      primaryLabel: LocaleKeys.ownerAddPropertyPricingTitle,
      onPrimaryTap: form.isVideoPreparing ? null : onNext,
      children: [
        AddPropertyInfoBanner(
          title: isReady ? LocaleKeys.ownerAddPropertyPhotosReady : null,
          text: isReady
              ? LocaleKeys.ownerAddPropertyPhotosReadyDescription
              : hasEnoughPhotos
              ? LocaleKeys.ownerAddPropertyPhotoMetadataRecommended
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
        PropertySelectionField(
          isValid: hasEnoughPhotos,
          message: LocaleKeys.ownerAddPropertyPhotosRemaining.replaceAll(
            '{count}',
            '$remaining',
          ),
          child: PhotoGridSection(
            photos: photos,
            onAddPhotos: onAddPhotos,
            onRemovePhoto: onRemovePhoto,
            onReplacePhoto: onReplacePhoto,
            onMainPhotoSelected: onMainPhotoSelected,
          ),
        ),
        if (photos.isNotEmpty)
          PhotoMetadataSection(
            photos: photos,
            onPhotoNameChanged: onPhotoNameChanged,
            onPhotoDescriptionChanged: onPhotoDescriptionChanged,
          ),
        const PhotoTipsSection(),
        PropertyVideoPicker(
          file: form.videoFile,
          existingUrl: form.videoUrl,
          durationSeconds: form.videoDuration,
          onVideoSelected: onVideoSelected,
          onVideoRemoved: onVideoRemoved,
          onPreparingChanged: onVideoPreparingChanged,
        ),
      ],
    );
  }
}
