import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_result_content.dart';

import '../widgets/tenant_filter/imports.dart';

class TenantFilterScreen extends StatefulWidget {
  const TenantFilterScreen({super.key, required this.initialFilters});

  final TenantSearchResultsFilterState initialFilters;

  @override
  State<TenantFilterScreen> createState() => _TenantFilterScreenState();
}

class _TenantFilterScreenState extends State<TenantFilterScreen> {
  late TenantFilterFormState _form;
  late final TextEditingController _cityController;
  late final TextEditingController _districtController;
  late final TextEditingController _minPriceController;
  late final TextEditingController _maxPriceController;

  @override
  void initState() {
    super.initState();
    _form = TenantFilterFormState.initial(
      query: widget.initialFilters.query,
      selectedFilters: widget.initialFilters.selectedFilters,
    );
    _cityController = TextEditingController(text: _form.city);
    _districtController = TextEditingController(text: _form.district);
    _minPriceController = TextEditingController(text: _form.minPrice);
    _maxPriceController = TextEditingController(text: _form.maxPrice);
  }

  @override
  void dispose() {
    _cityController.dispose();
    _districtController.dispose();
    _minPriceController.dispose();
    _maxPriceController.dispose();
    super.dispose();
  }

  void _reset() {
    setState(() {
      _form = TenantFilterFormState.initial();
      _cityController.clear();
      _districtController.clear();
      _minPriceController.clear();
      _maxPriceController.clear();
    });
  }

  void _togglePropertyType(String value) {
    final selected = Set<String>.from(_form.propertyTypes);
    selected.contains(value) ? selected.remove(value) : selected.add(value);
    setState(() => _form = _form.copyWith(propertyTypes: selected));
  }

  void _toggleAmenity(String value) {
    final selected = Set<String>.from(_form.amenities);
    selected.contains(value) ? selected.remove(value) : selected.add(value);
    setState(() => _form = _form.copyWith(amenities: selected));
  }

