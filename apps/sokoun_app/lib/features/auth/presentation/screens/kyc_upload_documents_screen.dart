import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';
import 'package:melos_core/core/widgets/first_validation_error_form.dart';
import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';
import 'package:melos_core/core/widgets/validation_helper.dart';
import 'package:sokoun_app/features/auth/data/models/kyc_upload_documents_data.dart';
import 'package:sokoun_app/features/auth/data/models/register.dart';
import 'package:sokoun_app/features/auth/presentation/cubits/register.dart';

import '../widgets/auth_scaffold.dart';
import '../widgets/kyc/kyc_flow_header.dart';
import '../widgets/kyc/kyc_privacy_card.dart';
import '../widgets/kyc/kyc_progress_bar.dart';
import '../widgets/kyc/kyc_upload_tile.dart';

class KycUploadDocumentsScreen extends StatefulWidget {
  const KycUploadDocumentsScreen({
    super.key,
    this.onBack,
    this.onSubmit,
    this.onRegisterSuccess,
  });

  final VoidCallback? onBack;
  final ValueChanged<KycDocumentUploadData>? onSubmit;
  final VoidCallback? onRegisterSuccess;

  @override
  State<KycUploadDocumentsScreen> createState() =>
      _KycUploadDocumentsScreenState();
}

class _KycUploadDocumentsScreenState extends State<KycUploadDocumentsScreen> {
  final GlobalKey _nationalIdFieldKey = GlobalKey();
  final GlobalKey<FormFieldState<String>> _frontIdFieldKey =
      GlobalKey<FormFieldState<String>>();
  final GlobalKey<FormFieldState<String>> _backIdFieldKey =
      GlobalKey<FormFieldState<String>>();
  final GlobalKey<FormFieldState<String>> _selfieFieldKey =
      GlobalKey<FormFieldState<String>>();
  final TextEditingController _nationalIdController = TextEditingController();
  final ValueNotifier<KycUploadDocumentsData> _dataNotifier = ValueNotifier(
    const KycUploadDocumentsData(),
  );
  Completer<void>? _submitCompleter;

  @override
  void dispose() {
    _nationalIdController.dispose();
    _dataNotifier.dispose();
    super.dispose();
  }

  void _updateData(
    KycUploadDocumentsData Function(KycUploadDocumentsData data) update,
  ) {
    _dataNotifier.value = update(_dataNotifier.value);
  }

  String? _validateNationalId(String? value) {
    final String? emptyError = Validators.validateEmpty(value);
    if (emptyError != null) {
      return emptyError;
    }

    if (value!.trim().length != 14) {
      return LocaleKeys.filedValidation;
    }

    return null;
  }

  List<FirstValidationErrorField> _validationFields() {
    final KycUploadDocumentsData data = _dataNotifier.value;
    return [
      FirstValidationErrorField(
        fieldKey: _nationalIdFieldKey,
        title: LocaleKeys.nationalId,
        value: _nationalIdController.text,
        validator: _validateNationalId,
      ),
      FirstValidationErrorField(
        fieldKey: _frontIdFieldKey,
        title: LocaleKeys.idFrontLabel,
        value: data.frontIdFileName,
        validator: Validators.validateEmpty,
      ),
      FirstValidationErrorField(
        fieldKey: _backIdFieldKey,
        title: LocaleKeys.idBackLabel,
        value: data.backIdFileName,
        validator: Validators.validateEmpty,
      ),
      FirstValidationErrorField(
        fieldKey: _selfieFieldKey,
        title: LocaleKeys.selfiePhoto,
        value: data.selfieFileName,
        validator: Validators.validateEmpty,
      ),
    ];
  }

  Future<void> _submit(BuildContext context) async {
    final KycUploadDocumentsData formData = _dataNotifier.value;
    if (!formData.canSubmit) {
      return;
    }

    final KycDocumentUploadData data = formData.toUploadData();

    if (widget.onSubmit != null) {
      widget.onSubmit?.call(data);
      return;
    }

    final RegisterCubit registerCubit = context.read<RegisterCubit>();
    registerCubit.updateKycDocuments(
      nationalId: data.nationalId,
      frontIdImage: data.frontIdImage,
      backIdImage: data.backIdImage,
      selfieImage: data.selfieImage,
    );

    await registerCubit.register(onSuccess: widget.onRegisterSuccess);
  }

