import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_details_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_save_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/imports.dart';

class PropertyDetailsScreen extends StatefulWidget {
  const PropertyDetailsScreen({super.key, required this.propertyId});

  final String propertyId;

  @override
  State<PropertyDetailsScreen> createState() => _PropertyDetailsScreenState();
}

class _PropertyDetailsScreenState extends State<PropertyDetailsScreen> {
  late final PropertyDetailsCubit _detailsCubit;
  late final PropertySaveCubit _saveCubit;
  late final Future<void> _detailsRequest;
  bool? _savedOverride;
  bool _isUpdatingSaved = false;

  @override
  void initState() {
    super.initState();
    _detailsCubit = PropertyDetailsCubit();
    _saveCubit = PropertySaveCubit();
    _detailsRequest = _detailsCubit.getPropertyDetails(widget.propertyId);
  }

  @override
  void dispose() {
    _detailsCubit.close();
    _saveCubit.close();
    super.dispose();
  }

  Future<void> _toggleSaved(TenantPropertyDetailsContent property) async {
    if (_isUpdatingSaved) return;

    final bool currentValue = _savedOverride ?? property.isSaved;
    final bool nextValue = !currentValue;
    final String propertyId = property.id.isEmpty
        ? widget.propertyId
        : property.id;

    setState(() {
      _savedOverride = nextValue;
      _isUpdatingSaved = true;
    });

    void rollbackSavedState(String _) {
      if (!mounted) return;
      setState(() => _savedOverride = currentValue);
    }

    if (nextValue) {
      await _saveCubit.saveProperty(
        propertyId: propertyId,
        onError: rollbackSavedState,
      );
    } else {
      await _saveCubit.unsaveProperty(
        propertyId: propertyId,
        onError: rollbackSavedState,
      );
    }
    if (!mounted) return;
    setState(() => _isUpdatingSaved = false);
  }

  Widget _buildDetails(PropertyDetailsModel data) {
    final TenantPropertyDetailsContent property =
        TenantPropertyDetailsContent.fromModel(data);
    return TenantPropertyDetailsBody(
      property: property,
      isSaved: _savedOverride ?? property.isSaved,
      onSavedPressed: () => _toggleSaved(property),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          bottom: false,
          child: BlocProvider<PropertyDetailsCubit>.value(
            value: _detailsCubit,
            child:
                StatusBuilder<
                  PropertyDetailsCubit,
                  PropertyDetailsModel
                >.withShimmer(
                  initialDataForShimmer: const PropertyDetailsModel.initial(),
                  requestToTryAgainWhenError: _detailsRequest,
                  builder: _buildDetails,
                  errorType: ErrorType.customView,
                  errorWidget: const TenantPropertyStatusView(
                    child: ExceptionView(),
                  ),
                ),
          ),
        ),
      ),
    );
  }
}
