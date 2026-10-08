import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

/// Natural-height labels remain readable in RTL and with large system text.
class FeatureDetailField extends StatelessWidget {
  const FeatureDetailField({
    super.key,
    required this.label,
    required this.value,
  });
  final String label, value;
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    spacing: 4,
    children: [
      AppText(
        label,
        color: context.appColor(AppColors.sokoonGray),
        fontWeight: FontWeight.w500,
      ),
      AppText(value, fontWeight: FontWeight.w600),
    ],
  );
}
