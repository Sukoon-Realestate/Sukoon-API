import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

import 'add_property_info_banner.dart';
import 'add_property_step_shell.dart';

import 'property_photo_grid.dart';
import 'property_photo_metadata.dart';
import 'property_photo_tips.dart';

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
        PhotoGridSection(
          photos: photos,
          onAddPhotos: onAddPhotos,
          onRemovePhoto: onRemovePhoto,
          onReplacePhoto: onReplacePhoto,
        ),
        if (photos.isNotEmpty)
          PhotoMetadataSection(
            photos: photos,
            onPhotoNameChanged: onPhotoNameChanged,
            onPhotoDescriptionChanged: onPhotoDescriptionChanged,
          ),
        const PhotoTipsSection(),
      ],
    );
  }
}
