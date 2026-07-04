import 'package:flutter/material.dart';

class ValidationHost<T> extends FormField<T> {
  final Widget Function(FormFieldState<T> state) builderWidget;
  final AutovalidateMode validationMode;

  ValidationHost({super.key,
    required this.builderWidget,
    required FormFieldValidator<T> validator,
    this.validationMode = AutovalidateMode.onUserInteraction,
    FormFieldSetter<T>? onSaved,
    T? initialValue,
  }) : super(
    onSaved: onSaved,
    validator: validator,
    initialValue: initialValue,
    builder: (field) => builderWidget(field),
    autovalidateMode: validationMode,
  );
}
//