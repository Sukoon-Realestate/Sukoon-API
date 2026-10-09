import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'dart:async';
import 'package:flutter/material.dart';
import '../../data/models/text_form_draft.dart';
import '../cubits/draft_cubit.dart';
import 'draft_feedback.dart';

/// A form lifecycle adapter. Persistence remains owned by DraftCubit.
class TextDraftBinding {
  TextDraftBinding({
    required String flow,
    String entityId = '',
    String workspace = '',
    required this.fields,
    required this.capture,
    required this.restore,
    required this.context,
    required this.mounted,
  }) : cubit = DraftCubit(
         TextFormDraft.store(
           flow: flow,
           entityId: entityId,
           workspace: workspace,
         ),
       );
  final DraftCubit<TextFormDraft> cubit;
  final List<Listenable> fields;
  final TextFormDraft Function() capture;
  final void Function(TextFormDraft) restore;
  final BuildContext Function() context;
  final bool Function() mounted;
  bool _restoring = false;
  bool _completed = false;
  bool _submissionUnconfirmed = false;
  int _edits = 0;
  Future<void>? _clearWork;
  Widget get feedback => Column(
    mainAxisSize: MainAxisSize.min,
    children: [
      DraftFeedback(cubit: cubit),
      BlocBuilder<DraftCubit<TextFormDraft>, DraftState<TextFormDraft>>(
        bloc: cubit,
        builder: (context, state) =>
            state.record?.value.submissionUnconfirmed == true
            ? AppText(LocaleKeys.professionalUnknownOutcome)
            : const SizedBox.shrink(),
      ),
    ],
  );
  bool get locallySaved => cubit.state.status == LocalSaveStatus.saved;
  void programmatic(void Function() update) {
    _restoring = true;
    try {
      update();
    } finally {
      _restoring = false;
    }
  }

  Future<void> start() async {
    for (final Listenable field in fields) {
      field.addListener(changed);
    }
    final int before = _edits;
    await cubit.load();
    final TextFormDraft? draft = cubit.state.record?.value;
    if (!mounted() || !cubit.active || draft == null || _edits != before) {
      return;
    }
    await WidgetsBinding.instance.endOfFrame;
    if (!mounted() || !cubit.active || _edits != before) return;
    final bool? keep = await askToRestoreDraft(context());
    if (!mounted() || !cubit.active) return;
    if (keep == true) {
      _submissionUnconfirmed = draft.submissionUnconfirmed;
      _restoring = true;
      restore(draft);
      _restoring = false;
    } else {
      _submissionUnconfirmed = false;
      await cubit.clear();
    }
  }

  void changed() {
    if (_restoring || _completed || !mounted()) return;
    _edits++;
    cubit.schedule(
      TextFormDraft(
        capture().fields,
        submissionUnconfirmed: _submissionUnconfirmed,
      ),
    );
  }

  Future<bool> beginSubmission() async {
    if (_submissionUnconfirmed) {
      Messages.showToast(msg: LocaleKeys.professionalUnknownOutcome);
      return false;
    }
    _submissionUnconfirmed = true;
    changed();
    await cubit.flush();
    if (cubit.state.status != LocalSaveStatus.saved) {
      _submissionUnconfirmed = false;
      return false;
    }
    return true;
  }

  Future<void> finishSubmission({
    required bool confirmed,
    bool unknown = false,
    bool keepListening = false,
  }) async {
    if (confirmed) {
      _submissionUnconfirmed = false;
      if (keepListening) {
        await cubit.clear();
      } else {
        await clear();
      }
    } else if (!unknown) {
      _submissionUnconfirmed = false;
      changed();
      await cubit.flush();
    }
  }

  Future<void> clear() {
    _completed = true;
    return _clearWork ??= cubit.clear();
  }

  Future<void> close() async {
    for (final Listenable field in fields) {
      field.removeListener(changed);
    }
    await _clearWork;
    await cubit.close();
  }
}
