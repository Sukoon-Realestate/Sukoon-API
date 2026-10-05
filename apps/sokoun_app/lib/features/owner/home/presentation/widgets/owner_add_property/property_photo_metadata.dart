import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
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
      spacing: 10.h,
      children: [
        AppText(
          LocaleKeys.ownerAddPropertyPhotoMetadataRecommended,
          style: AppTextStyles.regular12.copyWith(color: AppColors.sokoonGray),
        ),
        for (int index = 0; index < photos.length; index++)
          PhotoMetadataCard(
            key: ValueKey(photos[index].id),
            photo: photos[index],
            index: index,
            onNameChanged: (value) => onPhotoNameChanged(index, value),
            onDescriptionChanged: (value) =>
                onPhotoDescriptionChanged(index, value),
          ),
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
      child: Column(
        spacing: 10.h,
        children: [
          PhotoMetadataField(
            key: ValueKey('photo-name-${photo.id}'),
            label: LocaleKeys.ownerAddPropertyPhotoName,
            hint: LocaleKeys.ownerAddPropertyPhotoNameHint,
            initialValue: photo.name,
            onChanged: onNameChanged,
          ),
          PhotoMetadataField(
            key: ValueKey('photo-description-${photo.id}'),
            label: LocaleKeys.ownerAddPropertyPhotoDescription,
            hint: LocaleKeys.ownerAddPropertyPhotoDescriptionHint,
            initialValue: photo.description,
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
    this.validator,
    this.maxLines = 1,
  });

  final String label;
  final String hint;
  final String initialValue;
  final ValueChanged<String> onChanged;
  final FormFieldValidator<String>? validator;
  final int maxLines;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 6.h,
      children: [
        AppText(
          '$label (${LocaleKeys.ownerAddPropertyOptionalRecommended})',
          style: AppTextStyles.semiBold.copyWith(
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
          ),
          textAlign: TextAlign.start,
        ),
        TextFormField(
          initialValue: initialValue,
          onChanged: onChanged,
          validator: validator,
          maxLines: maxLines,
          minLines: maxLines == 1 ? 1 : 2,
          style: AppTextStyles.medium13.copyWith(
            color: AppColors.sokoonNavy,
            fontSize: 13.sp,
            height: 1.45,
          ),
          decoration: InputDecoration(
            errorMaxLines: 3,
            hintText: hint,
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
