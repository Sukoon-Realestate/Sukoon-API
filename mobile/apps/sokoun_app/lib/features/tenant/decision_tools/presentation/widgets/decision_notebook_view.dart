import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_results_screen.dart';
import '../../data/models/decision_notebook.dart';
import '../cubits/decision_tools_cubit.dart';
import '../screens/property_comparison_screen.dart';
import 'decision_editor.dart';
import 'decision_tools_empty.dart';

class DecisionNotebookView extends StatelessWidget {
  const DecisionNotebookView({
    super.key,
    required this.notebook,
    required this.cubit,
    required this.onReturned,
  });
  final DecisionNotebook notebook;
  final DecisionToolsCubit cubit;
  final Future<void> Function() onReturned;
  Future<void> _mutate(Future<void> Function() action) async {
    try {
      await action();
    } catch (_) {
      Messages.showToast(msg: LocaleKeys.freeLocalSaveFailed);
    }
  }

  @override
  Widget build(BuildContext context) {
    final lists =
        notebook.properties.map((property) => property.list).toSet().toList()
          ..sort();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(LocaleKeys.freePrivateDeviceNotes),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          onPressed: notebook.comparisonIds.length < 2
              ? null
              : () async {
                  await Go.to(
                    PropertyComparisonScreen(
                      propertyIds: notebook.comparisonIds,
                    ),
                  );
                  await onReturned();
                },
          icon: const Icon(Icons.compare_arrows),
          label: AppText(
            '${LocaleKeys.freeCompare} (${notebook.comparisonIds.length}/3)',
          ),
        ),
        if (notebook.properties.isEmpty)
          DecisionToolsEmpty(
            title: LocaleKeys.freeDecisionTools,
            description: LocaleKeys.freeDecisionEmpty,
          ),
        for (final list in lists) ...[
          const SizedBox(height: 20),
          AppText(
            list.isEmpty ? LocaleKeys.freeUnfiled : list,
            fontWeight: FontWeight.bold,
          ),
          for (final property in notebook.properties.where(
            (property) => property.list == list,
          ))
            Card(
              key: ValueKey(property.propertyId),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    AppText(property.title, fontWeight: FontWeight.bold),
                    if (property.note.isNotEmpty)
                      AppText(
                        property.note,
                        maxLines: 3,
                        overflow: TextOverflow.ellipsis,
                      ),
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      children: [
                        TextButton(
                          onPressed: () => Go.to(
                            PropertyDetailsScreen(
                              propertyId: property.propertyId,
                            ),
                          ),
                          child: AppText(LocaleKeys.freeOpenListing),
                        ),
                        TextButton(
                          onPressed: () => showModalBottomSheet<bool>(
                            context: context,
                            useSafeArea: true,
                            isScrollControlled: true,
                            showDragHandle: true,
                            builder: (_) => DecisionEditor(
                              cubit: cubit,
                              decision: property,
                            ),
                          ),
                          child: AppText(LocaleKeys.freePrivateNotes),
                        ),
                        FilterChip(
                          label: AppText(LocaleKeys.freeCompare),
                          selected: notebook.comparisonIds.contains(
                            property.propertyId,
                          ),
                          onSelected: (_) => _mutate(() async {
                            if (!await cubit.toggleComparison(property)) {
                              Messages.showToast(
                                msg: LocaleKeys.freeCompareLimit,
                              );
                            }
                          }),
                        ),
                        IconButton(
                          tooltip: LocaleKeys.freeRemove,
                          onPressed: () => _mutate(
                            () => cubit.removeDecision(property.propertyId),
                          ),
                          icon: const Icon(Icons.delete_outline),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
        ],
        const SizedBox(height: 24),
        AppText(LocaleKeys.freeSavedSearches, fontWeight: FontWeight.bold),
        const SizedBox(height: 8),
        AppText(LocaleKeys.freeSavedSearchManual),
        for (final search in notebook.searches)
          Card(
            key: ValueKey(search.id),
            child: ListTile(
              title: AppText(search.name),
              subtitle: AppText(search.filters.combinedSearch),
              onTap: () => Go.to(
                TenantSearchResultsScreen(initialFilters: search.filters),
              ),
              trailing: IconButton(
                tooltip: LocaleKeys.freeRemove,
                onPressed: () => _mutate(() => cubit.removeSearch(search.id)),
                icon: const Icon(Icons.delete_outline),
              ),
            ),
          ),
        const SizedBox(height: 24),
      ],
    );
  }
}
