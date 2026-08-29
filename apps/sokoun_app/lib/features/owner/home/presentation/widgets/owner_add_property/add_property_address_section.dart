import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_dropinity.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';

import 'add_property_field.dart';
import 'add_property_section_card.dart';

class AddPropertyAddressSection extends StatelessWidget {
  const AddPropertyAddressSection({
    super.key,
    required this.streetController,
    required this.selectedGovernorate,
    required this.selectedCity,
    required this.dropdownGeneration,
    required this.onGovernorateChanged,
    required this.onCityChanged,
    required this.onStreetChanged,
  });

  final TextEditingController streetController;
  final OwnerPropertyLocationModel? selectedGovernorate;
  final OwnerPropertyLocationModel? selectedCity;
  final int dropdownGeneration;
  final ValueChanged<OwnerPropertyLocationModel> onGovernorateChanged;
  final ValueChanged<OwnerPropertyLocationModel> onCityChanged;
  final ValueChanged<String> onStreetChanged;

  Future<List<OwnerPropertyLocationModel>> _getGovernorates(
    BuildContext context,
    int page,
  ) async {
    final OwnerPropertyLocationsResponse response =
        await OwnerPropertiesData.getGovernorates();
    return response.results;
  }

  Future<List<OwnerPropertyLocationModel>> _getCities(
    BuildContext context,
    int page,
    String search,
  ) async {
    final OwnerPropertyLocationModel? governorate = selectedGovernorate;
    if (governorate == null) {
      return const [];
    }
    final OwnerPropertyLocationsResponse response =
        await OwnerPropertiesData.getCities(
          governorateId: governorate.id,
          search: search,
        );
    return response.results;
  }

  @override
  Widget build(BuildContext context) {
    final OwnerPropertyLocationModel? governorate = selectedGovernorate;

    return AddPropertySectionCard(
      title: 'المنطقة والعنوان',
      child: Column(
        children: [
          AppDropinity<
            List<OwnerPropertyLocationModel>,
            OwnerPropertyLocationModel
          >.withApiRequest(
            key: ValueKey('owner-property-governorate-$dropdownGeneration'),
            listHeight: 220.h,
            initialValue: selectedGovernorate,
            hint: 'اختر',
            title: 'المحافظة',
            asyncCall: _getGovernorates,
            getLabel: (item) => item.name,
            onChanged: onGovernorateChanged,
          ),
          10.szH,
          IgnorePointer(
            ignoring: governorate == null,
            child: Opacity(
              opacity: governorate == null ? 0.55 : 1,
              child: governorate == null
                  ? AppDropinityLocal<OwnerPropertyLocationModel>(
                      key: ValueKey(
                        'owner-property-city-disabled-$dropdownGeneration',
                      ),
                      initialValue: null,
                      hint: 'اختر',
                      title: 'المدينة',
                      values: const [],
                      getLabel: (item) => item.name,
                      onChanged: onCityChanged,
                    )
                  : AppDropinity<
                      List<OwnerPropertyLocationModel>,
                      OwnerPropertyLocationModel
                    >.withApiSearchRequest(
                      key: ValueKey(
                        'owner-property-city-${governorate.id}-$dropdownGeneration',
                      ),
                      listHeight: 220.h,
                      initialValue: selectedCity,
                      hint: 'اختر',
                      title: 'المدينة',
                      asyncSearchCall: _getCities,
                      getLabel: (item) => item.name,
                      onChanged: onCityChanged,
                    ),
            ),
          ),
          10.szH,
          AddPropertyField(
            field: const AddPropertyFieldContent(
              label: 'الشارع',
              value: 'اكتب اسم الشارع',
            ),
            controller: streetController,
            onChanged: onStreetChanged,
            hint: 'اكتب اسم الشارع',
          ),
        ],
      ),
    );
  }
}
