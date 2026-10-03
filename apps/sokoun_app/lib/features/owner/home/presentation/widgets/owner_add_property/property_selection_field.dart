import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

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
  Widget build(BuildContext context) => FormField<bool>(
    validator: (_) => isValid ? null : message ?? LocaleKeys.fillField,
    builder: (state) => Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        child,
        if (state.errorText != null)
          Semantics(
            liveRegion: true,
            child: Padding(
              padding: const EdgeInsets.only(top: 8),
              child: AppText(
                state.errorText!,
                style: AppTextStyles.regular13.copyWith(
                  color: AppColors.sokoonRose,
                ),
              ),
            ),
          ),
      ],
    ),
  );
}
