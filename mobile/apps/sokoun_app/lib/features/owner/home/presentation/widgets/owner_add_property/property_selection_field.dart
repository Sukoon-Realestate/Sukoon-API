import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/sokoun_validation_field.dart';

/// Registers non-text controls with the step's form validation.
class PropertySelectionField extends StatelessWidget {
  const PropertySelectionField({
    super.key,
    required this.isValid,
    required this.child,
    this.message,
  });

  final bool isValid;
  final Widget child;
  final String? message;

  @override
  Widget build(BuildContext context) => SokounValidationField(
    value: isValid ? 'selected' : null,
    validator: (_) => isValid ? null : message ?? LocaleKeys.fillField,
    child: child,
  );
}
