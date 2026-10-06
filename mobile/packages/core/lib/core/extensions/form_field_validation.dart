import 'package:flutter/material.dart';


extension FormFieldExtension on Widget {
  FormField<T> asFormField<T>({
    required FormFieldValidator<T>? validator,
    T? initialValue,
    CrossAxisAlignment crossAxisAlignment = CrossAxisAlignment.start,
    AutovalidateMode autovalidateMode = AutovalidateMode.onUserInteraction,
    bool enabled = true,
    FormFieldSetter<T>? onSaved,
    FormFieldBuilder<T>? builder,
  }) {
    return FormField<T>(
      validator: validator,
      initialValue: initialValue,
      autovalidateMode: autovalidateMode,
      enabled: enabled,
      onSaved: onSaved,
      builder: (FormFieldState<T> state) {
        return Column(
          crossAxisAlignment: crossAxisAlignment,
          children: [
            this,
            if (state.errorText != null)
              Padding(
                padding: const EdgeInsets.only(top: 8.0),
                child: Text(
                  state.errorText!,
                  // todo: change to errorStyle
                  style: const TextStyle(
                    color: Colors.red,
                    fontSize: 12.0,
                  ),
                ),
              ),
          ],
        );
      },
    );
  }
}
