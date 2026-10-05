import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_dropinity.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';

import 'add_property_field.dart';
import 'package:melos_core/core/helpers/validators.dart';
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
    this.governorateFieldKey,
    this.cityFieldKey,
    this.streetFieldKey,
  });

  final TextEditingController streetController;
  final OwnerPropertyLocationModel? selectedGovernorate;
  final OwnerPropertyLocationModel? selectedCity;
  final int dropdownGeneration;
  final ValueChanged<OwnerPropertyLocationModel> onGovernorateChanged;
  final ValueChanged<OwnerPropertyLocationModel> onCityChanged;
  final ValueChanged<String> onStreetChanged;
  final GlobalKey? governorateFieldKey;
  final GlobalKey? cityFieldKey;
  final GlobalKey? streetFieldKey;

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
  ) async {
    final OwnerPropertyLocationModel? governorate = selectedGovernorate;
    if (governorate == null) {
      return const [];
    }
    final OwnerPropertyLocationsResponse response =
        await OwnerPropertiesData.getCities(
          governorateId: governorate.id,
          search: '',
        );
    return response.results;
  }

  @override
  Widget build(BuildContext context) {
    final OwnerPropertyLocationModel? governorate = selectedGovernorate;

    return AddPropertySectionCard(
      title: LocaleKeys.ownerAddPropertyAddressSection,
      child: Column(
        spacing: 10.h,
        children: [
          KeyedSubtree(
            key: governorateFieldKey,
            child:
                AppDropinity<
                  List<OwnerPropertyLocationModel>,
                  OwnerPropertyLocationModel
                >.withApiRequest(
                  key: ValueKey(
                    'owner-property-governorate-$dropdownGeneration',
                  ),
                  listHeight: 220.h,
                  initialValue: selectedGovernorate,
                  hint: LocaleKeys.ownerAddPropertyChoose,
                  title: '${LocaleKeys.ownerAddPropertyGovernorate} *',
                  asyncCall: _getGovernorates,
                  cacheKey: OwnerPropertiesData.governoratesCacheKey,
                  cacheToJson: (item) => item.toJson(),
                  cacheFromJson: OwnerPropertyLocationModel.fromJson,
                  getLabel: (item) => item.name,
                  validator: (_) =>
                      Validators.validateRequired(selectedGovernorate),
                  onChanged: onGovernorateChanged,
                ),
          ),
          IgnorePointer(
            key: cityFieldKey,
            ignoring: governorate == null,
            child: Opacity(
              opacity: governorate == null ? 0.55 : 1,
              child: governorate == null
                  ? AppDropinityLocal<OwnerPropertyLocationModel>(
                      key: ValueKey(
                        'owner-property-city-disabled-$dropdownGeneration',
                      ),
                      initialValue: null,
                      hint: LocaleKeys.ownerAddPropertyChoose,
                      title: '${LocaleKeys.ownerAddPropertyCity} *',
                      values: const [],
                      getLabel: (item) => item.name,
                      validator: (_) =>
                          Validators.validateRequired(selectedCity),
                      onChanged: onCityChanged,
                    )
                  : AppDropinity<
                      List<OwnerPropertyLocationModel>,
                      OwnerPropertyLocationModel
                    >.withApiRequest(
                      key: ValueKey(
                        'owner-property-city-${governorate.id}-$dropdownGeneration',
                      ),
                      listHeight: 220.h,
                      initialValue: selectedCity,
                      hint: LocaleKeys.ownerAddPropertyChoose,
                      title: '${LocaleKeys.ownerAddPropertyCity} *',
                      asyncCall: _getCities,
                      cacheKey: OwnerPropertiesData.citiesCacheKey(
                        governorate.id,
                      ),
                      cacheToJson: (item) => item.toJson(),
                      cacheFromJson: OwnerPropertyLocationModel.fromJson,
                      getLabel: (item) => item.name,
                      validator: (_) =>
                          Validators.validateRequired(selectedCity),
                      onChanged: onCityChanged,
                    ),
            ),
          ),
          AddPropertyField(
            key: streetFieldKey,
            field: AddPropertyFieldContent(
              label: LocaleKeys.propertyDistrict,
              value: LocaleKeys.propertyDistrictHint,
            ),
            controller: streetController,
            onChanged: onStreetChanged,
            hint: LocaleKeys.propertyDistrictHint,
          ),
        ],
      ),
    );
  }
}
