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
import 'package:sokoun_app/features/auth/data/models/kyc_upload_documents_data.dart';
import 'package:sokoun_app/features/auth/data/models/register.dart';
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

class _KycUploadDocumentsScreenState extends State<KycUploadDocumentsScreen> {
  final TextEditingController _nationalIdController = TextEditingController();
  final ValueNotifier<KycUploadDocumentsData> _dataNotifier = ValueNotifier(
    const KycUploadDocumentsData(),
  );

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

    _updateData(
      (data) => data.copyWith(
        frontIdImage: image,
        frontIdFileName: _fileNameFrom(image),
      ),
    );
  }

  Future<void> _pickBackIdImage() async {
    final File? image = await Helpers.getImageFromCameraOrDevice();
    if (!mounted || image == null) {
      return;
    }

    _updateData(
      (data) => data.copyWith(
        backIdImage: image,
        backIdFileName: _fileNameFrom(image),
      ),
    );
  }

  Future<void> _captureSelfieImage() async {
    final File? image = await Helpers.getImageFromCameraOrDevice();
    if (!mounted || image == null) {
      return;
    }

    _updateData(
      (data) => data.copyWith(
        selfieImage: image,
        selfieFileName: _fileNameFrom(image),
      ),
    );
  }

  Widget _buildDataListener(
    Widget Function(KycUploadDocumentsData data) builder,
  ) {
    return ValueListenableBuilder<KycUploadDocumentsData>(
      valueListenable: _dataNotifier,
      builder: (context, data, _) => builder(data),
    );
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
                      (data) => KycUploadTile(
                        title: LocaleKeys.idFrontLabel,
                        fileName: data.frontIdFileName,
                        onTap: _pickFrontIdImage,
                      ),
                    ),
                    14.szH,
                    _buildDataListener(
                      (data) => KycUploadTile(
                        title: LocaleKeys.idBackLabel,
                        fileName: data.backIdFileName,
                        onTap: _pickBackIdImage,
                      ),
                    ),
                    14.szH,
                    _buildDataListener(
                      (data) => KycUploadTile(
                        title: LocaleKeys.selfiePhoto,
                        fileName: data.selfieFileName,
                        onTap: _captureSelfieImage,
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
              _buildDataListener(
                (data) => AppLoadingButton(
                  asyncCall: _submit,
                  title: LocaleKeys.nextReviewData,
                  buttonColor: data.canSubmit
                      ? AppColors.sokoonTeal
                      : AppColors.sokoonMuted,
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
    );
  }
}
