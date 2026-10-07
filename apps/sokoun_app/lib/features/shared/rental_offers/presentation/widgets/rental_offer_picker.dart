import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import '../../data/models/rental_inventory.dart';
import '../../data/models/rental_selection.dart';
import 'rental_offer_labels.dart';
import 'rental_selection_panel.dart';

class RentalOfferPicker extends StatelessWidget {
  const RentalOfferPicker({
    super.key,
    required this.propertyId,
    required this.inventory,
    required this.selectedId,
    required this.onSelected,
    this.onConfirmed,
    this.confirmedSelection,
    this.contextScope = '',
    this.contextPricePeriod = '',
    this.enabled = true,
  });
  final String propertyId;
  final RentalInventory inventory;
  final String? selectedId;
  final ValueChanged<String> onSelected;
  final ValueChanged<RentalSelection>? onConfirmed;
  final RentalSelection? confirmedSelection;
  final String contextScope, contextPricePeriod;
  final bool enabled;
  @override
  Widget build(BuildContext context) {
    final selected = inventory.offerById(selectedId ?? '');
    final selection = selected == null
        ? null
        : RentalSelection.fromOffer(
            propertyId: propertyId,
            inventory: inventory,
            offer: selected,
          );
    final confirmed =
        selection != null &&
        confirmedSelection != null &&
        selection.sameTermsAs(confirmedSelection!);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 12.h,
      children: [
        AppText(LocaleKeys.rentalChooseOffer, fontWeight: FontWeight.bold),
        if (!inventory.isSupported) AppText(LocaleKeys.rentalUnknownScope),
        if (selectedId != null && selected == null)
          AppText(LocaleKeys.rentalNotAvailable),
        for (final offer in inventory.offers)
          Card(
            key: ValueKey(offer.id.isEmpty ? offer.reference : offer.id),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: BorderSide(
                color: Theme.of(context).colorScheme.outlineVariant,
              ),
            ),
            child: ListTile(
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 8,
              ),
              leading: Icon(
                selectedId == offer.id
                    ? Icons.radio_button_checked
                    : Icons.radio_button_unchecked,
              ),
              title: AppText(
                RentalOfferLabels.accommodation(
                  RentalSelection.fromOffer(
                    propertyId: propertyId,
                    inventory: inventory,
                    offer: offer,
                  ),
                ),
              ),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                spacing: 4,
                children: [
                  if (offer.scopeValue == contextScope &&
                      (contextPricePeriod.isEmpty ||
                          inventory.resolved(offer).terms.pricePeriod ==
                              contextPricePeriod))
                    AppText(LocaleKeys.rentalMatchesDiscovery),
                  AppText(
                    RentalOfferLabels.price(
                      RentalSelection.fromOffer(
                        propertyId: propertyId,
                        inventory: inventory,
                        offer: offer,
                      ),
                    ),
                  ),
                  AppText(
                    RentalOfferLabels.availability(
                      offer.availability,
                      archived: offer.archived,
                    ),
                  ),
                ],
              ),
              onTap:
                  enabled &&
                      inventory.isSupported &&
                      offer.scope != null &&
                      offer.id.isNotEmpty
                  ? () => onSelected(offer.id)
                  : null,
            ),
          ),
        if (!inventory.offers.any((o) => o.isAvailable))
          AppText(LocaleKeys.rentalNoAvailableOffers),
        if (selection != null) ...[
          if (!selection.isAvailable) AppText(LocaleKeys.rentalNotAvailable),
          if (confirmedSelection != null && !confirmed && selection.isAvailable)
            AppText(LocaleKeys.rentalTermsChanged),
          RentalSelectionPanel(selection: selection, inventory: inventory),
          if (onConfirmed != null)
            DefaultButton(
              title: confirmed
                  ? LocaleKeys.rentalAccommodationConfirmed
                  : LocaleKeys.rentalConfirmAccommodation,
              onTap:
                  enabled &&
                      !confirmed &&
                      inventory.isSupported &&
                      selection.canIdentify &&
                      selection.isAvailable &&
                      selection.terms.isValid
                  ? () => onConfirmed!(selection)
                  : null,
              isFitted: false,
              minHeight: 48.h,
            ),
        ],
      ],
    );
  }
}
