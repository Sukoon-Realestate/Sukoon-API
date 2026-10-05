import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

/// Gives a selection control inline errors using its current presentation value.
class SokounValidationField extends StatelessWidget {
  const SokounValidationField({
    super.key,
    required this.value,
    required this.validator,
    required this.child,
  });

  final String? value;
  final FormFieldValidator<String> validator;
  final Widget child;

  @override
  Widget build(BuildContext context) => FormField<String>(
    validator: (_) => validator(value),
    builder: (field) => Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        child,
        if (field.hasError && validator(value) != null)
          Semantics(
            liveRegion: true,
            child: Padding(
              padding: EdgeInsets.only(top: 8.h),
              child: AppText(
                field.errorText!,
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
