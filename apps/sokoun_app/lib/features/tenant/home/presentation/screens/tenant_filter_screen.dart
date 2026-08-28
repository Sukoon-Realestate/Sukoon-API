import 'dart:async';

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
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_search_count_cubit.dart';

import '../widgets/tenant_filter/imports.dart';

class TenantFilterScreen extends StatefulWidget {
  const TenantFilterScreen({super.key, required this.initialFilters});

  final PropertySearchFilters initialFilters;

  @override
  State<TenantFilterScreen> createState() => _TenantFilterScreenState();
}

class _TenantFilterScreenState extends State<TenantFilterScreen> {
  static const Duration _countDebounceDuration = Duration(milliseconds: 400);

  late PropertySearchFilters _filters;
  late final TextEditingController _cityController;
  late final TextEditingController _districtController;
  late final TextEditingController _minPriceController;
  late final TextEditingController _maxPriceController;
  late final PropertySearchCountCubit _propertySearchCountCubit;
  late Future<void> _propertySearchCountRequest;
  Timer? _countDebounce;

  @override
  void initState() {
    super.initState();
    _filters = widget.initialFilters;
    _cityController = TextEditingController(text: _filters.city);
    _districtController = TextEditingController(text: _filters.district);
    _minPriceController = TextEditingController(text: _filters.priceMin);
    _maxPriceController = TextEditingController(text: _filters.priceMax);
    _propertySearchCountCubit = PropertySearchCountCubit();
    _propertySearchCountRequest = _propertySearchCountCubit.getCount(_filters);
  }

  @override
  void dispose() {
    _cityController.dispose();
    _districtController.dispose();
    _minPriceController.dispose();
    _maxPriceController.dispose();
    _countDebounce?.cancel();
    _propertySearchCountCubit.close();
    super.dispose();
  }

  void _reset() {
    setState(() {
      _filters = widget.initialFilters.clearFilters();
      _cityController.clear();
      _districtController.clear();
      _minPriceController.clear();
      _maxPriceController.clear();
    });
    _scheduleResultCountRefresh();
  }

  void _updateFilters(
    PropertySearchFilters filters, {
    bool debounceCount = false,
  }) {
    setState(() => _filters = filters);
    _scheduleResultCountRefresh(debounce: debounceCount);
  }

  void _scheduleResultCountRefresh({bool debounce = false}) {
    _countDebounce?.cancel();
    if (debounce) {
      _countDebounce = Timer(_countDebounceDuration, _refreshResultCount);
      return;
    }
    _refreshResultCount();
  }

  void _refreshResultCount() {
    if (!mounted) return;
    final Future<void> request = _propertySearchCountCubit.getCount(_filters);
    setState(() => _propertySearchCountRequest = request);
  }

  Widget _buildShowResultsLabel([int? count]) {
    return AppText(
      count == null
          ? LocaleKeys.tenantFilterShowResults
          : '${LocaleKeys.tenantFilterShowResults} ($count)',
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

  @override
  Widget build(BuildContext context) {
    return BlocProvider.value(
      value: _propertySearchCountCubit,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              FilterTopBar(activeCount: _filters.activeCount, onReset: _reset),
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
                          options: TenantPropertyFilterOptions.ordering,
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
                          options: TenantPropertyFilterOptions.propertyTypes,
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
                                debounceCount: true,
                              ),
                            ),
                            10.szH,
                            FilterTextField(
                              label: LocaleKeys.tenantFilterDistrict,
                              hint: LocaleKeys.tenantFilterDistrictHint,
                              controller: _districtController,
                              onChanged: (value) => _updateFilters(
                                _filters.copyWith(district: value, page: 1),
                                debounceCount: true,
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
                                  _filters.copyWith(priceMin: value, page: 1),
                                  debounceCount: true,
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
                                  _filters.copyWith(priceMax: value, page: 1),
                                  debounceCount: true,
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
                              options: TenantPropertyFilterOptions.counts,
                              selectedValue: _filters.bedrooms,
                              onSelected: (value) => _updateFilters(
                                _filters.copyWith(bedrooms: value, page: 1),
                              ),
                            ),
                            12.szH,
                            SingleSelectGroup(
                              title: LocaleKeys.tenantFilterBathrooms,
                              options: TenantPropertyFilterOptions.counts,
                              selectedValue: _filters.bathrooms,
                              onSelected: (value) => _updateFilters(
                                _filters.copyWith(bathrooms: value, page: 1),
                              ),
                            ),
                            12.szH,
                            SingleSelectGroup(
                              title: LocaleKeys.tenantFilterPricePeriod,
                              options: TenantPropertyFilterOptions.pricePeriods,
                              selectedValue: _filters.pricePeriod,
                              onSelected: (value) => _updateFilters(
                                _filters.copyWith(pricePeriod: value, page: 1),
                              ),
                            ),
                            12.szH,
                            SingleSelectGroup(
                              title: LocaleKeys.tenantFilterSuitableFor,
                              options: TenantPropertyFilterOptions.suitableFor,
                              selectedValue: _filters.suitableFor,
                              onSelected: (value) => _updateFilters(
                                _filters.copyWith(suitableFor: value, page: 1),
                              ),
                            ),
                            12.szH,
                            SingleSelectGroup(
                              title: LocaleKeys.tenantFilterFurnished,
                              options:
                                  TenantPropertyFilterOptions.booleanOptions,
                              selectedValue: _filters.isFurnished,
                              onSelected: (value) => _updateFilters(
                                _filters.copyWith(isFurnished: value, page: 1),
                              ),
                            ),
                            12.szH,
                            SingleSelectGroup(
                              title: LocaleKeys.tenantFilterSmoking,
                              options:
                                  TenantPropertyFilterOptions.booleanOptions,
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
                          options: TenantPropertyFilterOptions.amenities,
                          selectedValues: _filters.amenities,
                          onSelected: _toggleAmenity,
                        ),
                      ),
                      12.szH,
                      FilterCard(
                        title: LocaleKeys.tenantFilterVerification,
                        child: SingleSelectGroup(
                          title: LocaleKeys.tenantFilterVerified,
                          options: TenantPropertyFilterOptions.booleanOptions,
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
                  border: Border(top: BorderSide(color: AppColors.grayPale)),
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
                    child:
                        StatusBuilder<
                          PropertySearchCountCubit,
                          int
                        >.withShimmer(
                          initialDataForShimmer: 0,
                          requestToTryAgainWhenError:
                              _propertySearchCountRequest,
                          errorType: ErrorType.customView,
                          errorWidget: _buildShowResultsLabel(),
                          builder: _buildShowResultsLabel,
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
