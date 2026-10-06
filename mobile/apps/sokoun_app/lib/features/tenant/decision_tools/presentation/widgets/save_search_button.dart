import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import '../cubits/decision_tools_cubit.dart';

class SaveSearchButton extends StatelessWidget {
  const SaveSearchButton({super.key, required this.filters});
  final PropertySearchFilters filters;
  Future<void> _save(BuildContext context) async {
    final name = TextEditingController(text: filters.combinedSearch);
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
        builder: (context) => Padding(
          padding: EdgeInsets.fromLTRB(
            20,
            12,
            20,
            MediaQuery.viewInsetsOf(context).bottom + 24,
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                AppText(LocaleKeys.freeSaveSearch, fontWeight: FontWeight.bold),
                const SizedBox(height: 8),
                AppText(LocaleKeys.freeSavedSearchManual),
                const SizedBox(height: 12),
                TextField(
                  controller: name,
                  maxLength: 80,
                  decoration: InputDecoration(
                    labelText: LocaleKeys.freeSearchName,
                  ),
                ),
                const SizedBox(height: 12),
                AppLoadingButton(
                  title: LocaleKeys.freeSaveSearch,
                  asyncCall: (_) async {
                    if (name.text.trim().isEmpty) {
                      Messages.showToast(msg: LocaleKeys.fillField);
                      return;
                    }
                    try {
                      await cubit.saveSearch(name.text, filters);
                      if (context.mounted) Go.back(true);
                    } catch (_) {
                      Messages.showToast(msg: LocaleKeys.freeLocalSaveFailed);
                    }
                  },
                ),
              ],
            ),
          ),
        ),
      );
    } catch (_) {
      Messages.showToast(msg: LocaleKeys.freeLocalSaveFailed);
    } finally {
      name.dispose();
      await cubit.close();
    }
  }

  @override
  Widget build(BuildContext context) => IconButton(
    tooltip: LocaleKeys.freeSaveSearch,
    icon: const Icon(Icons.bookmark_add_outlined),
    onPressed: () => _save(context),
  );
}
