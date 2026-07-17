import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';
import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';
import 'package:sokoun_app/features/auth/presentation/cubits/register.dart';

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

class KycDocumentUploadData {
  const KycDocumentUploadData({
    required this.nationalId,
    required this.frontIdImage,
    required this.backIdImage,
    required this.selfieImage,
  });

  final String nationalId;
  final File? frontIdImage;
  final File? backIdImage;
  final File? selfieImage;
}

class _KycUploadDocumentsScreenState extends State<KycUploadDocumentsScreen> {
  final TextEditingController _nationalIdController = TextEditingController();
  File? _frontIdImage;
  File? _backIdImage;
  File? _selfieImage;
  String? _frontIdFileName;
  String? _backIdFileName;
  String? _selfieFileName;

  @override
  void dispose() {
    _nationalIdController.dispose();
    super.dispose();
  }

  bool get _canSubmit {
    return _nationalIdController.text.trim().length == 14 &&
        (_frontIdImage != null || _frontIdFileName != null) &&
        (_backIdImage != null || _backIdFileName != null) &&
        (_selfieImage != null || _selfieFileName != null);
  }

  Future<void> _submit(BuildContext context) async {
    if (!_canSubmit) {
      return;
    }

    final KycDocumentUploadData data = KycDocumentUploadData(
      nationalId: _nationalIdController.text.trim(),
      frontIdImage: _frontIdImage,
      backIdImage: _backIdImage,
      selfieImage: _selfieImage,
    );

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

    setState(() {
      _frontIdImage = image;
      _frontIdFileName = _fileNameFrom(image);
    });
  }

  Future<void> _pickBackIdImage() async {
    final File? image = await Helpers.getImageFromCameraOrDevice();
    if (!mounted || image == null) {
      return;
    }

    setState(() {
      _backIdImage = image;
      _backIdFileName = _fileNameFrom(image);
    });
  }

  Future<void> _captureSelfieImage() async {
    final File? image = await Helpers.getImageFromCameraOrDevice();
    if (!mounted || image == null) {
      return;
    }

    setState(() {
      _selfieImage = image;
      _selfieFileName = _fileNameFrom(image);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
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
                      controller: _nationalIdController,
                      title: LocaleKeys.nationalIdHint,
                      inputType: TextInputType.number,
                      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
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
                      onChanged: (_) => setState(() {}),
                    ),
                    6.szH,
                    AppText(
                      '${_nationalIdController.text.length}/14 ${LocaleKeys.digits}',
                      color: AppColors.sokoonGray,
                      fontSize: 11.sp,
                      fontWeight: FontWeight.w400,
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
                    KycUploadTile(
                      title: LocaleKeys.idFrontLabel,
                      fileName: _frontIdFileName,
                      onTap: _pickFrontIdImage,
                    ),
                    14.szH,
                    KycUploadTile(
                      title: LocaleKeys.idBackLabel,
                      fileName: _backIdFileName,
                      onTap: _pickBackIdImage,
                    ),
                    14.szH,
                    KycUploadTile(
                      title: LocaleKeys.selfiePhoto,
                      fileName: _selfieFileName,
                      onTap: _captureSelfieImage,
                      emptyIcon: Icons.add_a_photo_outlined,
                      emptyTitle: LocaleKeys.capturePhoto,
                      emptySubtitle: null,
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
      ),
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
              AppLoadingButton(
                asyncCall: _submit,
                title: LocaleKeys.nextReviewData,
                buttonColor: _canSubmit
                    ? AppColors.sokoonTeal
                    : AppColors.sokoonMuted,
                textColor: AppColors.white,
                borderRadius: 14.r,
                height: 52.h,
                width: double.infinity,
                fontSize: 16.sp,
                fontWeight: FontWeight.w700,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
