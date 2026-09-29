import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class PropertyReviewSection extends StatelessWidget {
  const PropertyReviewSection({
    super.key,
    required this.title,
    required this.lines,
    required this.onEdit,
  });

  final String title;
  final List<String> lines;
  final VoidCallback onEdit;

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 12),
    padding: const EdgeInsetsDirectional.fromSTEB(16, 8, 8, 16),
    decoration: BoxDecoration(
      color: AppColors.white,
      border: Border.all(color: AppColors.sokoonBorder),
      borderRadius: BorderRadius.circular(16),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: AppText(
                title,
                style: AppTextStyles.bold16.copyWith(
                  fontSize: 16,
                  color: AppColors.sokoonNavy,
                  height: 1.45,
                ),
              ),
            ),
            IconButton(
              tooltip: '${LocaleKeys.editData}: $title',
              onPressed: onEdit,
              icon: const Icon(
                Icons.edit_outlined,
                size: 20,
                color: AppColors.sokoonTeal,
              ),
            ),
          ],
        ),
        for (final line in lines.where((value) => value.trim().isNotEmpty))
          Padding(
            padding: const EdgeInsetsDirectional.only(end: 8, top: 4),
            child: AppText(
              line,
              style: AppTextStyles.regular14.copyWith(
                fontSize: 14,
                height: 1.5,
                color: AppColors.sokoonGray,
              ),
            ),
          ),
      ],
    ),
  );
}
