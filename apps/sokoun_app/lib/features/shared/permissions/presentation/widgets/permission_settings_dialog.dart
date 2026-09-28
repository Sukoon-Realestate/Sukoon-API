import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class PermissionSettingsDialog extends StatelessWidget {
  const PermissionSettingsDialog({super.key, required this.description});

  final String description;

  static Future<bool?> show(BuildContext context, String description) =>
      showDialog<bool>(
        context: context,
        builder: (_) => PermissionSettingsDialog(description: description),
      );

  @override
  Widget build(BuildContext context) => AlertDialog(
    backgroundColor: AppColors.white,
    title: AppText(
      LocaleKeys.permissionSettingsTitle,
      color: AppColors.sokoonNavy,
      fontSize: 18.sp,
      fontWeight: FontWeight.w700,
    ),
    content: AppText(
      description,
      color: AppColors.sokoonGray,
      fontSize: 14.sp,
      height: 1.5,
    ),
    actions: [
      TextButton(
        onPressed: () => Go.back(false),
        child: AppText(
          LocaleKeys.permissionNotNow,
          color: AppColors.sokoonGray,
        ),
      ),
      TextButton(
        onPressed: () => Go.back(true),
        child: AppText(
          LocaleKeys.permissionOpenSettings,
          color: AppColors.sokoonTeal,
          fontWeight: FontWeight.w700,
        ),
      ),
    ],
  );
}