  void _apply() {
    Navigator.of(context).pop(
      TenantSearchResultsFilterState(
        query: _form.query.isEmpty ? widget.initialFilters.query : _form.query,
        selectedFilters: _form.selectedFilters,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              FilterTopBar(activeCount: _form.activeCount, onReset: _reset),
              Expanded(
                child: SingleChildScrollView(
                  padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 20.h),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      FilterCard(
                        title: 'نوع العقار',
                        child: FilterChipWrap(
                          options: TenantPropertyFilterOptions.propertyTypes,
                          selectedValues: _form.propertyTypes,
                          onSelected: _togglePropertyType,
                        ),
                      ),
                      12.szH,
                      FilterCard(
                        title: 'المدينة والمنطقة',
                        child: Column(
                          children: [
                            FilterTextField(
                              label: 'المدينة',
                              hint: 'مثال: القاهرة، الرياض…',
                              controller: _cityController,
                              onChanged: (value) => setState(
                                () => _form = _form.copyWith(city: value),
                              ),
                            ),
                            10.szH,
                            FilterTextField(
                              label: 'المنطقة / الحي',
                              hint: 'مثال: مدينة نصر، التجمع…',
                              controller: _districtController,
                              onChanged: (value) => setState(
                                () => _form = _form.copyWith(district: value),
                              ),
                            ),
                          ],
                        ),
                      ),
                      12.szH,
                      FilterCard(
                        title: 'نطاق السعر (ر.س / ج)',
                        child: Row(
                          children: [
                            Expanded(
                              child: FilterTextField(
                                label: 'من',
                                hint: 'من',
                                controller: _minPriceController,
                                keyboardType: TextInputType.number,
                                inputFormatters: [
                                  FilteringTextInputFormatter.digitsOnly,
                                ],
                                textAlign: TextAlign.center,
                                onChanged: (value) => setState(
                                  () => _form = _form.copyWith(minPrice: value),
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
                                label: 'إلى',
                                hint: 'إلى',
                                controller: _maxPriceController,
                                keyboardType: TextInputType.number,
                                inputFormatters: [
                                  FilteringTextInputFormatter.digitsOnly,
                                ],
                                textAlign: TextAlign.center,
                                onChanged: (value) => setState(
                                  () => _form = _form.copyWith(maxPrice: value),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      12.szH,
                      FilterCard(
                        title: 'تفاصيل العقار',
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            SingleSelectGroup(
                              title: 'عدد الغرف',
                              options: TenantPropertyFilterOptions.rooms,
                              selectedValue: _form.rooms,
                              onSelected: (value) => setState(
                                () => _form = _form.copyWith(rooms: value),
                              ),
                            ),
                            12.szH,
                            SingleSelectGroup(
                              title: 'عدد الحمامات',
                              options: TenantPropertyFilterOptions.bathrooms,
                              selectedValue: _form.bathrooms,
                              onSelected: (value) => setState(
                                () => _form = _form.copyWith(bathrooms: value),
                              ),
                            ),
                            12.szH,
                            SingleSelectGroup(
                              title: 'مدة الإيجار',
                              options: TenantPropertyFilterOptions.rentalTerms,
                              selectedValue: _form.rentalTerm,
                              onSelected: (value) => setState(
                                () => _form = _form.copyWith(rentalTerm: value),
                              ),
                            ),
                            12.szH,
                            SingleSelectGroup(
                              title: 'مناسب لـ',
                              options: TenantPropertyFilterOptions.tenantTypes,
                              selectedValue: _form.tenantType,
                              onSelected: (value) => setState(
                                () => _form = _form.copyWith(tenantType: value),
                              ),
                            ),
                            12.szH,
                            SingleSelectGroup(
                              title: 'التدخين',
                              options:
                                  TenantPropertyFilterOptions.smokingOptions,
                              selectedValue: _form.smoking,
                              onSelected: (value) => setState(
                                () => _form = _form.copyWith(smoking: value),
                              ),
                            ),
                          ],
                        ),
                      ),
                      12.szH,
                      FilterCard(
                        title: 'المرافق والخدمات',
                        child: FilterChipWrap(
                          options: TenantPropertyFilterOptions.amenities,
                          selectedValues: _form.amenities,
                          onSelected: _toggleAmenity,
                        ),
                      ),
                      12.szH,
                      FilterCard(
                        title: 'التوثيق',
                        child: Column(
                          children: [
                            SwitchRow(
                              title: 'عقارات موثقة فقط',
                              subtitle: 'عقارات مراجعة ومعتمدة من سكون',
                              value: _form.verifiedOnly,
                              onChanged: (value) => setState(
                                () =>
                                    _form = _form.copyWith(verifiedOnly: value),
                              ),
                            ),
                            const Divider(color: AppColors.sokoonBorder),
                            SwitchRow(
                              title: 'إثبات ملكية تم التحقق منه',
                              subtitle: 'المالك أثبت ملكية العقار',
                              value: _form.ownershipVerifiedOnly,
                              onChanged: (value) => setState(
                                () => _form = _form.copyWith(
                                  ownershipVerifiedOnly: value,
                                ),
                              ),
                            ),
                            10.szH,
                            Container(
                              padding: EdgeInsets.all(10.w),
                              decoration: BoxDecoration(
                                color: AppColors.yellowPale,
                                borderRadius: BorderRadius.circular(10.r),
                              ),
                              child: Row(
                                children: [
                                  Icon(
                                    Icons.privacy_tip_outlined,
                                    color: AppColors.brown,
                                    size: 16.r,
                                  ),
                                  8.szW,
                                  Expanded(
                                    child: AppText(
                                      'المستندات الخاصة لا تظهر للمستخدمين — فقط حالة التحقق',
                                      color: AppColors.brown,
                                      fontSize: 12.sp,
                                      fontWeight: FontWeight.w500,
                                      maxLines: 2,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
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
                    child: AppText(
                      'عرض النتائج (${_form.activeCount} فلاتر نشطة)',
                      color: AppColors.white,
                      fontSize: 14.sp,
                      fontWeight: FontWeight.w900,
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
