import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/localized_digits_formatter.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import '../../../data/models/owner_add_property_content.dart';
import 'add_property_section_card.dart';
import 'add_property_field.dart';
import 'property_form_validation.dart';

class AddPropertyDetailsSection extends StatelessWidget {
  const AddPropertyDetailsSection({
    super.key,
    required this.bedroomsController,
    required this.bathroomsController,
    required this.spaceController,
    required this.floorController,
    required this.onBedroomsChanged,
    required this.onBathroomsChanged,
    required this.onSpaceChanged,
    required this.onFloorChanged,
    this.bedroomsFieldKey,
    this.bathroomsFieldKey,
    this.spaceFieldKey,
    this.floorFieldKey,
  });

  final TextEditingController bedroomsController;
  final TextEditingController bathroomsController;
  final TextEditingController spaceController;
  final TextEditingController floorController;
  final ValueChanged<String> onBedroomsChanged;
  final ValueChanged<String> onBathroomsChanged;
  final ValueChanged<String> onSpaceChanged;
  final ValueChanged<String> onFloorChanged;
  final GlobalKey? bedroomsFieldKey;
  final GlobalKey? bathroomsFieldKey;
  final GlobalKey? spaceFieldKey;
  final GlobalKey? floorFieldKey;

  @override
  Widget build(BuildContext context) {
    final fields = [
      _NumberFieldConfig(
        fieldKey: bedroomsFieldKey,
        label: LocaleKeys.ownerAddPropertyBedrooms,
        controller: bedroomsController,
        onChanged: onBedroomsChanged,
      ),
      _NumberFieldConfig(
        fieldKey: bathroomsFieldKey,
        label: LocaleKeys.ownerAddPropertyBathrooms,
        controller: bathroomsController,
        onChanged: onBathroomsChanged,
      ),
      _NumberFieldConfig(
        fieldKey: spaceFieldKey,
        label: LocaleKeys.ownerAddPropertySpace,
        controller: spaceController,
        onChanged: onSpaceChanged,
      ),
      _NumberFieldConfig(
        fieldKey: floorFieldKey,
        label: LocaleKeys.ownerAddPropertyFloor,
        controller: floorController,
        onChanged: onFloorChanged,
      ),
    ];

    return AddPropertySectionCard(
      title: LocaleKeys.ownerAddPropertyDetails,
      child: SokounAdaptiveGrid(
        minimumWidth: 160,
        children: [
          for (final field in fields)
            AddPropertyField(
              key: field.fieldKey,
              isRequired: field.controller != floorController,
              hint: field.controller == floorController
                  ? LocaleKeys.ownerAddPropertyFloorHint
                  : null,
              field: AddPropertyFieldContent(
                label: field.label,
                value: '0',
                textAlign: TextAlign.center,
              ),
              validator: field.controller == floorController
                  ? PropertyFormValidation.floor
                  : PropertyFormValidation.positiveInteger,
              controller: field.controller,
              onChanged: field.onChanged,
              keyboardType: TextInputType.numberWithOptions(
                signed: field.controller == floorController,
              ),
              inputFormatters: [
                LocalizedDigitsFormatter(
                  allowNegative: field.controller == floorController,
                ),
              ],
            ),
        ],
      ),
    );
  }
}

class _NumberFieldConfig {
  const _NumberFieldConfig({
    required this.label,
    required this.controller,
    required this.onChanged,
    this.fieldKey,
  });

  final String label;
  final TextEditingController controller;
  final ValueChanged<String> onChanged;
  final GlobalKey? fieldKey;
}
