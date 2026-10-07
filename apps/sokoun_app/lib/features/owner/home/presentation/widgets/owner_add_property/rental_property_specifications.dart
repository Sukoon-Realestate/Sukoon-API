import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../../../data/models/owner_add_property_content.dart';
import 'rental_terms_fields.dart';

/// Optional parent facts remain editable, particularly when a known physical
/// room total conflicts with newly defined rooms. They are never unit facts.
class RentalPropertySpecifications extends StatelessWidget {
  const RentalPropertySpecifications({
    super.key,
    required this.form,
    required this.onChanged,
  });
  final OwnerAddPropertyFormState form;
  final ValueChanged<OwnerAddPropertyFormState> onChanged;
  @override
  Widget build(BuildContext context) => ExpansionTile(
    title: AppText(LocaleKeys.rentalPropertyDetails),
    subtitle: AppText(LocaleKeys.rentalSupportingPropertyHelp),
    children: [
      Column(
        spacing: 12,
        children: [
          RentalDraftField(
            fieldId: 'property:bedrooms',
            label: LocaleKeys.rentalPropertyRooms,
            value: form.bedrooms,
            numeric: true,
            integer: true,
            onChanged: (value) => onChanged(form.copyWith(bedrooms: value)),
          ),
          RentalDraftField(
            fieldId: 'property:bathrooms',
            label: LocaleKeys.rentalParentPropertyBathrooms,
            value: form.bathrooms,
            numeric: true,
            integer: true,
            onChanged: (value) => onChanged(form.copyWith(bathrooms: value)),
          ),
          RentalDraftField(
            fieldId: 'property:area',
            label: LocaleKeys.rentalParentPropertyArea,
            value: form.space,
            numeric: true,
            integer: true,
            onChanged: (value) => onChanged(form.copyWith(space: value)),
          ),
        ],
      ),
    ],
  );
}