  String _fileNameFrom(File image) {
    return image.uri.pathSegments.isEmpty
        ? image.path
        : image.uri.pathSegments.last;
  }

  Future<void> _pickFrontIdImage() async {
    final File? image = await Helpers.getImageFromCameraOrDevice();
    if (!mounted || image == null) {
      return;
    }

    final String fileName = _fileNameFrom(image);
    _updateData(
      (data) => data.copyWith(frontIdImage: image, frontIdFileName: fileName),
    );
    _frontIdFieldKey.currentState?.didChange(fileName);
  }

  Future<void> _pickBackIdImage() async {
    final File? image = await Helpers.getImageFromCameraOrDevice();
    if (!mounted || image == null) {
      return;
    }

    final String fileName = _fileNameFrom(image);
    _updateData(
      (data) => data.copyWith(backIdImage: image, backIdFileName: fileName),
    );
    _backIdFieldKey.currentState?.didChange(fileName);
  }

  Future<void> _captureSelfieImage() async {
    final File? image = await Helpers.getImageFromCameraOrDevice();
    if (!mounted || image == null) {
      return;
    }

    final String fileName = _fileNameFrom(image);
    _updateData(
      (data) => data.copyWith(selfieImage: image, selfieFileName: fileName),
    );
    _selfieFieldKey.currentState?.didChange(fileName);
  }

  Widget _buildDataListener(
    Widget Function(KycUploadDocumentsData data) builder,
  ) {
    return ValueListenableBuilder<KycUploadDocumentsData>(
      valueListenable: _dataNotifier,
      builder: (context, data, _) => builder(data),
    );
  }

