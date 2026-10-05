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
  });

  final List<OwnerPropertyContent>? initialProperties;
  final PagifyController<OwnerPropertyContent> pagifyController;
  final OwnerPropertyFilter filter;
  final VoidCallback onAddPressed;
  final ValueChanged<OwnerPropertyContent> onEditPressed;
  final ValueChanged<OwnerPropertyContent> onRejectedPressed;
  final ValueChanged<OwnerPropertyContent> onDeletePressed;

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
      ),
      itemBuilder: (context, data, index, property) => OwnerPropertyCard(
        key: ValueKey(property.id),
        property: property,
        onEditPressed: () => onEditPressed(property),
        onRejectedPressed: () => onRejectedPressed(property),
        onDeletePressed: () => onDeletePressed(property),
      ),
    ).padding(EdgeInsets.fromLTRB(20.w, 8.h, 20.w, 20.h));
  }
}
