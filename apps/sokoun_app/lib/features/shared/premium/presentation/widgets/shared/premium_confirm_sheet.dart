import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';

class PremiumConfirmSheet extends StatelessWidget {
  const PremiumConfirmSheet({
    super.key,
    required this.title,
    required this.details,
    required this.actionLabel,
  });
  final String title;
  final Widget details;
  final String actionLabel;
  static Future<bool> show(
    BuildContext context, {
    required String title,
    required Widget details,
    required String actionLabel,
  }) async =>
      await showModalBottomSheet<bool>(
        context: context,
        useSafeArea: true,
        isScrollControlled: true,
        showDragHandle: true,
        builder: (_) => PremiumConfirmSheet(
          title: title,
          details: details,
          actionLabel: actionLabel,
        ),
      ) ??
      false;
  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    padding: EdgeInsets.fromLTRB(20.w, 16.h, 20.w, 24.h),
    child: Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(title, fontWeight: FontWeight.bold),
        16.szH,
        details,
        24.szH,
        FilledButton(
          onPressed: () => Go.back(true),
          child: AppText(actionLabel),
        ),
        TextButton(
          onPressed: () => Go.back(false),
          child: AppText(LocaleKeys.cancel),
        ),
      ],
    ),
  );
}
