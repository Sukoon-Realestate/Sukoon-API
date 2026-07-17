import 'package:flutter/material.dart';

import '../extensions/context_extension.dart';
import '../shared/base_state.dart';
import 'toast_messages/toast_message.dart';

typedef FirstValidationErrorFormBuilder =
    Widget Function(BuildContext context, VoidCallback submit);

typedef FirstValidationErrorFieldsBuilder =
    List<FirstValidationErrorField> Function();

class FirstValidationErrorForm extends StatefulWidget {
  const FirstValidationErrorForm({
    super.key,
    this.formKey,
    required this.validationFields,
    required this.onValid,
    required this.builder,
    this.autovalidateMode,
    this.hideKeyboardOnSubmit = true,
    this.showToast = true,
    this.scrollToField = true,
    this.scrollDuration = const Duration(milliseconds: 350),
    this.scrollCurve = Curves.easeOutCubic,
    this.scrollAlignment = 0.12,
    this.onValidationError,
  });

  final GlobalKey<FormState>? formKey;
  final FirstValidationErrorFieldsBuilder validationFields;
  final VoidCallback onValid;
  final FirstValidationErrorFormBuilder builder;
  final AutovalidateMode? autovalidateMode;
  final bool hideKeyboardOnSubmit;
  final bool showToast;
  final bool scrollToField;
  final Duration scrollDuration;
  final Curve scrollCurve;
  final double scrollAlignment;
  final ValueChanged<FirstValidationError>? onValidationError;

  @override
  State<FirstValidationErrorForm> createState() =>
      _FirstValidationErrorFormState();
}

class _FirstValidationErrorFormState extends State<FirstValidationErrorForm> {
  final GlobalKey<FormState> _fallbackFormKey = GlobalKey<FormState>();

  GlobalKey<FormState> get _formKey => widget.formKey ?? _fallbackFormKey;

  void _submit() {
    if (widget.hideKeyboardOnSubmit) {
      context.hideKeyboard();
    }

    final FirstValidationError? firstValidationError = _firstValidationError;

    if (_formKey.currentState?.validate() != true) {
      if (firstValidationError != null) {
        _handleValidationError(firstValidationError);
      }
      return;
    }

    widget.onValid();
  }

  FirstValidationError? get _firstValidationError {
    for (final FirstValidationErrorField field in widget.validationFields()) {
      final String? error = field.validator(field.value);
      if (error != null && error.trim().isNotEmpty) {
        return FirstValidationError(field: field, message: error);
      }
    }

    return null;
  }

  void _handleValidationError(FirstValidationError error) {
    widget.onValidationError?.call(error);

    if (widget.showToast) {
      Messages.showToast(
        title: error.field.title,
        msg: error.message,
        status: BaseStatus.error,
      );
    }

    if (!widget.scrollToField) {
      return;
    }

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }

      final BuildContext? fieldContext = error.field.fieldKey.currentContext;
      if (fieldContext == null) {
        return;
      }

      Scrollable.ensureVisible(
        fieldContext,
        duration: widget.scrollDuration,
        curve: widget.scrollCurve,
        alignment: widget.scrollAlignment,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      autovalidateMode: widget.autovalidateMode,
      child: Builder(builder: (context) => widget.builder(context, _submit)),
    );
  }
}

class FirstValidationErrorField {
  const FirstValidationErrorField({
    required this.fieldKey,
    required this.title,
    required this.value,
    required this.validator,
  });

  final GlobalKey fieldKey;
  final String title;
  final String? value;
  final FormFieldValidator<String?> validator;
}

class FirstValidationError {
  const FirstValidationError({required this.field, required this.message});

  final FirstValidationErrorField field;
  final String message;
}
