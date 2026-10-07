import '../../../data/models/property_location.dart';
import 'add_property_map_section.dart';
import 'property_selection_field.dart';
import 'add_property_details_section.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:melos_core/core/widgets/first_validation_error_form.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_types_model.dart';

import 'add_property_address_section.dart';
import 'add_property_type_selector.dart';
import 'add_property_field.dart';
import 'add_property_section_card.dart';
import 'add_property_step_shell.dart';
import 'property_form_validation.dart';
import 'rental_inventory_editor.dart';
import 'rental_property_facilities.dart';
import 'rental_property_specifications.dart';
import 'rental_terms_fields.dart';
import 'add_property_additional_details.dart';
import 'package:sokoun_app/features/owner/home/data/owner_accommodation_draft_data.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/localized_digits_formatter.dart';

class AddPropertyBasicsPage extends StatefulWidget {
  const AddPropertyBasicsPage({
    super.key,
    required this.form,
    this.rentalScopeSelector,
    this.onFormChanged,
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
  final Widget? rentalScopeSelector;
  final ValueChanged<OwnerAddPropertyFormState>? onFormChanged;
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
  State<AddPropertyBasicsPage> createState() => _AddPropertyBasicsPageState();
}

class _AddPropertyBasicsPageState extends State<AddPropertyBasicsPage> {
  final GlobalKey _accommodationFieldKey = GlobalKey();
  final GlobalKey _typeFieldKey = GlobalKey();
  final GlobalKey _titleFieldKey = GlobalKey();
  final GlobalKey _governorateFieldKey = GlobalKey();
  final GlobalKey _cityFieldKey = GlobalKey();
  final GlobalKey _streetFieldKey = GlobalKey();
  final GlobalKey _bedroomsFieldKey = GlobalKey();
  final GlobalKey _bathroomsFieldKey = GlobalKey();
  final GlobalKey _spaceFieldKey = GlobalKey();
  final GlobalKey _floorFieldKey = GlobalKey();
  final GlobalKey _locationFieldKey = GlobalKey();

  List<FirstValidationErrorField> _validationFields() => [
    if (widget.form.isPartialOffering)
      FirstValidationErrorField(
        fieldKey: _accommodationFieldKey,
        title: LocaleKeys.rentalOfferedAccommodation,
        value: null,
        validator: (_) => widget.form.isAccommodationReady
            ? null
            : LocaleKeys.rentalAccommodationRequired,
      ),
    FirstValidationErrorField(
      fieldKey: _typeFieldKey,
      title: LocaleKeys.ownerAddPropertyType,
      value: widget.form.propertyTypeApiValue,
      validator: Validators.validateRequired,
    ),
    FirstValidationErrorField(
      fieldKey: _titleFieldKey,
      title: LocaleKeys.ownerAddPropertyTitleLabel,
      value: widget.titleController.text,
      validator: Validators.validateRequired,
    ),
    FirstValidationErrorField(
      fieldKey: _governorateFieldKey,
      title: LocaleKeys.ownerAddPropertyGovernorate,
      value: widget.selectedGovernorate?.id,
      validator: Validators.validateRequired,
    ),
    FirstValidationErrorField(
      fieldKey: _cityFieldKey,
      title: LocaleKeys.ownerAddPropertyCity,
      value: widget.selectedCity?.id,
      validator: Validators.validateRequired,
    ),
    FirstValidationErrorField(
      fieldKey: _streetFieldKey,
      title: LocaleKeys.propertyDistrict,
      value: widget.streetController.text,
      validator: Validators.validateRequired,
    ),
    if (!widget.form.isPartialOffering) ...[
      FirstValidationErrorField(
        fieldKey: _bedroomsFieldKey,
        title: LocaleKeys.ownerAddPropertyBedrooms,
        value: widget.bedroomsController.text,
        validator: PropertyFormValidation.positiveInteger,
      ),
      FirstValidationErrorField(
        fieldKey: _bathroomsFieldKey,
        title: LocaleKeys.ownerAddPropertyBathrooms,
        value: widget.bathroomsController.text,
        validator: PropertyFormValidation.positiveInteger,
      ),
      FirstValidationErrorField(
        fieldKey: _spaceFieldKey,
        title: LocaleKeys.ownerAddPropertySpace,
        value: widget.spaceController.text,
        validator: PropertyFormValidation.positiveInteger,
      ),
    ],
    FirstValidationErrorField(
      fieldKey: _floorFieldKey,
      title: LocaleKeys.ownerAddPropertyFloor,
      value: widget.floorController.text,
      validator: PropertyFormValidation.floor,
    ),
    FirstValidationErrorField(
      fieldKey: _locationFieldKey,
      title: LocaleKeys.ownerAddPropertyMapTitle,
      value: null,
      validator: (_) => widget.form.isLocationSelected
          ? null
          : LocaleKeys.ownerAddPropertySelectLocation,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return AddPropertyStepShell(
      validationFields: _validationFields,
      activeSegments: 1,
      segmentCount: 3,
      progressSubtitle: widget.form.rentalInventory == null
          ? LocaleKeys.ownerAddPropertyBasicsProgress
          : LocaleKeys.rentalFormDetailsProgress,
      primaryLabel: LocaleKeys.ownerAddPropertyNextPhotos,
      onPrimaryTap: widget.onNext,
      children: [
        if (widget.rentalScopeSelector != null) widget.rentalScopeSelector!,
        if (widget.form.isPartialOffering && widget.onFormChanged != null)
          PropertySelectionField(
            key: _accommodationFieldKey,
            isValid: widget.form.isAccommodationReady,
            message: LocaleKeys.rentalAccommodationRequired,
            child: RentalInventoryEditor(
              inventory: widget.form.rentalInventory!,
              selectedOfferRef: widget.form.selectedOfferRef,
              photos: widget.form.photoDrafts,
              totalRooms: int.tryParse(widget.form.bedrooms),
              onChanged: (inventory) => widget.onFormChanged!(
                widget.form.copyWith(rentalInventory: inventory),
              ),
              onOfferSelected: (ref) => widget.onFormChanged!(
                widget.form.copyWith(selectedOfferRef: ref),
              ),
              onAddOffer: (scope) => widget.onFormChanged!(
                OwnerAccommodationDraftData.addIndependentOffer(
                  widget.form,
                  scope,
                ),
              ),
            ),
          ),
        AppText(
          widget.form.isPartialOffering
              ? LocaleKeys.rentalPropertyContext
              : LocaleKeys.rentalPropertyDetails,
          fontWeight: FontWeight.bold,
        ),
        if (widget.form.isPartialOffering)
          AppText(LocaleKeys.rentalSupportingPropertyHelp),
        if (widget.form.isPartialOffering &&
            widget.form.rentalInventory!.offers.length > 1)
          AppText(LocaleKeys.rentalSharedEditHelp),
        AddPropertySectionCard(
          title: '${LocaleKeys.ownerAddPropertyType} *',
          child: PropertySelectionField(
            key: _typeFieldKey,
            isValid: widget.form.propertyTypeApiValue.isNotEmpty,
            child: AddPropertyTypeSelector(
              selectedValue: widget.form.propertyTypeApiValue,
              onSelected: widget.onPropertyTypeSelected,
            ),
          ),
        ),
        AddPropertySectionCard(
          title: widget.form.isPartialOffering
              ? LocaleKeys.rentalParentPropertyName
              : LocaleKeys.ownerAddPropertyNameSection,
          child: AddPropertyField(
            key: _titleFieldKey,
            field: AddPropertyFieldContent(
              label: widget.form.isPartialOffering
                  ? LocaleKeys.rentalParentPropertyName
                  : LocaleKeys.ownerAddPropertyTitleLabel,
              value: LocaleKeys.ownerAddPropertyTitleExample,
            ),
            controller: widget.titleController,
            onChanged: widget.onTitleChanged,
            hint: LocaleKeys.ownerAddPropertyTitleHint,
          ),
        ),
        AddPropertyAddressSection(
          governorateFieldKey: _governorateFieldKey,
          cityFieldKey: _cityFieldKey,
          streetFieldKey: _streetFieldKey,
          streetController: widget.streetController,
          selectedGovernorate: widget.selectedGovernorate,
          selectedCity: widget.selectedCity,
          dropdownGeneration: widget.locationDropdownGeneration,
          onGovernorateChanged: widget.onGovernorateChanged,
          onCityChanged: widget.onCityChanged,
          onStreetChanged: widget.onStreetChanged,
        ),
        if (!widget.form.isPartialOffering)
          AddPropertyDetailsSection(
            bedroomsFieldKey: _bedroomsFieldKey,
            bathroomsFieldKey: _bathroomsFieldKey,
            spaceFieldKey: _spaceFieldKey,
            floorFieldKey: _floorFieldKey,
            bedroomsController: widget.bedroomsController,
            bathroomsController: widget.bathroomsController,
            spaceController: widget.spaceController,
            floorController: widget.floorController,
            onBedroomsChanged: widget.onBedroomsChanged,
            onBathroomsChanged: widget.onBathroomsChanged,
            onSpaceChanged: widget.onSpaceChanged,
            onFloorChanged: widget.onFloorChanged,
          ),
        if (widget.form.isPartialOffering)
          AddPropertySectionCard(
            title: LocaleKeys.ownerAddPropertyFloor,
            child: AddPropertyField(
              key: _floorFieldKey,
              field: AddPropertyFieldContent(
                label: LocaleKeys.ownerAddPropertyFloor,
                value: '',
              ),
              controller: widget.floorController,
              onChanged: widget.onFloorChanged,
              isRequired: false,
              validator: PropertyFormValidation.floor,
              hint: LocaleKeys.ownerAddPropertyFloorHint,
              keyboardType: const TextInputType.numberWithOptions(signed: true),
              inputFormatters: [
                const LocalizedDigitsFormatter(allowNegative: true),
              ],
            ),
          ),
        if (widget.form.isPartialOffering && widget.onFormChanged != null)
          RentalPropertySpecifications(
            form: widget.form,
            onChanged: widget.onFormChanged!,
          ),
        if (widget.form.rentalInventory != null && widget.onFormChanged != null)
          RentalPropertyFacilities(
            form: widget.form,
            onChanged: widget.onFormChanged!,
          ),
        if (!widget.form.isPartialOffering &&
            widget.form.rentalInventory != null &&
            widget.onFormChanged != null)
          AddPropertySectionCard(
            title: LocaleKeys.ownerAddPropertyDescription,
            child: RentalDraftField(
              fieldId: 'property:description',
              validator: PropertyFormValidation.description,
              label: LocaleKeys.ownerAddPropertyDescriptionLabel,
              value: widget.form.description,
              multiline: true,
              onChanged: (value) => widget.onFormChanged!(
                widget.form.copyWith(description: value),
              ),
            ),
          ),
        if (widget.form.isPartialOffering && widget.onFormChanged != null)
          ExpansionTile(
            title: AppText(LocaleKeys.ownerAddPropertyAdditionalDetails),
            children: [
              AddPropertyAdditionalDetails(
                form: widget.form,
                onDetailsChanged: widget.onFormChanged!,
              ),
            ],
          ),
        PropertySelectionField(
          key: _locationFieldKey,
          isValid: widget.form.isLocationSelected,
          message: LocaleKeys.ownerAddPropertySelectLocation,
          child: AddPropertyMapSection(
            location: widget.form.location,
            query: '${widget.form.street}, ${widget.form.locationSummary}',
            onLocationSelected: widget.onLocationSelected,
          ),
        ),
      ],
    );
  }
}
