import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';
import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';
import 'package:melos_core/core/widgets/validation_helper.dart';
import 'package:sokoun_app/features/shared/auth/data/models/kyc_upload_documents_data.dart';

import '../auth_scaffold.dart';
import 'kyc_privacy_card.dart';
import 'kyc_progress_bar.dart';
import 'kyc_upload_tile.dart';

class KycUploadDocumentsView extends StatelessWidget {
  const KycUploadDocumentsView({
    super.key,
    required this.dataListenable,
    required this.nationalIdFieldKey,
    required this.frontIdFieldKey,
    required this.backIdFieldKey,
    required this.selfieFieldKey,
    required this.nationalIdController,
    required this.validateNationalId,
    required this.onNationalIdChanged,
    required this.onPickFrontId,
    required this.onPickBackId,
    required this.onCaptureSelfie,
    required this.onSubmit,
    this.onBack,
    this.existingAccount = false,
    this.submissionMessage,
  });

  final ValueListenable<KycUploadDocumentsData> dataListenable;
  final GlobalKey nationalIdFieldKey;
  final GlobalKey<FormFieldState<String>> frontIdFieldKey;
  final GlobalKey<FormFieldState<String>> backIdFieldKey;
  final GlobalKey<FormFieldState<String>> selfieFieldKey;
  final TextEditingController nationalIdController;
  final FormFieldValidator<String> validateNationalId;
  final ValueChanged<String?> onNationalIdChanged;
  final VoidCallback onPickFrontId;
  final VoidCallback onPickBackId;
  final VoidCallback onCaptureSelfie;
  final Future<void> Function() onSubmit;
  final VoidCallback? onBack;
  final bool existingAccount;
  final ValueListenable<String?>? submissionMessage;

