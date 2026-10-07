import 'dart:io';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/first_validation_error_form.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

import 'add_property_info_banner.dart';
import 'property_selection_field.dart';
import 'add_property_step_shell.dart';

import 'property_photo_grid.dart';
import 'property_photo_metadata.dart';
import 'property_photo_tips.dart';
import 'property_video_picker.dart';
import 'property_form_validation.dart';
import 'rental_accommodation_media_section.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class AddPropertyPhotosPage extends StatefulWidget {
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
    this.onPhotoMoved,
    this.onFormChanged,
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
  final ValueChanged<({int from, int to})>? onPhotoMoved;
  final OwnerAddPropertyFormState form;
  final ValueChanged<OwnerAddPropertyFormState>? onFormChanged;
  final void Function(File file, int durationSeconds) onVideoSelected;
  final VoidCallback onVideoRemoved;
  final ValueChanged<bool> onVideoPreparingChanged;

  @override
  State<AddPropertyPhotosPage> createState() => _AddPropertyPhotosPageState();
}

class _AddPropertyPhotosPageState extends State<AddPropertyPhotosPage> {
  final GlobalKey _photosFieldKey = GlobalKey();
  final GlobalKey _videoFieldKey = GlobalKey();

  String? get _photosError => PropertyFormValidation.photos(widget.form);

  List<FirstValidationErrorField> _validationFields() => [
    FirstValidationErrorField(
      fieldKey: _videoFieldKey,
      title: LocaleKeys.ownerPropertyVideoTitle,
      value: widget.form.hasVideo ? 'selected' : null,
      validator: (_) => PropertyFormValidation.video(widget.form),
    ),
    FirstValidationErrorField(
      fieldKey: _photosFieldKey,
      title: LocaleKeys.ownerPropertiesPhotos,
      value: '${widget.photos.length}',
      validator: (_) => _photosError,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final bool hasEnoughPhotos = _photosError == null;

    return AddPropertyStepShell(
      validationFields: _validationFields,
      activeSegments: 2,
      segmentCount: 3,
      progressSubtitle: LocaleKeys.ownerAddPropertyPhotosProgress,
      primaryLabel: LocaleKeys.ownerAddPropertyPricingTitle,
      onPrimaryTap: widget.form.isVideoPreparing ? null : widget.onNext,
      children: [
        if (widget.form.rentalInventory != null)
          AppText(LocaleKeys.rentalPropertyMediaOnce),
        AddPropertyInfoBanner(
          title: widget.isReady ? LocaleKeys.ownerAddPropertyPhotosReady : null,
          text: widget.isReady
              ? LocaleKeys.ownerAddPropertyPhotosReadyDescription
              : hasEnoughPhotos
              ? PropertyFormValidation.video(widget.form) ??
                    LocaleKeys.ownerAddPropertyPhotoMetadataRecommended
              : _photosError ?? '',
          backgroundColor: widget.isReady
              ? context.appColor(AppColors.greenPale, surface: true)
              : context.appColor(AppColors.orangePale, surface: true),
          borderColor: widget.isReady
              ? AppColors.greenAlpha19
              : AppColors.goldAlpha15,
          iconColor: widget.isReady
              ? context.appColor(AppColors.green)
              : context.appColor(AppColors.brown),
          textColor: widget.isReady
              ? context.appColor(AppColors.sokoonNavy)
              : context.appColor(AppColors.brown),
          icon: widget.isReady
              ? Icons.check_circle_outline_rounded
              : Icons.warning_amber_rounded,
        ),
        PropertySelectionField(
          key: _videoFieldKey,
          isValid: widget.form.isVideoReady,
          message: PropertyFormValidation.video(widget.form),
          child: PropertyVideoPicker(
            file: widget.form.videoFile,
            existingUrl: widget.form.videoUrl,
            durationSeconds: widget.form.videoDuration,
            onVideoSelected: widget.onVideoSelected,
            onVideoRemoved: widget.onVideoRemoved,
            onPreparingChanged: widget.onVideoPreparingChanged,
          ),
        ),
        PropertySelectionField(
          key: _photosFieldKey,
          isValid: hasEnoughPhotos,
          message: _photosError,
          child: PhotoGridSection(
            photos: widget.photos,
            onAddPhotos: widget.onAddPhotos,
            onRemovePhoto: widget.onRemovePhoto,
            onReplacePhoto: widget.onReplacePhoto,
            onMainPhotoSelected: widget.onMainPhotoSelected,
            onPhotoMoved: widget.onPhotoMoved,
          ),
        ),
        if (widget.photos.isNotEmpty)
          PhotoMetadataSection(
            photos: widget.photos,
            onPhotoNameChanged: widget.onPhotoNameChanged,
            onPhotoDescriptionChanged: widget.onPhotoDescriptionChanged,
          ),
        if (widget.form.isPartialOffering && widget.onFormChanged != null)
          RentalAccommodationMediaSection(
            form: widget.form,
            onChanged: widget.onFormChanged!,
          ),
        const PhotoTipsSection(),
      ],
    );
  }
}
