import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

import 'add_property_section_card.dart';

class PhotoMetadataSection extends StatelessWidget {
  const PhotoMetadataSection({
    super.key,
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
          PhotoMetadataCard(
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

class PhotoMetadataCard extends StatelessWidget {
  const PhotoMetadataCard({
    super.key,
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
                PhotoMetadataField(
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
                PhotoMetadataField(
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

class PhotoMetadataField extends StatelessWidget {
  const PhotoMetadataField({
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
