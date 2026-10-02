import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/localized_digits_formatter.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import '../../../data/models/owner_add_property_content.dart';
import 'add_property_section_card.dart';
import 'add_property_field.dart';

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
  });

  final TextEditingController bedroomsController;
  final TextEditingController bathroomsController;
  final TextEditingController spaceController;
  final TextEditingController floorController;
  final ValueChanged<String> onBedroomsChanged;
  final ValueChanged<String> onBathroomsChanged;
  final ValueChanged<String> onSpaceChanged;
  final ValueChanged<String> onFloorChanged;

  @override
  Widget build(BuildContext context) {
    final fields = [
      _NumberFieldConfig(
        label: LocaleKeys.ownerAddPropertyBedrooms,
        controller: bedroomsController,
        onChanged: onBedroomsChanged,
      ),
      _NumberFieldConfig(
        label: LocaleKeys.ownerAddPropertyBathrooms,
        controller: bathroomsController,
        onChanged: onBathroomsChanged,
      ),
      _NumberFieldConfig(
        label: LocaleKeys.ownerAddPropertySpace,
        controller: spaceController,
        onChanged: onSpaceChanged,
      ),
      _NumberFieldConfig(
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
              field: AddPropertyFieldContent(
                label: field.label,
                value: '0',
                textAlign: TextAlign.center,
              ),
              controller: field.controller,
              onChanged: field.onChanged,
              keyboardType: TextInputType.number,
              inputFormatters: [const LocalizedDigitsFormatter()],
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
  });

  final String label;
  final TextEditingController controller;
  final ValueChanged<String> onChanged;
}
