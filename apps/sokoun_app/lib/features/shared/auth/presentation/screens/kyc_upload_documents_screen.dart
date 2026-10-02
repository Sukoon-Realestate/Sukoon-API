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
import '../cubits/complete_registration_cubit.dart';
import '../../data/models/complete_registration_result.dart';
import 'kyc_pending_screen.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/shared_widgets/unsaved_changes_guard.dart';

class KycUploadDocumentsScreen extends StatefulWidget {
  const KycUploadDocumentsScreen({
    super.key,
    this.onBack,
    this.onRegisterSuccess,
    this.existingAccount = false,
  });

  final VoidCallback? onBack;
  final ValueChanged<RegisterBody>? onRegisterSuccess;
  final bool existingAccount;

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
  CompleteRegistrationCubit? _completionCubit;
  final ValueNotifier<String?> _submissionMessage = ValueNotifier(null);
  bool _submitted = false;

  @override
  void initState() {
    super.initState();
    if (widget.existingAccount) _completionCubit = CompleteRegistrationCubit();
  }

  @override
  void dispose() {
    _nationalIdController.dispose();
    _dataNotifier.dispose();
    _completionCubit?.close();
    _submissionMessage.dispose();
    _completeSubmit();
    super.dispose();
  }

  void _updateData(
    KycUploadDocumentsData Function(KycUploadDocumentsData data) update,
  ) {
    _dataNotifier.value = update(_dataNotifier.value);
  }

  String? _validateNationalId(String? value) {
    if (widget.existingAccount && (value?.trim().isEmpty ?? true)) return null;
    return Validators.validateEgyptianNationalId(value);
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
      if (!widget.existingAccount)
        FirstValidationErrorField(
          fieldKey: _frontIdFieldKey,
          title: LocaleKeys.idFrontLabel,
          value: data.frontIdFileName,
          validator: Validators.validateEmpty,
        ),
      if (!widget.existingAccount)
        FirstValidationErrorField(
          fieldKey: _backIdFieldKey,
          title: LocaleKeys.idBackLabel,
          value: data.backIdFileName,
          validator: Validators.validateEmpty,
        ),
      if (!widget.existingAccount)
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
    if (widget.existingAccount) {
      _submissionMessage.value = null;
      await _completionCubit!.submit(
        formData,
        onResult: (result) {
          if (!mounted) return;
          if (result.isComplete) {
            _submitted = true;
            Go.off(const KycPendingScreen(existingAccount: true));
          } else {
            _submissionMessage.value = _missingFieldsMessage(result);
          }
        },
      );
      if (mounted && _completionCubit!.state.isError) {
        _submissionMessage.value = _completionCubit!.state.msg;
      }
      return;
    }
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

  String _missingFieldsMessage(CompleteRegistrationResult result) {
    final String fields = result.missingFields
        .map(
          (field) => switch (field) {
            'national_id' => LocaleKeys.nationalId,
            'front_id_image' => LocaleKeys.idFrontLabel,
            'back_id_image' => LocaleKeys.idBackLabel,
            'selfie_image' => LocaleKeys.selfiePhoto,
            _ => field,
          },
        )
        .join(', ');
    return fields.isEmpty
        ? LocaleKeys.kycIncompleteSubmission
        : '${LocaleKeys.kycMissingFields}: $fields';
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
    if (_submitCompleter != null) return;
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
    final Widget form = FirstValidationErrorForm(
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
          existingAccount: widget.existingAccount,
          submissionMessage: _submissionMessage,
        );
      },
    );
    if (!widget.existingAccount) return form;
    return UnsavedChangesGuard(
      hasChanges: () => !_submitted && _dataNotifier.value.hasChanges,
      isSaving: () => _completionCubit?.isLoading ?? false,
      child: form,
    );
  }
}
