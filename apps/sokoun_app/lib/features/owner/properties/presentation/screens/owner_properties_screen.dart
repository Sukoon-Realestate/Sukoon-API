part of '../../imports.dart';

class OwnerPropertiesScreen extends StatefulWidget {
  const OwnerPropertiesScreen({super.key, this.initialProperties});

  final List<OwnerPropertyContent>? initialProperties;

  @override
  State<OwnerPropertiesScreen> createState() => _OwnerPropertiesScreenState();
}

class _OwnerPropertiesScreenState extends State<OwnerPropertiesScreen> {
  late PagifyController<OwnerPropertyContent> _pagifyController;
  late final List<OwnerPropertyContent>? _fixtureProperties;
  final ValueNotifier<OwnerPropertyFilter> _selectedFilter = ValueNotifier(
    OwnerPropertyFilter.underReview,
  );
  final ValueNotifier<bool> _isLoadingPropertyDetails = ValueNotifier<bool>(
    false,
  );

  @override
  void initState() {
    super.initState();
    _pagifyController = PagifyController<OwnerPropertyContent>();
    final List<OwnerPropertyContent>? properties = widget.initialProperties;
    _fixtureProperties = properties == null ? null : List.of(properties);
  }

  @override
  void dispose() {
    _isLoadingPropertyDetails.dispose();
    _selectedFilter.dispose();
    super.dispose();
  }

  void _selectFilter(OwnerPropertyFilter filter) {
    if (_selectedFilter.value == filter) return;
    // A fresh keyed list starts at page one and isolates previous tab responses.
    // AppPagify owns disposal of each controller when its list is replaced.
    _pagifyController = PagifyController<OwnerPropertyContent>();
    _selectedFilter.value = filter;
  }

  Future<void> _openAddProperty() async {
    final bool? shouldReturnToProperties = await Go.to<bool>(
      const OwnerPropertyFlowScreen(),
    );
    if (shouldReturnToProperties == true && mounted) {
      if (widget.initialProperties == null) {
        await _pagifyController.refresh();
      }
    }
  }

  Future<void> _openEdit(OwnerPropertyContent property) async {
    final PropertyDetailsModel? details = await _loadPropertyDetails(
      property.id,
    );
    if (details == null || !mounted) {
      return;
    }
    final PropertyDetailsModel? updated = await Go.to<PropertyDetailsModel>(
      OwnerPropertyFlowScreen(property: details),
    );
    if (updated == null || !mounted) {
      return;
    }
    _replaceProperty(_mergePropertyDetails(property, updated));
  }

  Future<PropertyDetailsModel?> _loadPropertyDetails(String propertyId) async {
    if (_isLoadingPropertyDetails.value) {
      return null;
    }
    _isLoadingPropertyDetails.value = true;
    final PropertyDetailsCubit cubit = PropertyDetailsCubit();
    PropertyDetailsModel? details;
    try {
      await cubit.getPropertyDetails(propertyId);
      if (cubit.state.isSuccess || cubit.state.data.id.isNotEmpty) {
        details = cubit.state.data;
      }
    } finally {
      await cubit.close();
      if (mounted) {
        _isLoadingPropertyDetails.value = false;
      }
    }
    return details;
  }

  OwnerPropertyContent _mergePropertyDetails(
    OwnerPropertyContent property,
    PropertyDetailsModel details,
  ) {
    final String location = [
      details.street,
      details.district,
      details.city.name,
      details.governorateName,
    ].where((part) => part.trim().isNotEmpty).join('، ');
    return property.copyWith(
      title: details.title,
      mainImage: details.mainImage,
      location: location.isEmpty ? property.location : location,
      monthlyPrice: EgyptianPound.parseAmount(details.price) ?? 0,
      pricePeriod: details.pricePeriod,
      bedrooms: details.bedrooms,
      area: details.area,
      description: details.description,
      photoCount: details.imageUrls.length,
      status: OwnerPropertyStatusX.fromName(details.status),
    );
  }

  Future<void> _openRejection(OwnerPropertyContent property) async {
    final PropertyDetailsModel? updated = await Go.to<PropertyDetailsModel>(
      OwnerPropertyRejectionScreen(property: property),
    );
    if (updated != null && mounted) {
      _replaceProperty(_mergePropertyDetails(property, updated));
    }
  }

  void _replaceProperty(OwnerPropertyContent property) {
    final List<OwnerPropertyContent>? fixtures = _fixtureProperties;
    final int fixtureIndex =
        fixtures?.indexWhere((item) => item.id == property.id) ?? -1;
    if (fixtureIndex >= 0) fixtures![fixtureIndex] = property;
    final int index = _pagifyController.items.indexWhere(
      (item) => item.id == property.id,
    );
    if (index < 0) {
      return;
    }
    if (_selectedFilter.value.accepts(property.status)) {
      _pagifyController.replaceWith(index, property);
    } else {
      _pagifyController.removeWhere((item) => item.id == property.id);
    }
  }

  Future<void> _deleteProperty(OwnerPropertyContent property) async {
    final bool? deleted = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      isDismissible: false,
      enableDrag: false,
      builder: (_) => OwnerPropertyDeleteSheet(property: property),
    );
    if (!mounted || deleted != true) return;
    _fixtureProperties?.removeWhere((item) => item.id == property.id);
    _pagifyController.removeWhere((item) => item.id == property.id);
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: OwnerPropertyFilter.values.length,
      animationDuration: SokounMotion.duration(context, milliseconds: 240),
      child: AppScaffold(
        title: LocaleKeys.ownerPropertiesTitle,
        showBackButton: true,
        actions: [
          IconButton(
            tooltip: LocaleKeys.ownerPropertiesAdd,
            onPressed: _openAddProperty,
            icon: const Icon(Icons.add_rounded),
          ),
        ],
        backgroundColor: AppColors.scaffoldBackground,
        contentWidth: SokounContentWidth.wide,
        body: SafeArea(
          child: ValueListenableBuilder<bool>(
            valueListenable: _isLoadingPropertyDetails,
            child: ValueListenableBuilder<OwnerPropertyFilter>(
              valueListenable: _selectedFilter,
              builder: (context, filter, _) {
                final String statusId = filter.apiValue;
                return Column(
                  children: [
                    OwnerPropertiesStatusTabs(
                      selectedFilter: filter,
                      onFilterSelected: _selectFilter,
                    ),
                    Expanded(
                      child: OwnerPropertiesList(
                        key: ValueKey(statusId),
                        filter: filter,
                        initialProperties: _fixtureProperties,
                        pagifyController: _pagifyController,
                        onAddPressed: _openAddProperty,
                        onEditPressed: _openEdit,
                        onRejectedPressed: _openRejection,
                        onDeletePressed: _deleteProperty,
                      ),
                    ),
                  ],
                );
              },
            ),
            builder: (context, isLoading, child) => Stack(
              children: [
                child!,
                if (isLoading)
                  Positioned.fill(
                    child: ColoredBox(
                      color: AppColors.whiteAlpha60,
                      child: CustomLoading.showLoadingView(
                        color: AppColors.sokoonTeal,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
