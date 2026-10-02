part of '../../imports.dart';

class OwnerPropertiesScreen extends StatefulWidget {
  const OwnerPropertiesScreen({super.key, this.initialProperties});

  final List<OwnerPropertyContent>? initialProperties;

  @override
  State<OwnerPropertiesScreen> createState() => _OwnerPropertiesScreenState();
}

class _OwnerPropertiesScreenState extends State<OwnerPropertiesScreen> {
  late final PagifyController<OwnerPropertyContent> _pagifyController;
  final ValueNotifier<bool> _isLoadingPropertyDetails = ValueNotifier<bool>(
    false,
  );

  @override
  void initState() {
    super.initState();
    _pagifyController = PagifyController<OwnerPropertyContent>();
  }

  @override
  void dispose() {
    _isLoadingPropertyDetails.dispose();
    super.dispose();
  }

  Future<void> _openAddProperty() async {
    final bool? shouldReturnToProperties = await Go.to<bool>(
      const OwnerPropertyFlowScreen(),
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
      OwnerPropertyFlowScreen(property: details),
    );
    if (updated == null || !mounted) {
      return;
    }
    _replaceProperty(_mergePropertyDetails(property, updated));
    _showMessage(LocaleKeys.ownerPropertiesSaved);
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
      details.district,
      details.city.name,
      details.city.governorateName,
    ].where((part) => part.trim().isNotEmpty).join('، ');
    return property.copyWith(
      title: details.title,
      mainImage: details.mainImage,
      location: location.isEmpty ? property.location : location,
      monthlyPrice: (double.tryParse(details.price) ?? 0).round(),
      pricePeriod: details.pricePeriod,
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

  void _replaceProperty(OwnerPropertyContent property) {
    final int index = _pagifyController.items.indexWhere(
      (item) => item.id == property.id,
    );
    if (index < 0) {
      return;
    }
    _pagifyController.replaceWith(index, property);
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(content: AppText(message, style: AppTextStyles.regular)),
      );
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
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
          child: OwnerPropertiesList(
            initialProperties: widget.initialProperties,
            pagifyController: _pagifyController,
            onAddPressed: _openAddProperty,
            onEditPressed: _openEdit,
            onRejectedPressed: _openRejection,
          ),
          builder: (context, isLoading, child) => Stack(
            children: [
              child!,
              if (isLoading)
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
      ),
    );
  }
}
