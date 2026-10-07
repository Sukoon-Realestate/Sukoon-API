import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_inventory.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import '../../../data/owner_accommodation_draft_data.dart';
import 'add_property_section_card.dart';
import 'rental_terms_fields.dart';

class RentalOfferTermsEditor extends StatelessWidget {
  const RentalOfferTermsEditor({
    super.key,
    required this.inventory,
    required this.onChanged,
  });
  final RentalInventory inventory;
  final ValueChanged<RentalInventory> onChanged;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    spacing: 16,
    children: [
      ExpansionTile(
        title: AppText(LocaleKeys.rentalDefaults),
        children: [
          RentalTermsFields(
            terms: inventory.defaults,
            defaults: true,
            fieldId: 'shared-terms',
            onChanged: (terms) =>
                onChanged(inventory.copyWith(defaults: terms)),
          ),
        ],
      ),
      for (final offer in inventory.offers)
        AddPropertySectionCard(
          key: ValueKey(offer.reference),
          title: RentalOfferLabels.accommodation(
            RentalSelection.fromOffer(
              propertyId: '',
              inventory: inventory,
              offer: offer,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 12,
            children: [
              AppText(
                offer.scope?.priceBasis ?? LocaleKeys.rentalUnknownScope,
                fontWeight: FontWeight.bold,
              ),
              if (offer.roomRefs.isNotEmpty)
                AppText(
                  offer.roomRefs
                      .map(
                        (ref) =>
                            inventory.roomByRef(ref)?.name ??
                            LocaleKeys.rentalUnspecified,
                      )
                      .join(' · '),
                ),
              RentalTermsFields(
                terms: offer.terms,
                fieldId: offer.reference,
                showDescription: false,
                inherited: offer.inheritedFields,
                onChanged: (terms) => onChanged(
                  OwnerAccommodationDraftData.replaceOffer(
                    inventory,
                    offer.copyWith(terms: terms),
                  ),
                ),
                onInheritanceChanged: (fields) => onChanged(
                  OwnerAccommodationDraftData.replaceOffer(
                    inventory,
                    offer.copyWith(inheritedFields: fields),
                  ),
                ),
              ),
              AppText(
                RentalOfferLabels.availability(
                  offer.availability,
                  archived: offer.archived,
                ),
              ),
              if (offer.id.isEmpty)
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final availability in [
                      'available',
                      'unavailable',
                      'rented',
                    ])
                      ChoiceChip(
                        label: AppText(
                          RentalOfferLabels.availability(availability),
                        ),
                        selected: offer.availability == availability,
                        onSelected: (_) => onChanged(
                          OwnerAccommodationDraftData.replaceOffer(
                            inventory,
                            offer.copyWith(availability: availability),
                          ),
                        ),
                      ),
                  ],
                ),
            ],
          ),
        ),
    ],
  );
}
