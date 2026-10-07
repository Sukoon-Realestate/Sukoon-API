import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../../../data/models/owner_add_property_content.dart';
import '../../../data/owner_accommodation_draft_data.dart';
import 'add_property_chip_wrap.dart';
import 'add_property_section_card.dart';
import 'rental_terms_fields.dart';

class RentalPropertyFacilities extends StatelessWidget {
  const RentalPropertyFacilities({
    super.key,
    required this.form,
    required this.onChanged,
  });
  final OwnerAddPropertyFormState form;
  final ValueChanged<OwnerAddPropertyFormState> onChanged;

  @override
  Widget build(BuildContext context) {
    final inventory = form.rentalInventory;
    return AddPropertySectionCard(
      title: form.isPartialOffering
          ? LocaleKeys.rentalSharedSpaces
          : LocaleKeys.rentalPropertyFacilities,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 12,
        children: [
          AddPropertyChipWrap(
            chips: [
              for (final entry in {
                'wifi': LocaleKeys.ownerAddPropertyWifi,
                'furnished': LocaleKeys.ownerAddPropertyFurnished,
                'elevator': LocaleKeys.ownerAddPropertyElevator,
                'garage': LocaleKeys.ownerAddPropertyGarage,
                'security': LocaleKeys.ownerAddPropertySecurity,
                'balcony': LocaleKeys.ownerAddPropertyBalcony,
                'air_conditioning': LocaleKeys.ownerAddPropertyAirConditioning,
                'natural_gas': LocaleKeys.ownerAddPropertyNaturalGas,
                'near_metro': LocaleKeys.ownerAddPropertyNearMetro,
                'electricity_meter':
                    LocaleKeys.ownerAddPropertyElectricityMeter,
                'water_meter': LocaleKeys.ownerAddPropertyWaterMeter,
              }.entries)
                AddPropertyChipContent(
                  label:
                      form.optionLabels['amenity:${entry.key}'] ?? entry.value,
                  value: entry.key,
                  isSelected: form.amenityApiValues.contains(entry.key),
                ),
              for (final unsupported in form.unsupportedAmenities)
                AddPropertyChipContent(
                  label:
                      form.optionLabels['amenity:$unsupported'] ?? unsupported,
                  value: unsupported,
                  isSelected: true,
                ),
            ],
            onChipTap: (chip) {
              final amenities = {...form.amenityApiValues};
              if (!amenities.remove(chip.selectionValue)) {
                amenities.add(chip.selectionValue);
              }
              onChanged(form.copyWith(amenities: amenities));
            },
          ),
          if (form.isPartialOffering && inventory != null) ...[
            AppText(LocaleKeys.rentalDraftDetailsHelp),
            RentalDraftField(
              fieldId: 'property:shared-facilities',
              label: LocaleKeys.rentalSharedFacilitiesInput,
              value: inventory.draftDetails.facilities.join('\n'),
              multiline: true,
              onChanged: (v) => onChanged(
                form.copyWith(
                  rentalInventory: inventory.copyWith(
                    draftDetails: inventory.draftDetails.copyWith(
                      facilities: OwnerAccommodationDraftData.lines(v),
                    ),
                  ),
                ),
              ),
            ),
            RentalDraftField(
              fieldId: 'property:rules',
              label: LocaleKeys.rentalSharedRulesInput,
              value: inventory.draftDetails.rules.join('\n'),
              multiline: true,
              onChanged: (v) => onChanged(
                form.copyWith(
                  rentalInventory: inventory.copyWith(
                    draftDetails: inventory.draftDetails.copyWith(
                      rules: OwnerAccommodationDraftData.lines(v),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
