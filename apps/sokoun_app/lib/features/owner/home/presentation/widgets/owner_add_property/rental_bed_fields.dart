import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_room.dart';
import 'add_property_section_card.dart';
import 'rental_terms_fields.dart';

class RentalBedFields extends StatelessWidget {
  const RentalBedFields({
    super.key,
    required this.bed,
    required this.onChanged,
  });
  final RentalBed bed;
  final ValueChanged<RentalBed> onChanged;

  @override
  Widget build(BuildContext context) => AddPropertySectionCard(
    title: LocaleKeys.rentalBedDetails,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 12,
      children: [
        RentalDraftField(
          fieldId: '${bed.reference}:name',
          label: '${LocaleKeys.rentalBedName} *',
          value: bed.name,
          validator: (v) => v?.trim().isNotEmpty == true
              ? null
              : LocaleKeys.rentalBedNameRequired,
          onChanged: (v) => onChanged(bed.copyWith(name: v)),
        ),
        RentalDraftField(
          fieldId: '${bed.reference}:type',
          label: LocaleKeys.rentalBedType,
          value: bed.draftDetails.type,
          onChanged: (v) => onChanged(
            bed.copyWith(draftDetails: bed.draftDetails.copyWith(type: v)),
          ),
        ),
        RentalDraftField(
          fieldId: '${bed.reference}:storage',
          label: LocaleKeys.rentalBedStorage,
          value: bed.draftDetails.storage,
          onChanged: (v) => onChanged(
            bed.copyWith(draftDetails: bed.draftDetails.copyWith(storage: v)),
          ),
        ),
        RentalDraftField(
          fieldId: '${bed.reference}:description',
          label: LocaleKeys.rentalBedDescription,
          value: bed.draftDetails.description,
          multiline: true,
          onChanged: (v) => onChanged(
            bed.copyWith(
              draftDetails: bed.draftDetails.copyWith(description: v),
            ),
          ),
        ),
      ],
    ),
  );
}
