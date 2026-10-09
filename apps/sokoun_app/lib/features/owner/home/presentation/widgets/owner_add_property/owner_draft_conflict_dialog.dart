import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class OwnerDraftConflictDialog extends StatelessWidget {
  const OwnerDraftConflictDialog({
    super.key,
    required this.currentTitle,
    required this.draftTitle,
  });
  final String currentTitle;
  final String draftTitle;
  @override
  Widget build(BuildContext context) => AlertDialog(
    title: AppText(LocaleKeys.professionalReviewChanges),
    content: SingleChildScrollView(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppText(LocaleKeys.professionalDraftConflict),
          const SizedBox(height: 12),
          AppText(currentTitle),
          const Divider(),
          AppText(draftTitle),
        ],
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Go.back(false),
        child: AppText(LocaleKeys.workspaceStay),
      ),
      TextButton(
        onPressed: () => Go.back(true),
        child: AppText(LocaleKeys.professionalReviewChanges),
      ),
    ],
  );
}
