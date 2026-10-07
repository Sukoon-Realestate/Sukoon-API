import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:pagify/pagify.dart';
import '../../../data/models/property_details_model.dart';
import '../../../data/models/property_map_viewport.dart';
import '../../../data/models/property_search_model.dart';
import '../../../data/property_search_data.dart';
import '../../screens/property_details_screen.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/widgets/decision_tools_empty.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_listing_category.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_collection_filter.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_listing_categories.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_collection_footer.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';

class PropertyMapResults extends StatefulWidget {
  const PropertyMapResults({
    super.key,
    required this.filters,
    required this.onCategorySelected,
  });
  final PropertySearchFilters filters;
  final ValueChanged<RentalListingCategory> onCategorySelected;
  @override
  State<PropertyMapResults> createState() => _PropertyMapResultsState();
}

class _PropertyMapResultsState extends State<PropertyMapResults> {
  final PagifyController<PropertyDetailsModel> _pagination = PagifyController();
  bool _centeredOnResults = false;
  final ValueNotifier<List<PropertyDetailsModel>> _loaded = ValueNotifier(
    const [],
  );
  final ValueNotifier<PropertyMapViewport?> _viewport = ValueNotifier(null);
  final ValueNotifier<GoogleMapController?> _map = ValueNotifier(null);
  @override
  void dispose() {
    _loaded.dispose();
    _viewport.dispose();
    _map.dispose();
    super.dispose();
  }

  String _price(PropertyDetailsModel property) =>
      RentalOfferLabels.listingPrice(
        property.rentalSummary,
        hasInventory: property.hasRentalOffers,
        legacyPrice: property.price,
        legacyPeriod: property.pricePeriod,
        contextScope: widget.filters.rentalScope,
        contextPricePeriod: widget.filters.pricePeriod,
      );

  Future<void> _centerOnResults() async {
    final controller = _map.value;
    final first = _loaded.value
        .where(const PropertyMapViewport.initial().contains)
        .firstOrNull;
    if (_centeredOnResults || controller == null || first == null) return;
    _centeredOnResults = true;
    try {
      await controller.animateCamera(
        CameraUpdate.newLatLng(
          LatLng(double.parse(first.latitude), double.parse(first.longitude)),
        ),
      );
    } catch (_) {
      // The map can be disposed while the native camera update is in flight.
      _centeredOnResults = false;
    }
  }

  Future<void> _filterVisibleArea() async {
    final controller = _map.value;
    if (controller == null) return;
    try {
      final bounds = await controller.getVisibleRegion();
      if (!mounted) return;
      _viewport.value = PropertyMapViewport(
        south: bounds.southwest.latitude,
        north: bounds.northeast.latitude,
        west: bounds.southwest.longitude,
        east: bounds.northeast.longitude,
      );
    } catch (_) {
      Messages.showToast(msg: LocaleKeys.freeMapUnavailable);
    }
  }

