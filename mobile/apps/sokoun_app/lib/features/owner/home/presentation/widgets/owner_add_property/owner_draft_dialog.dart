import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../../../data/enums/owner_draft_action.dart';

class OwnerDraftDialog extends StatelessWidget {
  const OwnerDraftDialog({super.key, required this.isRecovery});
  final bool isRecovery;
  @override
  Widget build(BuildContext context) => AlertDialog(
    title: AppText(
      isRecovery ? LocaleKeys.freeResumeDraft : LocaleKeys.freeKeepDraft,
    ),
    content: AppText(
      isRecovery
          ? LocaleKeys.freeDraftRecovery
          : LocaleKeys.freeDraftExitDescription,
    ),
    actions: [
      if (!isRecovery)
        TextButton(
          onPressed: () => Go.back(OwnerDraftAction.stay),
          child: AppText(LocaleKeys.workspaceStay),
        ),
      TextButton(
        onPressed: () => Go.back(OwnerDraftAction.discard),
        child: AppText(LocaleKeys.freeDiscardLocalDraft),
      ),
      TextButton(
        onPressed: () => Go.back(
          isRecovery ? OwnerDraftAction.resume : OwnerDraftAction.saveAndLeave,
        ),
        child: AppText(
          isRecovery ? LocaleKeys.freeResumeDraft : LocaleKeys.freeSaveAndExit,
        ),
      ),
    ],
  );
}
