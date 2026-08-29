import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/lancher_helper.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_result_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_details_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_property_photos_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/imports.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';

class PropertyDetailsScreen extends StatefulWidget {
  const PropertyDetailsScreen({super.key, this.item, this.propertyId});

  final SearchResultContent? item;
  final String? propertyId;

  @override
  State<PropertyDetailsScreen> createState() => _PropertyDetailsScreenState();
}

class _PropertyDetailsScreenState extends State<PropertyDetailsScreen> {
  late final PropertyDetailsCubit? _detailsCubit;
  late final Future<void>? _detailsRequest;
  late final TenantPropertyDetailsContent? _mockProperty;
  bool? _favoriteOverride;
  bool? _savedOverride;

  @override
  void initState() {
    super.initState();
    final String? propertyId = widget.propertyId;
    if (propertyId != null) {
      _mockProperty = null;
      _detailsCubit = PropertyDetailsCubit();
      _detailsRequest = _detailsCubit!.getPropertyDetails(propertyId);
      return;
    }

    _detailsCubit = null;
    _detailsRequest = null;
    _mockProperty = TenantPropertyDetailsContent.fromSearchResult(
      widget.item ?? TenantSearchResultContent.results.first,
    );
  }

  @override
  void dispose() {
    _detailsCubit?.close();
    super.dispose();
  }

  void _toggleFavorite(bool initialValue) {
    setState(() => _favoriteOverride = !(_favoriteOverride ?? initialValue));
  }

  void _toggleSaved(bool initialValue) {
    setState(() => _savedOverride = !(_savedOverride ?? initialValue));
  }

  void _openPhotos(TenantPropertyDetailsContent property, [int index = 0]) {
    Go.to(TenantPropertyPhotosScreen(property: property, initialIndex: index));
  }

  Future<void> _openLocation(TenantPropertyDetailsContent property) async {
    await LauncherHelper.launchGoogleMaps(
      latitude: property.latitude,
      longitude: property.longitude,
    );
  }

  void _openBookVisit(TenantPropertyDetailsContent property) {
    Go.to(
      BookVisitScreen(
        property: VisitPropertyContent.fromPropertyDetails(property),
      ),
    );
  }

  Future<void> _copyPropertyLink(TenantPropertyDetailsContent property) async {
    await Clipboard.setData(ClipboardData(text: property.shareUrl));
    if (!mounted) return;

    Go.back();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(LocaleKeys.tenantPropertyDetailsLinkCopied)),
    );
  }

  void _closeShareSheet() => Go.back();

  void _showShareSheet(TenantPropertyDetailsContent property) {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: AppColors.transparent,
      builder: (_) => TenantPropertyShareSheet(
        onCopyLinkPressed: () => _copyPropertyLink(property),
        onSharePressed: _closeShareSheet,
        onCancelPressed: _closeShareSheet,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final PropertyDetailsCubit? cubit = _detailsCubit;
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          bottom: false,
          child: cubit == null
              ? _buildDetailsBody(_mockProperty!)
              : BlocProvider<PropertyDetailsCubit>.value(
                  value: cubit,
                  child:
                      StatusBuilder<
                        PropertyDetailsCubit,
                        PropertyDetailsModel
                      >.withShimmer(
                        initialDataForShimmer:
                            const PropertyDetailsModel.initial(),
                        requestToTryAgainWhenError: _detailsRequest!,
                        builder: (data) => _buildDetailsBody(
                          TenantPropertyDetailsContent.fromModel(data),
                        ),
                        errorType: ErrorType.customView,
                        errorWidget: TenantPropertyStatusView(
                          onBackPressed: Go.back,
                          child: const ExceptionView(),
                        ),
                      ),
                ),
        ),
      ),
    );
  }

  Widget _buildDetailsBody(TenantPropertyDetailsContent property) {
    final bool isFavorite = _favoriteOverride ?? property.isFavorite;
    final bool isSaved = _savedOverride ?? property.isSaved;
    return TenantPropertyDetailsBody(
      property: property,
      isFavorite: isFavorite,
      isSaved: isSaved,
      onBackPressed: Go.back,
      onSharePressed: () => _showShareSheet(property),
      onFavoritePressed: () => _toggleFavorite(property.isFavorite),
      onSavedPressed: () => _toggleSaved(property.isSaved),
      onPhotosPressed: (index) => _openPhotos(property, index),
      onLocationPressed: () => _openLocation(property),
      onBookVisitPressed: () => _openBookVisit(property),
    );
  }
}