  Widget _header() => ValueListenableBuilder<List<PropertyDetailsModel>>(
    valueListenable: _loaded,
    builder: (context, properties, _) {
      final located = properties
          .where(const PropertyMapViewport.initial().contains)
          .toList(growable: false);
      final first = located.firstOrNull;
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: RentalListingCategories(
              selected: RentalListingCategory.fromScope(
                widget.filters.rentalScope,
              ),
              onSelected: widget.onCategorySelected,
              includeUnspecified: false,
              scopeSearchUnavailable:
                  !RentalOfferCapabilities.configured.canSearch,
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: AppText(
              LocaleKeys.freeMapLoadedExplanation
                  .replaceAll('{count}', '${properties.length}')
                  .replaceAll('{located}', '${located.length}'),
            ),
          ),
          SizedBox(
            height: 260,
            child: GoogleMap(
              initialCameraPosition: CameraPosition(
                target: first == null
                    ? const LatLng(30.0444, 31.2357)
                    : LatLng(
                        double.parse(first.latitude),
                        double.parse(first.longitude),
                      ),
                zoom: 11,
              ),
              onMapCreated: (controller) {
                if (mounted) {
                  _map.value = controller;
                  _centerOnResults();
                }
              },
              mapToolbarEnabled: false,
              myLocationButtonEnabled: false,
              zoomControlsEnabled: true,
              markers: {
                for (final property in located)
                  Marker(
                    markerId: MarkerId(property.id),
                    position: LatLng(
                      double.parse(property.latitude),
                      double.parse(property.longitude),
                    ),
                    infoWindow: InfoWindow(
                      title: property.title,
                      snippet: _price(property),
                      onTap: () => Go.to(
                        PropertyDetailsScreen(
                          propertyId: property.id,
                          searchPreferences: widget.filters,
                        ),
                      ),
                    ),
                  ),
              },
            ),
          ),
          ValueListenableBuilder<GoogleMapController?>(
            valueListenable: _map,
            builder: (context, controller, _) => Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Wrap(
                spacing: 8,
                children: [
                  OutlinedButton.icon(
                    onPressed: controller == null ? null : _filterVisibleArea,
                    icon: const Icon(Icons.filter_alt_outlined),
                    label: AppText(LocaleKeys.freeFilterLoadedArea),
                  ),
                  TextButton(
                    onPressed: () => _viewport.value = null,
                    child: AppText(LocaleKeys.freeShowAllLoaded),
                  ),
                ],
              ),
            ),
          ),
          ValueListenableBuilder<PropertyMapViewport?>(
            valueListenable: _viewport,
            builder: (context, viewport, _) =>
                viewport != null && !properties.any(viewport.contains)
                ? Padding(
                    padding: const EdgeInsets.all(16),
                    child: AppText(LocaleKeys.freeMapNoLoadedMatches),
                  )
                : const SizedBox.shrink(),
          ),
        ],
      );
    },
  );

  @override
  Widget build(BuildContext context) => AppPagify<PropertyDetailsModel>(
    pagifyController: _pagination,
    header: _header(),
    enablePullRefresh: true,
    cacheKey: '${PropertySearchData.cacheKeyFor(widget.filters)}_map',
    cacheToJson: (property) => property.toJson(),
    cacheFromJson: PropertyDetailsModel.fromJson,
    asyncCall: (context, page) async {
      final (response, pagination) = await PropertySearchData.getPropertiesPage(
        widget.filters.copyWith(page: page),
      );
      return (response.results, pagination);
    },
    onSuccess: (context, properties) {
      if (mounted) {
        _loaded.value = RentalCollectionFilter.properties(
          properties,
          identity: (property) => property.id,
          matches: (_) => true,
        );
        _centerOnResults();
      }
    },
    emptyListView: DecisionToolsEmpty(
      title: LocaleKeys.freeMapResults,
      description: LocaleKeys.freeMapNoResults,
    ),
    filterItems: (items) => RentalCollectionFilter.properties(
      items,
      identity: (property) => property.id,
      matches: (_) => true,
    ),
    filteredFooterBuilder: (context, hasMore, isLoading, error, loadMore) =>
        RentalCollectionFooter(
          hasMorePages: hasMore,
          isLoading: isLoading,
          errorMessage: error,
          onLoadMore: loadMore,
        ).paddingAll(16),
    itemBuilder: (context, properties, index, property) =>
        ValueListenableBuilder<PropertyMapViewport?>(
          valueListenable: _viewport,
          builder: (context, viewport, _) =>
              viewport != null && !viewport.contains(property)
              ? const SizedBox.shrink()
              : Card(
                  key: ValueKey(property.id),
                  margin: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 6,
                  ),
                  child: ListTile(
                    title: AppText(property.title),
                    subtitle: AppText(
                      [
                        ...RentalOfferLabels.listingFacts(
                          property.rentalSummary,
                          contextScope: widget.filters.rentalScope,
                        ),
                        _price(property),
                        if (!const PropertyMapViewport.initial().contains(
                          property,
                        ))
                          LocaleKeys.freeMapMissingLocation,
                      ].join('\n'),
                    ),
                    onTap: () => Go.to(
                      PropertyDetailsScreen(
                        propertyId: property.id,
                        searchPreferences: widget.filters,
                      ),
                    ),
                  ),
                ),
        ),
  );
}
