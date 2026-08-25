part of '../../imports.dart';

class OwnerPropertiesScreen extends StatefulWidget {
  const OwnerPropertiesScreen({super.key, this.initialProperties});

  final List<OwnerPropertyContent>? initialProperties;

  @override
  State<OwnerPropertiesScreen> createState() => _OwnerPropertiesScreenState();
}

class _OwnerPropertiesScreenState extends State<OwnerPropertiesScreen> {
  static const int _pageSize = 10;

  late final PagifyController<OwnerPropertyContent> _pagifyController;

  @override
  void initState() {
    super.initState();
    _pagifyController = PagifyController<OwnerPropertyContent>();
  }

  Future<(List<OwnerPropertyContent>, PaginationData)> _getPropertiesPage(
    BuildContext context,
    int page,
  ) async {
    final List<OwnerPropertyContent>? initialProperties =
        widget.initialProperties;
    if (initialProperties != null) {
      return (
        page == 1 ? initialProperties : const <OwnerPropertyContent>[],
        PaginationData(perPage: initialProperties.length, totalPages: 1),
      );
    }

    final OwnerPropertiesResponse response =
        await OwnerPropertiesData.getOwnedProperties(
          page: page,
          pageSize: _pageSize,
        );
    final int totalPages = response.count == 0
        ? 1
        : (response.count + _pageSize - 1) ~/ _pageSize;
    return (
      response.results,
      PaginationData(perPage: _pageSize, totalPages: totalPages),
    );
  }

  Future<void> _openAddProperty() async {
    final bool? shouldReturnToProperties = await Go.to<bool>(
      OwnerAddPropertyFlowScreen(onViewProperties: () => Go.back(true)),
    );
    if (shouldReturnToProperties == true && mounted) {
      _showMessage(LocaleKeys.ownerPropertiesSubmittedMessage);
      if (widget.initialProperties == null) {
        await _pagifyController.refresh();
      }
    }
  }

  Future<void> _openEdit(OwnerPropertyContent property) async {
    final OwnerPropertyEditResult? result =
        await Go.to<OwnerPropertyEditResult>(
          OwnerEditPropertyScreen(property: property),
        );
    if (result == null || !mounted) {
      return;
    }
    if (result.isDeleted) {
      _deleteProperty(property);
      return;
    }
    _replaceProperty(result.property);
    _showMessage(LocaleKeys.ownerPropertiesSaved);
  }

  Future<void> _openAnalytics(OwnerPropertyContent property) {
    return Go.to(OwnerPropertyAnalyticsScreen(property: property));
  }

  Future<void> _openRejection(OwnerPropertyContent property) async {
    final OwnerPropertyContent? updated = await Go.to<OwnerPropertyContent>(
      OwnerPropertyRejectionScreen(property: property),
    );
    if (updated != null && mounted) {
      _replaceProperty(updated);
      _showMessage(LocaleKeys.ownerPropertiesResubmitted);
    }
  }

  Future<void> _openActions(OwnerPropertyContent property) async {
    final OwnerPropertyAction? action =
        await showModalBottomSheet<OwnerPropertyAction>(
          context: context,
          useSafeArea: true,
          isScrollControlled: true,
          backgroundColor: AppColors.transparent,
          barrierColor: AppColors.blackAlpha45,
          builder: (context) => OwnerPropertyActionSheet(property: property),
        );
    if (action == null || !mounted) {
      return;
    }
    if (action.isEdit) {
      await _openEdit(property);
      return;
    }
    if (action.isPause) {
      final OwnerPropertyStatus nextStatus = property.status.isHidden
          ? OwnerPropertyStatus.verified
          : OwnerPropertyStatus.hidden;
      _replaceProperty(property.copyWith(status: nextStatus));
      _showMessage(
        nextStatus.isHidden
            ? LocaleKeys.ownerPropertiesPausedMessage
            : LocaleKeys.ownerPropertiesReactivatedMessage,
      );
      return;
    }
    if (action.isMarkRented) {
      _replaceProperty(property.copyWith(status: OwnerPropertyStatus.rented));
      _showMessage(LocaleKeys.ownerPropertiesMarkedRentedMessage);
      return;
    }
    _deleteProperty(property);
  }

  void _replaceProperty(OwnerPropertyContent property) {
    final int index = _pagifyController.items.indexWhere(
      (item) => item.id == property.id,
    );
    if (index < 0) {
      return;
    }
    _pagifyController.replaceWith(index, property);
  }

  void _deleteProperty(OwnerPropertyContent property) {
    _pagifyController.removeWhere((item) => item.id == property.id);
    _showMessage(LocaleKeys.ownerPropertiesDeletedMessage);
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: AppText(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            children: [
              Padding(
                padding: EdgeInsets.fromLTRB(20.w, 12.h, 20.w, 8.h),
                child: OwnerPropertiesHeader(onAddPressed: _openAddProperty),
              ),
              Expanded(
                child: Padding(
                  padding: EdgeInsets.fromLTRB(20.w, 8.h, 20.w, 20.h),
                  child: AppPagify<OwnerPropertyContent>(
                    pagifyController: _pagifyController,
                    asyncCall: _getPropertiesPage,
                    shrinkWrap: false,
                    itemBuilder: (context, data, index, property) => Padding(
                      padding: EdgeInsets.only(bottom: 12.h),
                      child: OwnerPropertyCard(
                        property: property,
                        onEditPressed: () => _openEdit(property),
                        onAnalyticsPressed: () => _openAnalytics(property),
                        onActionsPressed: () => _openActions(property),
                        onPressed: property.status.isRejected
                            ? () => _openRejection(property)
                            : () => _openActions(property),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
