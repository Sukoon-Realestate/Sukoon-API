import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_filter_options_cubit.dart';

import '../widgets/tenant_filter/imports.dart';

typedef TenantFiltersApplied =
    FutureOr<void> Function(PropertySearchFilters filters);

class TenantFilterScreen extends StatefulWidget {
  const TenantFilterScreen({
    super.key,
    required this.initialFilters,
    required this.onFiltersApplied,
  });

  final PropertySearchFilters initialFilters;
  final TenantFiltersApplied onFiltersApplied;

  @override
  State<TenantFilterScreen> createState() => _TenantFilterScreenState();
}

class _TenantFilterScreenState extends State<TenantFilterScreen> {
  late PropertySearchFilters _filters;
  late final TextEditingController _cityController;
  late final TextEditingController _districtController;
  late final TextEditingController _minPriceController;
  late final TextEditingController _maxPriceController;
  late final PropertyFilterOptionsCubit _propertyFilterOptionsCubit;
  late final Future<void> _propertyFilterOptionsRequest;

  @override
  void initState() {
    super.initState();
    _filters = widget.initialFilters;
    _cityController = TextEditingController(text: _filters.city);
    _districtController = TextEditingController(text: _filters.district);
    _minPriceController = TextEditingController(text: _filters.priceMin);
    _maxPriceController = TextEditingController(text: _filters.priceMax);
    _propertyFilterOptionsCubit = PropertyFilterOptionsCubit();
    _propertyFilterOptionsRequest = _propertyFilterOptionsCubit
        .getFilterOptions();
  }

  @override
  void dispose() {
    _cityController.dispose();
    _districtController.dispose();
    _minPriceController.dispose();
    _maxPriceController.dispose();
    _propertyFilterOptionsCubit.close();
    super.dispose();
  }

  void _reset() {
    final String defaultOrdering =
        _propertyFilterOptionsCubit.state.data.defaultOrdering;
    final PropertySearchFilters clearedFilters = widget.initialFilters
        .clearFilters();
    setState(() {
      _filters = defaultOrdering.isEmpty
          ? clearedFilters
          : clearedFilters.copyWith(ordering: defaultOrdering);
      _cityController.clear();
      _districtController.clear();
      _minPriceController.clear();
      _maxPriceController.clear();
    });
  }

  void _updateFilters(PropertySearchFilters filters) =>
      setState(() => _filters = filters);

  Future<void> _apply() async {
    final PropertySearchFilters filters = _filters.copyWith(page: 1);
    Go.back();
    await widget.onFiltersApplied(filters);
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider<PropertyFilterOptionsCubit>.value(
      value: _propertyFilterOptionsCubit,
      child:
          StatusBuilder<
            PropertyFilterOptionsCubit,
            PropertyFilterOptionsModel
          >.withShimmer(
            initialDataForShimmer: const PropertyFilterOptionsModel.initial(),
            requestToTryAgainWhenError: _propertyFilterOptionsRequest,
            errorType: ErrorType.defaultView,
            builder: (filterOptions) => Scaffold(
              backgroundColor: AppColors.scaffoldBackground,
              body: SafeArea(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    FilterTopBar(
                      activeCount: _filters.activeCount,
                      onReset: _reset,
                    ),
                    Expanded(
                      child: TenantFilterContent(
                        filters: _filters,
                        filterOptions: filterOptions,
                        cityController: _cityController,
                        districtController: _districtController,
                        minPriceController: _minPriceController,
                        maxPriceController: _maxPriceController,
                        onFiltersChanged: _updateFilters,
                      ),
                    ),
                    FilterApplyBar(onApplyPressed: _apply),
                  ],
                ),
              ),
            ),
          ),
    );
  }
}
