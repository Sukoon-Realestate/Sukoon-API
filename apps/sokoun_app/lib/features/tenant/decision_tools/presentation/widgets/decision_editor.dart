import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import '../../data/models/decision_notebook.dart';
import '../cubits/decision_tools_cubit.dart';

class DecisionEditor extends StatefulWidget {
  const DecisionEditor({
    super.key,
    required this.cubit,
    required this.decision,
  });
  final DecisionToolsCubit cubit;
  final PropertyDecision decision;
  @override
  State<DecisionEditor> createState() => _DecisionEditorState();
}

class _DecisionEditorState extends State<DecisionEditor> {
  late final TextEditingController _list;
  late final TextEditingController _note;
  late final ValueNotifier<Set<String>> _checked;
  @override
  void initState() {
    super.initState();
    _list = TextEditingController(text: widget.decision.list);
    _note = TextEditingController(text: widget.decision.note);
    _checked = ValueNotifier(Set.of(widget.decision.checkedItems));
  }

  @override
  void dispose() {
    _list.dispose();
    _note.dispose();
    _checked.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Padding(
    padding: EdgeInsets.fromLTRB(
      20,
      8,
      20,
      MediaQuery.viewInsetsOf(context).bottom + 24,
    ),
    child: SingleChildScrollView(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(widget.decision.title, fontWeight: FontWeight.bold),
          const SizedBox(height: 8),
          AppText(LocaleKeys.freePrivateDeviceNotes),
          const SizedBox(height: 16),
          TextField(
            controller: _list,
            maxLength: 60,
            decoration: InputDecoration(
              labelText: LocaleKeys.freeDecisionList,
              hintText: LocaleKeys.freeDecisionListExample,
            ),
          ),
          TextField(
            controller: _note,
            maxLines: 4,
            maxLength: 4000,
            decoration: InputDecoration(labelText: LocaleKeys.freePrivateNotes),
          ),
          const SizedBox(height: 12),
          AppText(LocaleKeys.freeViewingChecklist, fontWeight: FontWeight.bold),
          ValueListenableBuilder<Set<String>>(
            valueListenable: _checked,
            builder: (context, checked, _) => Column(
              children: [
                for (final item in <String, String>{
                  'water': LocaleKeys.freeCheckWater,
                  'light': LocaleKeys.freeCheckLight,
                  'noise': LocaleKeys.freeCheckNoise,
                  'maintenance': LocaleKeys.freeCheckMaintenance,
                  'internet': LocaleKeys.freeCheckInternet,
                  'costs': LocaleKeys.freeCheckCosts,
                  'safety': LocaleKeys.freeCheckSafety,
                }.entries)
                  CheckboxListTile(
                    contentPadding: EdgeInsets.zero,
                    title: AppText(item.value),
                    value: checked.contains(item.key),
                    onChanged: (value) {
                      final next = Set<String>.of(checked);
                      value == true
                          ? next.add(item.key)
                          : next.remove(item.key);
                      _checked.value = next;
                    },
                  ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          AppLoadingButton(
            title: LocaleKeys.freeSaveNotes,
            asyncCall: (_) async {
              try {
                await widget.cubit.saveDecision(
                  widget.decision.copyWith(
                    list: _list.text.trim(),
                    note: _note.text.trim(),
                    checkedItems: Set.unmodifiable(_checked.value),
                  ),
                );
                if (context.mounted) Go.back(true);
              } catch (_) {
                Messages.showToast(msg: LocaleKeys.freeLocalSaveFailed);
              }
            },
          ),
        ],
      ),
    ),
  );
}
