import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_filter_options_cubit.dart';

import '../widgets/tenant_filter/imports.dart';

class TenantFilterScreen extends StatefulWidget {
  const TenantFilterScreen({super.key, required this.initialFilters});

  final PropertySearchFilters initialFilters;

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

  Widget _buildShowResultsLabel() {
    return AppText(
      LocaleKeys.tenantFilterShowResults,
      color: AppColors.white,
      fontSize: 14.sp,
      fontWeight: FontWeight.w900,
    );
  }

  void _selectPropertyType(String value) {
    _updateFilters(
      _filters.copyWith(
        propertyType: _filters.propertyType == value ? '' : value,
        page: 1,
      ),
    );
  }

  void _toggleAmenity(String value) {
    final Set<String> selectedAmenities = Set<String>.from(_filters.amenities);
    selectedAmenities.contains(value)
        ? selectedAmenities.remove(value)
        : selectedAmenities.add(value);
    _updateFilters(_filters.copyWith(amenities: selectedAmenities, page: 1));
  }

  void _apply() => Go.back(_filters.copyWith(page: 1));

  List<TenantFilterOption> _withAll(List<TenantFilterOption> options) => [
    TenantFilterOption(value: '', label: LocaleKeys.tenantSearchAll),
    ...options.where((option) => option.selectionValue.isNotEmpty),
  ];

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
                      child: SingleChildScrollView(
                        padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 20.h),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            FilterCard(
                              title: LocaleKeys.tenantFilterOrdering,
                              child: SingleSelectGroup(
                                title: LocaleKeys.tenantFilterSortListings,
                                options: filterOptions.ordering,
                                selectedValue: _filters.ordering,
                                onSelected: (value) => _updateFilters(
                                  _filters.copyWith(ordering: value, page: 1),
                                ),
                              ),
                            ),
                            12.szH,
                            FilterCard(
                              title: LocaleKeys.tenantFilterPropertyType,
                              child: FilterChipWrap(
                                options: filterOptions.propertyTypes,
                                selectedValues: {_filters.propertyType},
                                onSelected: _selectPropertyType,
                              ),
                            ),
                            12.szH,
                            FilterCard(
                              title: LocaleKeys.tenantFilterLocation,
                              child: Column(
                                children: [
                                  FilterTextField(
                                    label: LocaleKeys.tenantFilterCity,
                                    hint: LocaleKeys.tenantFilterCityHint,
                                    controller: _cityController,
                                    onChanged: (value) => _updateFilters(
                                      _filters.copyWith(city: value, page: 1),
                                    ),
                                  ),
                                  10.szH,
                                  FilterTextField(
                                    label: LocaleKeys.tenantFilterDistrict,
                                    hint: LocaleKeys.tenantFilterDistrictHint,
                                    controller: _districtController,
                                    onChanged: (value) => _updateFilters(
                                      _filters.copyWith(
                                        district: value,
                                        page: 1,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            12.szH,
                            FilterCard(
                              title: LocaleKeys.tenantFilterPriceRange,
                              child: Row(
                                children: [
                                  Expanded(
                                    child: FilterTextField(
                                      label: LocaleKeys.tenantFilterFrom,
                                      hint: LocaleKeys.tenantFilterFrom,
                                      controller: _minPriceController,
                                      keyboardType: TextInputType.number,
                                      inputFormatters: [
                                        FilteringTextInputFormatter.digitsOnly,
                                      ],
                                      textAlign: TextAlign.center,
                                      onChanged: (value) => _updateFilters(
                                        _filters.copyWith(
                                          priceMin: value,
                                          page: 1,
                                        ),
                                      ),
                                    ),
                                  ),
                                  10.szW,
                                  AppText(
                                    '—',
                                    color: AppColors.sokoonGray,
                                    fontSize: 16.sp,
                                    fontWeight: FontWeight.w700,
                                  ),
                                  10.szW,
                                  Expanded(
                                    child: FilterTextField(
                                      label: LocaleKeys.tenantFilterTo,
                                      hint: LocaleKeys.tenantFilterTo,
                                      controller: _maxPriceController,
                                      keyboardType: TextInputType.number,
                                      inputFormatters: [
                                        FilteringTextInputFormatter.digitsOnly,
                                      ],
                                      textAlign: TextAlign.center,
                                      onChanged: (value) => _updateFilters(
                                        _filters.copyWith(
                                          priceMax: value,
                                          page: 1,
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            12.szH,
                            FilterCard(
                              title: LocaleKeys.tenantFilterPropertyDetails,
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  SingleSelectGroup(
                                    title: LocaleKeys.tenantFilterBedrooms,
                                    options: _withAll(filterOptions.bedrooms),
                                    selectedValue: _filters.bedrooms,
                                    onSelected: (value) => _updateFilters(
                                      _filters.copyWith(
                                        bedrooms: value,
                                        page: 1,
                                      ),
                                    ),
                                  ),
                                  12.szH,
                                  SingleSelectGroup(
                                    title: LocaleKeys.tenantFilterBathrooms,
                                    options: _withAll(filterOptions.bathrooms),
                                    selectedValue: _filters.bathrooms,
                                    onSelected: (value) => _updateFilters(
                                      _filters.copyWith(
                                        bathrooms: value,
                                        page: 1,
                                      ),
                                    ),
                                  ),
                                  12.szH,
                                  SingleSelectGroup(
                                    title: LocaleKeys.tenantFilterPricePeriod,
                                    options: _withAll(
                                      filterOptions.pricePeriods,
                                    ),
                                    selectedValue: _filters.pricePeriod,
                                    onSelected: (value) => _updateFilters(
                                      _filters.copyWith(
                                        pricePeriod: value,
                                        page: 1,
                                      ),
                                    ),
                                  ),
                                  12.szH,
                                  SingleSelectGroup(
                                    title: LocaleKeys.tenantFilterSuitableFor,
                                    options: _withAll(
                                      filterOptions.suitableFor,
                                    ),
                                    selectedValue: _filters.suitableFor,
                                    onSelected: (value) => _updateFilters(
                                      _filters.copyWith(
                                        suitableFor: value,
                                        page: 1,
                                      ),
                                    ),
                                  ),
                                  12.szH,
                                  SingleSelectGroup(
                                    title: LocaleKeys.tenantFilterFurnished,
                                    options: _withAll(
                                      filterOptions.booleanOptions,
                                    ),
                                    selectedValue: _filters.isFurnished,
                                    onSelected: (value) => _updateFilters(
                                      _filters.copyWith(
                                        isFurnished: value,
                                        page: 1,
                                      ),
                                    ),
                                  ),
                                  12.szH,
                                  SingleSelectGroup(
                                    title: LocaleKeys.tenantFilterSmoking,
                                    options: _withAll(
                                      filterOptions.booleanOptions,
                                    ),
                                    selectedValue: _filters.smokingAllowed,
                                    onSelected: (value) => _updateFilters(
                                      _filters.copyWith(
                                        smokingAllowed: value,
                                        page: 1,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            12.szH,
                            FilterCard(
                              title: LocaleKeys.tenantFilterAmenities,
                              child: FilterChipWrap(
                                options: filterOptions.amenities,
                                selectedValues: _filters.amenities,
                                onSelected: _toggleAmenity,
                              ),
                            ),
                            12.szH,
                            FilterCard(
                              title: LocaleKeys.tenantFilterVerification,
                              child: SingleSelectGroup(
                                title: LocaleKeys.tenantFilterVerified,
                                options: _withAll(filterOptions.booleanOptions),
                                selectedValue: _filters.isVerified,
                                onSelected: (value) => _updateFilters(
                                  _filters.copyWith(isVerified: value, page: 1),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    Container(
                      padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 16.h),
                      decoration: const BoxDecoration(
                        color: AppColors.white,
                        border: Border(
                          top: BorderSide(color: AppColors.grayPale),
                        ),
                      ),
                      child: GestureDetector(
                        onTap: _apply,
                        behavior: HitTestBehavior.opaque,
                        child: Container(
                          height: 48.h,
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: AppColors.sokoonTeal,
                            borderRadius: BorderRadius.circular(14.r),
                          ),
                          child: _buildShowResultsLabel(),
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
