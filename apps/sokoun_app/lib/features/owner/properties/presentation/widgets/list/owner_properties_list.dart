part of '../../../imports.dart';

class OwnerPropertiesList extends StatelessWidget {
  const OwnerPropertiesList({
    super.key,
    required this.initialProperties,
    required this.pagifyController,
    required this.onAddPressed,
    required this.onEditPressed,
    required this.onRejectedPressed,
    required this.errorViewBuilder,
  });

  final List<OwnerPropertyContent>? initialProperties;
  final PagifyController<OwnerPropertyContent> pagifyController;
  final VoidCallback onAddPressed;
  final ValueChanged<OwnerPropertyContent> onEditPressed;
  final ValueChanged<OwnerPropertyContent> onRejectedPressed;
  final AppRequestErrorViewBuilder errorViewBuilder;

  Future<(List<OwnerPropertyContent>, PaginationData)> _loadPage(int page) {
    final List<OwnerPropertyContent>? fixtures = initialProperties;
    if (fixtures != null) {
      return Future.value((
        page == 1 ? fixtures : const <OwnerPropertyContent>[],
        PaginationData(perPage: fixtures.length, totalPages: 1),
      ));
    }

    return OwnerPropertiesData.getOwnedPropertiesPage(page: page);
  }

  @override
  Widget build(BuildContext context) {
    final bool usesApi = initialProperties == null;
    return AppPagify<OwnerPropertyContent>(
      pagifyController: pagifyController,
      asyncCall: (_, page) => _loadPage(page),
      shrinkWrap: false,
      cacheKey: usesApi ? OwnerPropertiesData.cacheKey : null,
      cacheToJson: usesApi ? (property) => property.toJson() : null,
      cacheFromJson: usesApi ? OwnerPropertyContent.fromJson : null,
      emptyListView: OwnerPropertiesEmptyState(onAddPressed: onAddPressed),
      errorBuilder: (error) => errorViewBuilder(
        error: error,
        onRetry: () async => pagifyController.refresh(),
      ),
      itemBuilder: (context, data, index, property) => OwnerPropertyCard(
        key: ValueKey(property.id),
        property: property,
        onEditPressed: () => onEditPressed(property),
        onRejectedPressed: () => onRejectedPressed(property),
      ).paddingBottom(12.h),
    ).padding(EdgeInsets.fromLTRB(20.w, 8.h, 20.w, 20.h));
  }
}
