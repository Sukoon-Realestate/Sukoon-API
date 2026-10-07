import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import '../../../data/models/property_filter_options_model.dart';
import '../../../data/models/property_search_model.dart';
import '../tenant_search_results/search_result_card.dart';
import 'rental_home_empty_state.dart';

/// A bounded preview. View all delegates pagination to the existing AppPagify.
class RentalHomeSectionPreview extends StatelessWidget {
  const RentalHomeSectionPreview({
    super.key,
    required this.data,
    required this.filters,
  });

  final PropertySearchResponseModel data;
  final PropertySearchFilters filters;

  @override
  Widget build(BuildContext context) => data.results.isEmpty
      ? const RentalHomeEmptyState()
      : Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppText(
              LocaleKeys.rentalHomePreview
                  .replaceAll('{shown}', '${data.results.length}')
                  .replaceAll('{count}', '${data.count}'),
            ),
            10.szH,
            SokounAdaptiveGrid(
              maximumColumns: 2,
              children: [
                for (final item in data.results)
                  SearchResultCard(
                    key: ValueKey(item.id),
                    item: item,
                    filterOptions: const PropertyFilterOptionsModel.initial(),
                    preferences: filters,
                  ),
              ],
            ),
          ],
        );
}
