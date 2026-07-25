part of '../../imports.dart';

class OwnerPropertiesScreen extends StatefulWidget {
  const OwnerPropertiesScreen({super.key, this.initialProperties});

  final List<OwnerPropertyContent>? initialProperties;

  @override
  State<OwnerPropertiesScreen> createState() => _OwnerPropertiesScreenState();
}

class _OwnerPropertiesScreenState extends State<OwnerPropertiesScreen> {
  late List<OwnerPropertyContent> _properties;

  @override
  void initState() {
    super.initState();
    _properties = List<OwnerPropertyContent>.of(
      widget.initialProperties ?? OwnerPropertiesContent.prototype(),
    );
  }

  Future<void> _openAddProperty() async {
    final bool? shouldReturnToProperties = await Go.to<bool>(
      OwnerAddPropertyFlowScreen(onViewProperties: () => Go.back(true)),
    );
    if (shouldReturnToProperties == true && mounted) {
      _showMessage(LocaleKeys.ownerPropertiesSubmittedMessage);
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
    final int index = _properties.indexWhere((item) => item.id == property.id);
    if (index < 0) {
      return;
    }
    setState(() => _properties[index] = property);
  }

  void _deleteProperty(OwnerPropertyContent property) {
    setState(() {
      _properties.removeWhere((item) => item.id == property.id);
    });
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
                child: _properties.isEmpty
                    ? _OwnerPropertiesEmptyState(onAddPressed: _openAddProperty)
                    : ListView.separated(
                        padding: EdgeInsets.fromLTRB(20.w, 8.h, 20.w, 20.h),
                        itemBuilder: (context, index) {
                          final OwnerPropertyContent property =
                              _properties[index];
                          return OwnerPropertyCard(
                            property: property,
                            onEditPressed: () => _openEdit(property),
                            onAnalyticsPressed: () => _openAnalytics(property),
                            onActionsPressed: () => _openActions(property),
                            onPressed: property.status.isRejected
                                ? () => _openRejection(property)
                                : () => _openActions(property),
                          );
                        },
                        separatorBuilder: (context, index) => 12.szH,
                        itemCount: _properties.length,
                      ),
              ),
            ],
          ),
        ),
        bottomNavigationBar: const OwnerPropertiesBottomNavigation(
          activeTab: OwnerPropertiesNavigationTab.properties,
        ),
      ),
    );
  }
}

class _OwnerPropertiesEmptyState extends StatelessWidget {
  const _OwnerPropertiesEmptyState({required this.onAddPressed});

  final VoidCallback onAddPressed;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: EdgeInsets.all(28.w),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 88.r,
              height: 88.r,
              decoration: const BoxDecoration(
                color: AppColors.mintPale,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.apartment_rounded,
                color: AppColors.sokoonTeal,
                size: 40.r,
              ),
            ),
            16.szH,
            AppText(
              LocaleKeys.ownerPropertiesEmptyTitle,
              color: AppColors.sokoonNavy,
              fontSize: 18.sp,
              fontWeight: FontWeight.w900,
              textAlign: TextAlign.center,
            ),
            8.szH,
            AppText(
              LocaleKeys.ownerPropertiesEmptyDescription,
              color: AppColors.sokoonGray,
              fontSize: 14.sp,
              textAlign: TextAlign.center,
            ),
            20.szH,
            DefaultButton(
              title: LocaleKeys.ownerPropertiesAdd,
              onTap: onAddPressed,
              width: 190.w,
              height: 46.h,
              borderRadius: BorderRadius.circular(14.r),
              fontWeight: FontWeight.w900,
            ),
          ],
        ),
      ),
    );
  }
}
