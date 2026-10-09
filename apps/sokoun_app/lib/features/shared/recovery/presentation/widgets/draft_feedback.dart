import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../cubits/draft_cubit.dart';

class DraftFeedback<T> extends StatelessWidget {
  const DraftFeedback({super.key, required this.cubit});
  final DraftCubit<T> cubit;
  @override
  Widget build(BuildContext context) =>
      BlocBuilder<DraftCubit<T>, DraftState<T>>(
        bloc: cubit,
        builder: (context, state) => state.status == LocalSaveStatus.initial
            ? const SizedBox.shrink()
            : Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Semantics(
                      liveRegion: true,
                      child: AppText(switch (state.status) {
                        LocalSaveStatus.saving => LocaleKeys.professionalSaving,
                        LocalSaveStatus.saved => LocaleKeys.freeDraftSaved,
                        _ => LocaleKeys.freeLocalSaveFailed,
                      }),
                    ),
                    if (state.status == LocalSaveStatus.failed)
                      TextButton(
                        onPressed: cubit.retry,
                        child: AppText(LocaleKeys.ownerRetryAction),
                      ),
                  ],
                ),
              ),
      );
}

Future<bool?> askToRestoreDraft(BuildContext context) => showDialog<bool>(
  context: context,
  barrierDismissible: false,
  builder: (_) => AlertDialog(
    title: AppText(LocaleKeys.freeResumeDraft),
    content: AppText(LocaleKeys.freeDraftRecovery),
    actions: [
      TextButton(
        onPressed: () => Go.back(false),
        child: AppText(LocaleKeys.freeDiscardLocalDraft),
      ),
      TextButton(
        onPressed: () => Go.back(true),
        child: AppText(LocaleKeys.freeResumeDraft),
      ),
    ],
  ),
);
