import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

import 'add_property_chip_wrap.dart';
import 'add_property_info_banner.dart';
import 'add_property_section_card.dart';
import 'add_property_step_shell.dart';

class AddPropertyExtraDetailsPage extends StatelessWidget {
  const AddPropertyExtraDetailsPage({
    super.key,
    required this.form,
    required this.onSmokingSelected,
    required this.onSuitableForSelected,
    required this.onProofUploadTap,
    required this.onNext,
    required this.onBack,
    this.isSubmitting = false,
    this.primaryLabel,
  });

  final OwnerAddPropertyFormState form;
  final ValueChanged<String> onSmokingSelected;
  final ValueChanged<String> onSuitableForSelected;
  final VoidCallback onProofUploadTap;
  final VoidCallback onNext;
  final VoidCallback onBack;
  final bool isSubmitting;
  final String? primaryLabel;

  @override
  Widget build(BuildContext context) {
    return AddPropertyStepShell(
      title: LocaleKeys.ownerAddPropertyDetails,
      activeSegments: 5,
      segmentCount: 5,
      progressSubtitle: LocaleKeys.ownerAddPropertyExtraProgress,
      primaryLabel:
          primaryLabel ??
          (isSubmitting
              ? LocaleKeys.ownerAddPropertySubmitting
              : LocaleKeys.ownerAddPropertySubmitReview),
      onPrimaryTap: form.isExtraDetailsReady && !isSubmitting ? onNext : null,
      onBack: onBack,
      children: [
        AddPropertySectionCard(
          title: LocaleKeys.ownerAddPropertySmokingQuestion,
          child: AddPropertyChipWrap(
            chips: OwnerAddPropertyContent.singleSelectedChips(
              labels: OwnerAddPropertyContent.smokingOptionLabels,
              selectedValue: form.smokingPolicy,
            ),
            onChipTap: (chip) => onSmokingSelected(chip.label),
          ),
        ),
        AddPropertySectionCard(
          title: LocaleKeys.ownerAddPropertySuitableFor,
          child: AddPropertyChipWrap(
            chips: OwnerAddPropertyContent.singleSelectedChips(
              labels: OwnerAddPropertyContent.suitableForOptions,
              selectedValue: form.suitableFor,
            ),
            onChipTap: (chip) => onSuitableForSelected(chip.label),
          ),
        ),
        _OwnershipProofSection(form: form, onProofUploadTap: onProofUploadTap),
      ],
    );
  }
}

class _OwnershipProofSection extends StatelessWidget {
  const _OwnershipProofSection({
    required this.form,
    required this.onProofUploadTap,
  });

  final OwnerAddPropertyFormState form;
  final VoidCallback onProofUploadTap;

  @override
  Widget build(BuildContext context) {
    final bool isUploaded = form.isProofUploaded;

    return AddPropertySectionCard(
      title: LocaleKeys.ownerAddPropertyProofTitle,
      subtitle: LocaleKeys.ownerAddPropertyProofSubtitle,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          GestureDetector(
            onTap: onProofUploadTap,
            behavior: HitTestBehavior.opaque,
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 22.h),
              decoration: BoxDecoration(
                color: isUploaded
                    ? AppColors.greenPale
                    : AppColors.grayOffWhite,
                borderRadius: BorderRadius.circular(12.r),
                border: Border.all(
                  color: isUploaded
                      ? AppColors.greenAlpha19
                      : AppColors.grayPale,
                  width: 1.2,
                ),
              ),
              child: Column(
                children: [
                  Icon(
                    isUploaded
                        ? Icons.insert_drive_file_outlined
                        : Icons.cloud_upload_outlined,
                    color: isUploaded ? AppColors.green : AppColors.sokoonGray,
                    size: 30.r,
                  ),
                  8.szH,
                  AppText(
                    isUploaded
                        ? form.proofFileName
                        : LocaleKeys.ownerAddPropertyProofUpload,
                    color: AppColors.sokoonNavy,
                    fontSize: 13.sp,
                    fontWeight: FontWeight.w800,
                    textAlign: TextAlign.center,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  4.szH,
                  AppText(
                    isUploaded
                        ? LocaleKeys.ownerAddPropertyProofChange
                        : LocaleKeys.ownerAddPropertyProofFormats,
                    color: isUploaded ? AppColors.green : AppColors.sokoonGray,
                    fontSize: 11.sp,
                    fontWeight: FontWeight.w500,
                  ),
                ],
              ),
            ),
          ),
          10.szH,
          AddPropertyInfoBanner(
            title: form.isProofUploaded
                ? LocaleKeys.ownerAddPropertyProofAttached
                : LocaleKeys.ownerAddPropertyProofInternal,
            text: form.isProofUploaded
                ? LocaleKeys.ownerAddPropertyProofPrivate
                : LocaleKeys.ownerAddPropertyProofPrivateContinuation,
            backgroundColor: form.isProofUploaded
                ? AppColors.greenPale
                : AppColors.mintPale,
            borderColor: form.isProofUploaded
                ? AppColors.greenAlpha19
                : AppColors.tealAlpha19,
            iconColor: form.isProofUploaded
                ? AppColors.green
                : AppColors.sokoonTeal,
            icon: Icons.lock_outline_rounded,
          ),
        ],
      ),
    );
  }
}
