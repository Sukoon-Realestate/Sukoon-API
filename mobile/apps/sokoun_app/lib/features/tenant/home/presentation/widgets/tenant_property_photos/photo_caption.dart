import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class TenantPropertyPhotoCaption extends StatelessWidget {
  const TenantPropertyPhotoCaption({
    super.key,
    required this.name,
    required this.description,
    required this.index,
    required this.total,
  });

  final String name;
  final String description;
  final int index;
  final int total;

  @override
  Widget build(BuildContext context) => Column(
    mainAxisSize: MainAxisSize.min,
    crossAxisAlignment: CrossAxisAlignment.stretch,
    spacing: 6.h,
    children: [
      AppText(
        '${index + 1} / $total — $name',
        style: AppTextStyles.bold14.copyWith(color: AppColors.white),
        textAlign: TextAlign.center,
      ),
      if (description.trim().isNotEmpty)
        AppText(
          description,
          style: AppTextStyles.regular13.copyWith(
            color: AppColors.white.withValues(alpha: .8),
          ),
          textAlign: TextAlign.center,
        ),
    ],
  );
}
