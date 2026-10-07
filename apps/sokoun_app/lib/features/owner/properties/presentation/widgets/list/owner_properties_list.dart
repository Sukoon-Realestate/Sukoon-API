part of '../../../imports.dart';

class OwnerPropertiesList extends StatelessWidget {
  const OwnerPropertiesList({
    super.key,
    required this.initialProperties,
    required this.pagifyController,
    required this.filter,
    required this.onAddPressed,
    required this.onEditPressed,
    required this.onRejectedPressed,
    required this.onDeletePressed,
    this.onInventoryChanged,
    this.onEditOfferPressed,
    this.category = RentalListingCategory.all,
    required this.onCategorySelected,
  });

  final void Function(OwnerPropertyContent, String)? onEditOfferPressed;
  final List<OwnerPropertyContent>? initialProperties;
  final PagifyController<OwnerPropertyContent> pagifyController;
  final OwnerPropertyFilter filter;
  final RentalListingCategory category;
  final ValueChanged<RentalListingCategory> onCategorySelected;
  final VoidCallback onAddPressed;
  final ValueChanged<OwnerPropertyContent> onEditPressed;
  final ValueChanged<OwnerPropertyContent> onRejectedPressed;
  final ValueChanged<OwnerPropertyContent> onDeletePressed;
  final void Function(OwnerPropertyContent, PropertyDetailsModel)?
  onInventoryChanged;

  Future<(List<OwnerPropertyContent>, PaginationData)> _loadPage(int page) {
    final List<OwnerPropertyContent>? fixtures = initialProperties;
    if (fixtures != null) {
      final List<OwnerPropertyContent> properties = fixtures
          .where((property) => filter.accepts(property.status))
          .toList(growable: false);
      return Future.value((
        page == 1 ? properties : const <OwnerPropertyContent>[],
        PaginationData(perPage: OwnerPropertiesData.pageSize, totalPages: 1),
      ));
    }

    return OwnerPropertiesData.getOwnedPropertiesPage(
      page: page,
      filter: filter,
    );
  }

  @override
  Widget build(BuildContext context) {
    final bool usesApi = initialProperties == null;
    return AppPagify<OwnerPropertyContent>(
      header: RentalListingCategories(
        selected: category,
        onSelected: onCategorySelected,
        loadedPropertiesOnly: usesApi && category != RentalListingCategory.all,
      ).paddingBottom(16),
      enablePullRefresh: true,
      pagifyController: pagifyController,
      rankingType: Ranking.adaptiveGrid,
      asyncCall: (_, page) => _loadPage(page),
      shrinkWrap: false,
      cacheKey: usesApi ? OwnerPropertiesData.cacheKeyFor(filter) : null,
      cacheToJson: usesApi ? (property) => property.toJson() : null,
      cacheFromJson: usesApi ? OwnerPropertyContent.fromJson : null,
      emptyListView: OwnerPropertiesEmptyState(
        filter: filter,
        onAddPressed: onAddPressed,
        category: category,
        onShowAllPressed: () => onCategorySelected(RentalListingCategory.all),
      ),
      filterItems: (items) => RentalCollectionFilter.properties(
        items,
        identity: (property) => property.id,
        matches: (property) => RentalCollectionFilter.matchesProperty(
          category: category,
          inventory: property.rentalInventory,
          summary: property.rentalSummary,
        ),
      ),
      filteredFooterBuilder: (context, hasMore, isLoading, error, loadMore) =>
          RentalCollectionFooter(
            hasMorePages: hasMore,
            isLoading: isLoading,
            errorMessage: error,
            onLoadMore: loadMore,
          ),
      itemBuilder: (context, data, index, property) => OwnerPropertyCard(
        key: ValueKey(property.id),
        property: property,
        category: category,
        onEditPressed: () => onEditPressed(property),
        onEditOfferPressed: onEditOfferPressed == null
            ? null
            : (id) => onEditOfferPressed!(property, id),
        onRejectedPressed: () => onRejectedPressed(property),
        onDeletePressed: () => onDeletePressed(property),
        onInventoryChanged: onInventoryChanged == null
            ? null
            : (updated) => onInventoryChanged!(property, updated),
      ),
    ).padding(EdgeInsets.fromLTRB(20.w, 8.h, 20.w, 20.h));
  }
}
