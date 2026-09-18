part of '../../imports.dart';

class OwnerPropertiesScreen extends StatefulWidget {
  const OwnerPropertiesScreen({super.key, this.initialProperties});

  final List<OwnerPropertyContent>? initialProperties;

  @override
  State<OwnerPropertiesScreen> createState() => _OwnerPropertiesScreenState();
}

class _OwnerPropertiesScreenState extends State<OwnerPropertiesScreen> {
  late final PagifyController<OwnerPropertyContent> _pagifyController;
  bool _isLoadingPropertyDetails = false;

  @override
  void initState() {
    super.initState();
    _pagifyController = PagifyController<OwnerPropertyContent>();
  }

  Future<void> _openAddProperty() async {
    final bool? shouldReturnToProperties = await Go.to<bool>(
      const OwnerAddPropertyFlowScreen(),
    );
    if (shouldReturnToProperties == true && mounted) {
      _showMessage(LocaleKeys.ownerPropertiesSubmittedMessage);
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
      OwnerEditPropertyScreen(property: details),
    );
    if (updated == null || !mounted) {
      return;
    }
    _replaceProperty(_mergePropertyDetails(property, updated));
    _showMessage(LocaleKeys.ownerPropertiesSaved);
  }

  Future<PropertyDetailsModel?> _loadPropertyDetails(String propertyId) async {
    if (_isLoadingPropertyDetails) {
      return null;
    }
    setState(() => _isLoadingPropertyDetails = true);
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
        setState(() => _isLoadingPropertyDetails = false);
      }
    }
    return details;
  }

  OwnerPropertyContent _mergePropertyDetails(
    OwnerPropertyContent property,
    PropertyDetailsModel details,
  ) {
    final String location = [
      details.district,
      details.city.name,
      details.city.governorateName,
    ].where((part) => part.trim().isNotEmpty).join('، ');
    return property.copyWith(
      title: details.title,
      mainImage: details.mainImage,
      location: location.isEmpty ? property.location : location,
      monthlyPrice: (double.tryParse(details.price) ?? 0).round(),
      bedrooms: details.bedrooms,
      area: details.area,
      description: details.description,
      photoCount: details.imageUrls.length,
      status: property.status.isRejected
          ? OwnerPropertyStatus.pending
          : property.status,
    );
  }

  Future<void> _openRejection(OwnerPropertyContent property) async {
    final PropertyDetailsModel? updated = await Go.to<PropertyDetailsModel>(
      OwnerPropertyRejectionScreen(property: property),
    );
    if (updated != null && mounted) {
      _replaceProperty(_mergePropertyDetails(property, updated));
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
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: Stack(
          children: [
            Column(
              children: [
                OwnerPropertiesHeader().padding(EdgeInsets.fromLTRB(20.w, 12.h, 20.w, 8.h)),
                Expanded(
                  child: OwnerPropertiesList(
                    initialProperties: widget.initialProperties,
                    pagifyController: _pagifyController,
                    onAddPressed: _openAddProperty,
                    onEditPressed: _openEdit,
                    onActionsPressed: _openActions,
                    onRejectedPressed: _openRejection,
                  ),
                ),
              ],
            ),
            if (_isLoadingPropertyDetails)
              Positioned.fill(
                child: ColoredBox(
                  color: AppColors.whiteAlpha60,
                  child: const Center(
                    child: CircularProgressIndicator(
                      color: AppColors.sokoonTeal,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
