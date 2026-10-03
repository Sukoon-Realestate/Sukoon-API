import '../../../data/models/property_location.dart';
import 'add_property_map_section.dart';
import 'property_selection_field.dart';
import 'add_property_details_section.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_types_model.dart';

import 'add_property_address_section.dart';
import 'add_property_type_selector.dart';
import 'add_property_field.dart';
import 'add_property_section_card.dart';
import 'add_property_step_shell.dart';

class AddPropertyBasicsPage extends StatelessWidget {
  const AddPropertyBasicsPage({
    super.key,
    required this.form,
    required this.titleController,
    required this.streetController,
    required this.bedroomsController,
    required this.bathroomsController,
    required this.spaceController,
    required this.floorController,
    required this.selectedGovernorate,
    required this.selectedCity,
    required this.locationDropdownGeneration,
    required this.onPropertyTypeSelected,
    required this.onTitleChanged,
    required this.onGovernorateChanged,
    required this.onCityChanged,
    required this.onStreetChanged,
    required this.onBedroomsChanged,
    required this.onBathroomsChanged,
    required this.onSpaceChanged,
    required this.onFloorChanged,
    required this.onLocationSelected,
    required this.onNext,
  });

  final OwnerAddPropertyFormState form;
  final TextEditingController titleController;
  final TextEditingController streetController;
  final TextEditingController bedroomsController;
  final TextEditingController bathroomsController;
  final TextEditingController spaceController;
  final TextEditingController floorController;
  final OwnerPropertyLocationModel? selectedGovernorate;
  final OwnerPropertyLocationModel? selectedCity;
  final int locationDropdownGeneration;
  final ValueChanged<PropertyTypeModel> onPropertyTypeSelected;
  final ValueChanged<String> onTitleChanged;
  final ValueChanged<OwnerPropertyLocationModel> onGovernorateChanged;
  final ValueChanged<OwnerPropertyLocationModel> onCityChanged;
  final ValueChanged<String> onStreetChanged;
  final ValueChanged<String> onBedroomsChanged;
  final ValueChanged<String> onBathroomsChanged;
  final ValueChanged<String> onSpaceChanged;
  final ValueChanged<String> onFloorChanged;
  final ValueChanged<PropertyLocation> onLocationSelected;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    return AddPropertyStepShell(
      activeSegments: 1,
      segmentCount: 3,
      progressSubtitle: LocaleKeys.ownerAddPropertyBasicsProgress,
      primaryLabel: LocaleKeys.ownerAddPropertyNextPhotos,
      onPrimaryTap: onNext,
      children: [
        AddPropertySectionCard(
          title: '${LocaleKeys.ownerAddPropertyType} *',
          child: PropertySelectionField(
            isValid: form.propertyTypeApiValue.isNotEmpty,
            child: AddPropertyTypeSelector(
              selectedValue: form.propertyTypeApiValue,
              onSelected: onPropertyTypeSelected,
            ),
          ),
        ),
        AddPropertySectionCard(
          title: LocaleKeys.ownerAddPropertyNameSection,
          child: AddPropertyField(
            field: AddPropertyFieldContent(
              label: LocaleKeys.ownerAddPropertyTitleLabel,
              value: LocaleKeys.ownerAddPropertyTitleExample,
            ),
            controller: titleController,
            onChanged: onTitleChanged,
            hint: LocaleKeys.ownerAddPropertyTitleHint,
          ),
        ),
        AddPropertyAddressSection(
          streetController: streetController,
          selectedGovernorate: selectedGovernorate,
          selectedCity: selectedCity,
          dropdownGeneration: locationDropdownGeneration,
          onGovernorateChanged: onGovernorateChanged,
          onCityChanged: onCityChanged,
          onStreetChanged: onStreetChanged,
        ),
        AddPropertyDetailsSection(
          bedroomsController: bedroomsController,
          bathroomsController: bathroomsController,
          spaceController: spaceController,
          floorController: floorController,
          onBedroomsChanged: onBedroomsChanged,
          onBathroomsChanged: onBathroomsChanged,
          onSpaceChanged: onSpaceChanged,
          onFloorChanged: onFloorChanged,
        ),
        PropertySelectionField(
          isValid: form.isLocationSelected,
          message: LocaleKeys.ownerAddPropertySelectLocation,
          child: AddPropertyMapSection(
            location: form.location,
            query: '${form.street}, ${form.locationSummary}',
            onLocationSelected: onLocationSelected,
          ),
        ),
      ],
    );
  }
}
