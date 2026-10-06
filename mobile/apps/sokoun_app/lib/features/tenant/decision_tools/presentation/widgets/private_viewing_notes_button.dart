import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import '../cubits/decision_tools_cubit.dart';
import 'decision_editor.dart';

class PrivateViewingNotesButton extends StatelessWidget {
  const PrivateViewingNotesButton({
    super.key,
    required this.propertyId,
    required this.title,
  });
  final String propertyId;
  final String title;
  Future<void> _open(BuildContext context) async {
    final cubit = DecisionToolsCubit(
      accountId: UserModel.currentUser?.id ?? '',
    );
    try {
      await cubit.load();
      if (!context.mounted) return;
      await showModalBottomSheet<bool>(
        context: context,
        useSafeArea: true,
        isScrollControlled: true,
        showDragHandle: true,
        builder: (_) => DecisionEditor(
          cubit: cubit,
          decision: cubit.state.decisionFor(propertyId, title),
        ),
      );
    } catch (_) {
      Messages.showToast(msg: LocaleKeys.freeLocalSaveFailed);
    } finally {
      await cubit.close();
    }
  }

  @override
  Widget build(BuildContext context) => OutlinedButton.icon(
    onPressed: propertyId.isEmpty ? null : () => _open(context),
    icon: const Icon(Icons.checklist),
    label: AppText(LocaleKeys.freeViewingChecklist),
  );
}
