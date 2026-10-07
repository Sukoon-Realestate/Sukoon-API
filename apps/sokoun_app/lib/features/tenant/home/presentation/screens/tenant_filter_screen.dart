import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/first_validation_error_form.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
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
    this.initialFilterOptions,
    this.onFilterOptionsLoaded,
  });

  final PropertySearchFilters initialFilters;
  final TenantFiltersApplied onFiltersApplied;
  final PropertyFilterOptionsModel? initialFilterOptions;
  final ValueChanged<PropertyFilterOptionsModel>? onFilterOptionsLoaded;

  @override
  State<TenantFilterScreen> createState() => _TenantFilterScreenState();
}

class _TenantFilterScreenState extends State<TenantFilterScreen> {
  final GlobalKey _priceRangeFieldKey = GlobalKey();
  late final ValueNotifier<PropertySearchFilters> _filters;
  late final TextEditingController _cityController;
  late final TextEditingController _districtController;
  late final TextEditingController _minPriceController;
  late final TextEditingController _maxPriceController;
  late final PropertyFilterOptionsCubit _propertyFilterOptionsCubit;

  @override
  void initState() {
    super.initState();
    _filters = ValueNotifier<PropertySearchFilters>(widget.initialFilters);
    _cityController = TextEditingController(text: _filters.value.city);
    _districtController = TextEditingController(text: _filters.value.district);
    _minPriceController = TextEditingController(text: _filters.value.priceMin);
    _maxPriceController = TextEditingController(text: _filters.value.priceMax);
    _propertyFilterOptionsCubit = PropertyFilterOptionsCubit(
      initialOptions: widget.initialFilterOptions,
    );
    if (widget.initialFilterOptions == null) {
      _loadFilterOptions();
    }
  }

  Future<void> _loadFilterOptions() async {
    await _propertyFilterOptionsCubit.getFilterOptions();
    if (mounted && _propertyFilterOptionsCubit.state.isSuccess) {
      widget.onFilterOptionsLoaded?.call(_propertyFilterOptionsCubit.data);
    }
  }

  @override
  void dispose() {
    _cityController.dispose();
    _districtController.dispose();
    _minPriceController.dispose();
    _maxPriceController.dispose();
    _filters.dispose();
    _propertyFilterOptionsCubit.close();
    super.dispose();
  }

  void _reset() {
    final String defaultOrdering =
        _propertyFilterOptionsCubit.state.data.defaultOrdering;
    final PropertySearchFilters clearedFilters = widget.initialFilters
        .clearFilters();
    _cityController.clear();
    _districtController.clear();
    _minPriceController.clear();
    _maxPriceController.clear();
    _filters.value = defaultOrdering.isEmpty
        ? clearedFilters
        : clearedFilters.copyWith(ordering: defaultOrdering);
  }

  void _updateFilters(PropertySearchFilters filters) =>
      _filters.value = filters;

  Future<void> _apply() async {
    final PropertySearchFilters filters = _filters.value.copyWith(page: 1);
    Go.back();
    await widget.onFiltersApplied(filters);
  }

  List<FirstValidationErrorField> _validationFields() => [
    FirstValidationErrorField(
      fieldKey: _priceRangeFieldKey,
      title: LocaleKeys.tenantFilterPriceRange,
      value: _maxPriceController.text,
      validator: (_) => !_filters.value.hasValidPriceRange
          ? LocaleKeys.searchPriceRangeError
          : RentalOfferCapabilities.configured.canSearch &&
                _filters.value.requiresPricePeriod &&
                _filters.value.pricePeriod.isEmpty
          ? LocaleKeys.rentalPricePeriodRequired
          : null,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return BlocProvider<PropertyFilterOptionsCubit>.value(
      value: _propertyFilterOptionsCubit,
      child: AppScaffold(
        title: LocaleKeys.tenantFilterTitle,
        titleWidget: Row(
          mainAxisSize: MainAxisSize.min,
          spacing: 8.w,
          children: [
            Flexible(
              child: AppText(
                LocaleKeys.tenantFilterTitle,
                style: AppTextStyles.extraBold.copyWith(fontSize: 16.sp),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            ValueListenableBuilder<PropertySearchFilters>(
              valueListenable: _filters,
              builder: (context, filters, _) => Badge(
                label: AppText(
                  '${filters.activeCount}',
                  style: AppTextStyles.regular10.copyWith(
                    color: AppColors.white,
                  ),
                ),
              ),
            ),
          ],
        ),
        showBackButton: true,
        actions: [
          TextButton(
            onPressed: _reset,
            child: AppText(
              LocaleKeys.tenantFilterReset,
              style: AppTextStyles.bold13.copyWith(
                color: context.appColor(AppColors.sokoonTeal),
              ),
            ),
          ),
        ],
        backgroundColor: context.appColor(
          AppColors.scaffoldBackground,
          surface: true,
        ),
        body: SafeArea(
          child:
              StatusBuilder<
                PropertyFilterOptionsCubit,
                PropertyFilterOptionsModel
              >.withShimmer(
                initialDataForShimmer:
                    const PropertyFilterOptionsModel.initial(),
                onRetry: _loadFilterOptions,
                errorType: ErrorType.defaultView,
                builder: (filterOptions) =>
                    ValueListenableBuilder<PropertySearchFilters>(
                      valueListenable: _filters,
                      builder: (context, filters, _) =>
                          FirstValidationErrorForm(
                            validationFields: _validationFields,
                            onValid: _apply,
                            builder: (context, submit) => Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                Expanded(
                                  child: TenantFilterContent(
                                    priceRangeFieldKey: _priceRangeFieldKey,
                                    filters: filters,
                                    filterOptions: filterOptions,
                                    cityController: _cityController,
                                    districtController: _districtController,
                                    minPriceController: _minPriceController,
                                    maxPriceController: _maxPriceController,
                                    onFiltersChanged: _updateFilters,
                                  ),
                                ),
                                FilterApplyBar(onApplyPressed: submit),
                              ],
                            ),
                          ),
                    ),
              ),
        ),
      ),
    );
  }
}