  @override
  Widget build(BuildContext context) {
    return AuthScaffold(
      showBackButton: true,
      isScrollable: false,
      padding: EdgeInsets.zero,
      bottomNavigationBar: _KycUploadSubmitBar(
        onSubmit: onSubmit,
        existingAccount: existingAccount,
      ),
      onBack: onBack,
      title: LocaleKeys.uploadDocumentsTitle,
      child: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              padding: EdgeInsets.all(16.w),
              child: ValueListenableBuilder<KycUploadDocumentsData>(
                valueListenable: dataListenable,
                builder: (context, data, _) => Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const KycProgressBar(currentStep: 2),
                    16.szH,
                    if (submissionMessage != null)
                      ValueListenableBuilder<String?>(
                        valueListenable: submissionMessage!,
                        builder: (_, message, __) => message == null
                            ? const SizedBox.shrink()
                            : Semantics(
                                liveRegion: true,
                                child: AppText(
                                  message,
                                  style: AppTextStyles.regular13.copyWith(
                                    color: AppColors.sokoonRose,
                                  ),
                                ),
                              ),
                      ),
                    AppText(
                      existingAccount
                          ? LocaleKeys.kycExistingDocumentsHint
                          : LocaleKeys.uploadClearIdImage,
                      style: AppTextStyles.regular13.copyWith(
                        color: AppColors.sokoonGray,
                        fontSize: 13.sp,
                        height: 1.45,
                      ),
                    ),
                    18.szH,
                    _NationalIdField(
                      fieldKey: nationalIdFieldKey,
                      controller: nationalIdController,
                      validator: validateNationalId,
                      valueLength: data.nationalId.length,
                      onChanged: onNationalIdChanged,
                      isRequired: !existingAccount,
                    ),
                    18.szH,
                    _KycUploadValidationField(
                      fieldKey: frontIdFieldKey,
                      value: data.frontIdFileName,
                      isRequired: !existingAccount,
                      child: KycUploadTile(
                        title: LocaleKeys.idFrontLabel,
                        fileName: data.frontIdFileName,
                        image: data.frontIdImage,
                        onTap: onPickFrontId,
                      ),
                    ),
                    14.szH,
                    _KycUploadValidationField(
                      fieldKey: backIdFieldKey,
                      value: data.backIdFileName,
                      isRequired: !existingAccount,
                      child: KycUploadTile(
                        title: LocaleKeys.idBackLabel,
                        fileName: data.backIdFileName,
                        image: data.backIdImage,
                        onTap: onPickBackId,
                      ),
                    ),
                    14.szH,
                    _KycUploadValidationField(
                      fieldKey: selfieFieldKey,
                      value: data.selfieFileName,
                      isRequired: !existingAccount,
                      child: KycUploadTile(
                        title: existingAccount
                            ? LocaleKeys.kycOptionalSelfie
                            : LocaleKeys.selfiePhoto,
                        fileName: data.selfieFileName,
                        image: data.selfieImage,
                        onTap: onCaptureSelfie,
                        emptyIcon: Icons.add_a_photo_outlined,
                        emptyTitle: LocaleKeys.capturePhoto,
                        emptySubtitle: null,
                      ),
                    ),
                    14.szH,
                    KycPrivacyCard(
                      title: LocaleKeys.kycUploadPrivacyTitle,
                      subtitle: LocaleKeys.idPhotoNeverVisible,
                    ),
                    24.szH,
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _NationalIdField extends StatelessWidget {
  const _NationalIdField({
    required this.fieldKey,
    required this.controller,
    required this.validator,
    required this.valueLength,
    required this.onChanged,
    required this.isRequired,
  });

  final GlobalKey fieldKey;
  final TextEditingController controller;
  final FormFieldValidator<String> validator;
  final int valueLength;
  final ValueChanged<String?> onChanged;
  final bool isRequired;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text.rich(
          TextSpan(
            text: '${LocaleKeys.nationalId} ',
            style: AppTextStyles.extraBold.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 14.sp,
            ),
            children: [
              TextSpan(
                text: isRequired ? '*' : '',
                style: AppTextStyles.base.copyWith(color: AppColors.sokoonRose),
              ),
            ],
          ),
        ),
        8.szH,
        DefaultTextField(
          key: fieldKey,
          controller: controller,
          title: LocaleKeys.nationalIdHint,
          inputType: TextInputType.number,
          inputFormatters: [FilteringTextInputFormatter.digitsOnly],
          validator: validator,
          maxLength: 14,
          textAlign: TextAlign.start,
          borderRadius: 12.r,
          fillColor: AppColors.white,
          borderColor: AppColors.grayPale,
          contentPadding: EdgeInsets.symmetric(
            horizontal: 16.w,
            vertical: 14.h,
          ),
          style: AppTextStyles.semiBold.copyWith(
            color: AppColors.sokoonNavy,
            fontSize: 15.sp,
          ),
          onChanged: onChanged,
        ),
        6.szH,
        AppText(
          '$valueLength/14 ${LocaleKeys.digits}',
          style: AppTextStyles.regular11.copyWith(
            color: AppColors.sokoonGray,
            fontSize: 11.sp,
            height: 1.45,
          ),
        ),
        10.szH,
        Container(
          padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 10.h),
          decoration: BoxDecoration(
            color: AppColors.mintPale,
            borderRadius: BorderRadius.circular(8.r),
            border: Border.all(color: AppColors.tealAlpha09),
          ),
          child: Row(
            spacing: 8.w,
            children: [
              Icon(
                Icons.info_outline_rounded,
                color: AppColors.sokoonTeal,
                size: 16.r,
              ),
              Expanded(
                child: AppText(
                  LocaleKeys.nationalIdPrivacyHint,
                  style: AppTextStyles.regular11.copyWith(
                    color: AppColors.sokoonTeal,
                    fontSize: 11.sp,
                    height: 1.45,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _KycUploadValidationField extends StatelessWidget {
  const _KycUploadValidationField({
    required this.fieldKey,
    required this.value,
    required this.child,
    this.isRequired = true,
  });

  final GlobalKey<FormFieldState<String>> fieldKey;
  final String? value;
  final Widget child;
  final bool isRequired;

  @override
  Widget build(BuildContext context) {
    return ValidationHost<String>(
      key: fieldKey,
      initialValue: value,
      validator: isRequired ? Validators.validateEmpty : (_) => null,
      builderWidget: (field) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 6.h,
        children: [
          child,
          if (field.hasError)
            AppText(
              field.errorText ?? '',
              style: AppTextStyles.regular11.copyWith(
                color: AppColors.sokoonRose,
                fontSize: 11.sp,
                height: 1.45,
              ),
            ),
        ],
      ),
    );
  }
}

class _KycUploadSubmitBar extends StatelessWidget {
  const _KycUploadSubmitBar({
    required this.onSubmit,
    required this.existingAccount,
  });

  final Future<void> Function() onSubmit;
  final bool existingAccount;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Container(
        padding: EdgeInsets.fromLTRB(16.w, 10.h, 16.w, 16.h),
        decoration: const BoxDecoration(
          color: AppColors.white,
          border: Border(top: BorderSide(color: AppColors.grayPale)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          spacing: 8.h,
          children: [
            AppText(
              existingAccount
                  ? LocaleKeys.kycExistingDocumentsHint
                  : LocaleKeys.enterNationalIdToContinue,
              style: AppTextStyles.regular12.copyWith(
                color: AppColors.sokoonGray,
                fontSize: 12.sp,
                height: 1.45,
              ),
              textAlign: TextAlign.center,
            ),
            AppLoadingButton(
              asyncCall: (_) => onSubmit(),
              title: LocaleKeys.nextReviewData,
              buttonColor: AppColors.sokoonTeal,
              textColor: AppColors.white,
              borderRadius: 14.r,
              height: 52.h,
              width: double.infinity,
              textStyle: AppTextStyles.bold16.copyWith(
                fontSize: 16.sp,
                height: 1.45,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
