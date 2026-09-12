import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:melos_core/core/widgets/first_validation_error_form.dart';
import 'package:sokoun_app/features/shared/auth/data/models/kyc_upload_documents_data.dart';
import 'package:sokoun_app/features/shared/auth/data/models/register.dart';
import 'package:sokoun_app/features/shared/auth/presentation/cubits/register.dart';
import '../widgets/kyc/kyc_upload_documents_view.dart';

class KycUploadDocumentsScreen extends StatefulWidget {
  const KycUploadDocumentsScreen({
    super.key,
    this.onBack,
    this.onRegisterSuccess,
  });

  final VoidCallback? onBack;
  final ValueChanged<RegisterBody>? onRegisterSuccess;

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
        return KycUploadDocumentsView(
          dataListenable: _dataNotifier,
          nationalIdFieldKey: _nationalIdFieldKey,
          frontIdFieldKey: _frontIdFieldKey,
          backIdFieldKey: _backIdFieldKey,
          selfieFieldKey: _selfieFieldKey,
          nationalIdController: _nationalIdController,
          validateNationalId: _validateNationalId,
          onNationalIdChanged: (value) => _updateData(
            (data) => data.copyWith(nationalId: (value ?? '').trim()),
          ),
          onPickFrontId: _pickFrontIdImage,
          onPickBackId: _pickBackIdImage,
          onCaptureSelfie: _captureSelfieImage,
          onSubmit: () => _submitForm(submit),
          onBack: widget.onBack,
        );
      },
    );
  }
}
