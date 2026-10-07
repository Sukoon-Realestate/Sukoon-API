import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import '../../data/models/property_search_model.dart';
import '../widgets/property_map/property_map_results.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_listing_category.dart';

class PropertyMapScreen extends StatefulWidget {
  const PropertyMapScreen({super.key, required this.filters});
  final PropertySearchFilters filters;

  @override
  State<PropertyMapScreen> createState() => _PropertyMapScreenState();
}

class _PropertyMapScreenState extends State<PropertyMapScreen> {
  late final ValueNotifier<PropertySearchFilters> _filters = ValueNotifier(
    widget.filters,
  );

  @override
  void dispose() {
    _filters.dispose();
    super.dispose();
  }

  void _selectCategory(RentalListingCategory category) {
    _filters.value = _filters.value.copyWith(
      rentalScope: category.scope?.value ?? '',
      page: 1,
    );
  }

  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.freeMapResults,
    showBackButton: true,
    body: SafeArea(
      child: ValueListenableBuilder<PropertySearchFilters>(
        valueListenable: _filters,
        builder: (context, filters, _) {
          // Changing the query replaces its pagination/cache/map owner and
          // prevents a response from the previous scope entering this list.
          final String queryResetKey = filters.cacheKey;
          return PropertyMapResults(
            key: ValueKey(queryResetKey),
            filters: filters,
            onCategorySelected: _selectCategory,
          );
        },
      ),
    ),
  );
}
