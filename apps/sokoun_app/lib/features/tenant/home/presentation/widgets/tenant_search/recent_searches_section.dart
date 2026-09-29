import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';

import '../../../data/models/tenant_search_content.dart';
import '../../cubits/tenant_recent_searches_cubit.dart';
import 'recent_search_row.dart';
import 'search_section_title.dart';

class RecentSearchesSection extends StatelessWidget {
  const RecentSearchesSection({
    super.key,
    required this.searches,
    required this.onSelected,
  });

  final List<RecentSearchContent> searches;
  final ValueChanged<RecentSearchContent> onSelected;

  Future<void> _remove(
    BuildContext context, [
    RecentSearchContent? search,
  ]) async {
    final cubit = context.read<TenantRecentSearchesCubit>();
    final snapshot = List<RecentSearchContent>.of(cubit.state);
    final saved = search == null
        ? await cubit.clearRecentSearches()
        : await cubit.removeRecentSearch(search);
    if (!context.mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: AppText(
            saved
                ? LocaleKeys.searchHistoryRemoved
                : LocaleKeys.searchHistorySaveFailed,
          ),
          action: saved
              ? SnackBarAction(
                  label: LocaleKeys.undoAction,
                  onPressed: () async {
                    if (cubit.isClosed) return;
                    final restored = await cubit.restoreRecentSearches(
                      snapshot,
                    );
                    if (!restored && context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: AppText(LocaleKeys.searchHistorySaveFailed),
                        ),
                      );
                    }
                  },
                )
              : null,
        ),
      );
  }

  @override
  Widget build(BuildContext context) => AnimatedSize(
    duration: SokounMotion.duration(context, milliseconds: 260),
    curve: SokounMotion.curve,
    alignment: AlignmentDirectional.topStart,
    child: searches.isEmpty
        ? const SizedBox(width: double.infinity)
        : Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 18),
              Wrap(
                alignment: WrapAlignment.spaceBetween,
                crossAxisAlignment: WrapCrossAlignment.center,
                spacing: 12,
                children: [
                  SearchSectionTitle(LocaleKeys.tenantSearchRecentSearches),
                  TextButton(
                    onPressed: () => _remove(context),
                    child: Text(LocaleKeys.clearSearchHistory),
                  ),
                ],
              ),
              for (final search in searches)
                RecentSearchRow(
                  search: search,
                  onTap: () => onSelected(search),
                  onRemove: () => _remove(context, search),
                ),
            ],
          ),
  );
}