  Widget _buildUploadValidationField({
    required GlobalKey<FormFieldState<String>> fieldKey,
    required String? value,
    required Widget child,
  }) {
    return ValidationHost<String>(
      key: fieldKey,
      initialValue: value,
      validator: Validators.validateEmpty,
      builderWidget: (field) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            child,
            if (field.hasError) ...[
              6.szH,
              AppText(
                field.errorText ?? '',
                color: AppColors.sokoonRose,
                fontSize: 11.sp,
                fontWeight: FontWeight.w400,
              ),
            ],
          ],
        );
      },
    );
  }

  Future<void> _submitForm(VoidCallback submit) async {
    final Completer<void> completer = Completer<void>();
    _submitCompleter = completer;
    submit();
    await completer.future;
  }

  void _completeSubmit() {
    final Completer<void>? completer = _submitCompleter;
    _submitCompleter = null;

    if (completer != null && !completer.isCompleted) {
      completer.complete();
    }
  }

  @override
  Widget build(BuildContext context) {
    return FirstValidationErrorForm(
      validationFields: _validationFields,
      onValidationError: (_) => _completeSubmit(),
      onValid: () async {
        try {
          await _submit(context);
        } finally {
          _completeSubmit();
        }
      },
      builder: (context, submit) {
        return AuthScaffold(
          padding: EdgeInsets.zero,
          bottomNavigationBar: SafeArea(
            child: Container(
              padding: EdgeInsets.fromLTRB(16.w, 10.h, 16.w, 16.h),
              decoration: const BoxDecoration(
                color: AppColors.white,
                border: Border(top: BorderSide(color: AppColors.grayPale)),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  AppText(
                    LocaleKeys.enterNationalIdToContinue,
                    color: AppColors.sokoonGray,
                    fontSize: 12.sp,
                    fontWeight: FontWeight.w400,
                    textAlign: TextAlign.center,
                  ),
                  8.szH,
                  _buildDataListener(
                    (data) => AppLoadingButton(
                      asyncCall: (_) async => await _submitForm(submit),
                      title: LocaleKeys.nextReviewData,
                      buttonColor: AppColors.tealOrGoldBasedRole,
                      textColor: AppColors.white,
                      borderRadius: 14.r,
                      height: 52.h,
                      width: double.infinity,
                      fontSize: 16.sp,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
          ),
          child: Column(
            children: [
              KycFlowHeader(
                title: LocaleKeys.uploadDocumentsTitle,
                onBack: widget.onBack,
              ),
              Expanded(
                child: SingleChildScrollView(
                  padding: EdgeInsets.all(16.w),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const KycProgressBar(currentStep: 2),
                      16.szH,
                      AppText(
                        LocaleKeys.uploadClearIdImage,
                        color: AppColors.sokoonGray,
                        fontSize: 13.sp,
                        fontWeight: FontWeight.w400,
                      ),
                      18.szH,
                      Text.rich(
                        TextSpan(
                          text: '${LocaleKeys.nationalId} ',
                          style: TextStyle(
                            color: AppColors.sokoonNavy,
                            fontFamily: ConstantManager.fontFamily,
                            fontSize: 14.sp,
                            fontWeight: FontWeight.w800,
                          ),
                          children: const [
                            TextSpan(
                              text: '*',
                              style: TextStyle(color: AppColors.sokoonRose),
                            ),
                          ],
                        ),
                      ),
                      8.szH,
                      DefaultTextField(
                        key: _nationalIdFieldKey,
                        controller: _nationalIdController,
                        title: LocaleKeys.nationalIdHint,
                        inputType: TextInputType.number,
                        inputFormatters: [
                          FilteringTextInputFormatter.digitsOnly,
                        ],
                        validator: _validateNationalId,
                        maxLength: 14,
                        textAlign: TextAlign.right,
                        borderRadius: 12.r,
                        fillColor: AppColors.white,
                        borderColor: AppColors.grayPale,
                        contentPadding: EdgeInsets.symmetric(
                          horizontal: 16.w,
                          vertical: 14.h,
                        ),
                        style: TextStyle(
                          color: AppColors.sokoonNavy,
                          fontFamily: ConstantManager.fontFamily,
                          fontSize: 15.sp,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 0,
                        ),
                        onChanged: (value) => _updateData(
                          (data) =>
                              data.copyWith(nationalId: (value ?? '').trim()),
                        ),
                      ),
                      6.szH,
                      _buildDataListener(
                        (data) => AppText(
                          '${data.nationalId.length}/14 ${LocaleKeys.digits}',
                          color: AppColors.sokoonGray,
                          fontSize: 11.sp,
                          fontWeight: FontWeight.w400,
                        ),
                      ),
                      10.szH,
                      Container(
                        padding: EdgeInsets.symmetric(
                          horizontal: 12.w,
                          vertical: 10.h,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF0FDF9),
                          borderRadius: BorderRadius.circular(8.r),
                          border: Border.all(color: AppColors.tealAlpha09),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              Icons.info_outline_rounded,
                              color: AppColors.sokoonTeal,
                              size: 16.r,
                            ),
                            8.szW,
                            Expanded(
                              child: AppText(
                                LocaleKeys.nationalIdPrivacyHint,
                                color: AppColors.sokoonTeal,
                                fontSize: 11.sp,
                                fontWeight: FontWeight.w400,
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                      ),
                      18.szH,
                      _buildDataListener(
                        (data) => _buildUploadValidationField(
                          fieldKey: _frontIdFieldKey,
                          value: data.frontIdFileName,
                          child: KycUploadTile(
                            title: LocaleKeys.idFrontLabel,
                            fileName: data.frontIdFileName,
                            image: data.frontIdImage,
                            onTap: _pickFrontIdImage,
                          ),
                        ),
                      ),
                      14.szH,
                      _buildDataListener(
                        (data) => _buildUploadValidationField(
                          fieldKey: _backIdFieldKey,
                          value: data.backIdFileName,
                          child: KycUploadTile(
                            title: LocaleKeys.idBackLabel,
                            fileName: data.backIdFileName,
                            image: data.backIdImage,
                            onTap: _pickBackIdImage,
                          ),
                        ),
                      ),
                      14.szH,
                      _buildDataListener(
                        (data) => _buildUploadValidationField(
                          fieldKey: _selfieFieldKey,
                          value: data.selfieFileName,
                          child: KycUploadTile(
                            title: LocaleKeys.selfiePhoto,
                            fileName: data.selfieFileName,
                            image: data.selfieImage,
                            onTap: _captureSelfieImage,
                            emptyIcon: Icons.add_a_photo_outlined,
                            emptyTitle: LocaleKeys.capturePhoto,
                            emptySubtitle: null,
                          ),
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
            ],
          ),
        );
      },
    );
  }
}
