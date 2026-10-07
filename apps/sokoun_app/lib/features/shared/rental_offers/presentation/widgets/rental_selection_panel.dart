import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_tenant_type.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import '../../data/models/rental_selection.dart';
import '../../data/enums/rental_scope.dart';
import 'rental_offer_labels.dart';
import '../../data/models/rental_inventory.dart';
import 'rental_accommodation_details.dart';

/// Uses only the selected offer or a server-supplied historical snapshot.
class RentalSelectionPanel extends StatelessWidget {
  const RentalSelectionPanel({
    super.key,
    required this.selection,
    this.historical = false,
    this.inventory,
  });
  final RentalSelection selection;
  final bool historical;
  final RentalInventory? inventory;

  @override
  Widget build(BuildContext context) => Card(
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(12),
      side: BorderSide(color: Theme.of(context).colorScheme.outlineVariant),
    ),
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 8,
        children: [
          AppText(
            RentalOfferLabels.detailsHeading(selection.scope),
            fontWeight: FontWeight.bold,
          ),
          AppText(RentalOfferLabels.accommodation(selection)),
          if (selection.scope == RentalScope.bed &&
              selection.roomNames.isNotEmpty)
            AppText(
              '${LocaleKeys.rentalParentRoom}: ${selection.roomNames.join(' · ')}',
            )
          else if (selection.roomIds.isNotEmpty)
            AppText(
              LocaleKeys.rentalIncludedRooms.replaceAll(
                '{count}',
                '${selection.roomIds.length}',
              ),
            ),
          AppText(
            RentalOfferLabels.price(selection),
            fontWeight: FontWeight.bold,
          ),
          if (!historical)
            AppText(
              RentalOfferLabels.availability(
                selection.availability,
                archived: selection.archived,
              ),
            ),
          if (selection.terms.minimumMonths > 0)
            AppText(
              '${LocaleKeys.ownerAddPropertyMinimumRentalMonths}: ${selection.terms.minimumMonths}',
            ),
          if (selection.terms.deposit.isNotEmpty)
            AppText(
              '${LocaleKeys.rentalOfferDeposit}: ${PropertyDetailsModel.depositLabelFor(selection.terms.deposit)}',
            ),
          if (inventory != null && !historical)
            RentalAccommodationDetails(
              selection: selection,
              inventory: inventory!,
              showHeading: false,
            ),
          if ((inventory == null || historical) && selection.capacity != null)
            AppText(
              '${switch (selection.scope) {
                RentalScope.bed => LocaleKeys.rentalParentRoomCapacity,
                RentalScope.roomGroup => LocaleKeys.rentalGroupCapacity,
                _ => LocaleKeys.rentalRoomCapacity,
              }}: ${selection.capacity}',
            ),
          if ((inventory == null || historical) &&
              selection.bathroomAccess.isNotEmpty)
            AppText(
              '${LocaleKeys.rentalBathroomAccess}: ${selection.bathroomAccess.map((value) => switch (value) {
                'private' => LocaleKeys.rentalPrivateBathroom,
                'shared' => LocaleKeys.rentalSharedBathroom,
                _ => LocaleKeys.rentalUnspecified,
              }).join(' · ')}',
            ),
          if (selection.terms.suitableFor.isNotEmpty)
            AppText(
              '${LocaleKeys.rentalOfferSuitability}: ${(PropertyTenantType.fromValue(selection.terms.suitableFor)?.label ?? selection.terms.suitableFor)}',
            ),
          if (selection.terms.description.isNotEmpty)
            AppText(selection.terms.description),
          if (selection.terms.smokingAllowed != null)
            AppText(
              selection.terms.smokingAllowed == true
                  ? LocaleKeys.tenantPropertyDetailsSmokingAllowed
                  : LocaleKeys.tenantPropertyDetailsSmokingNotAllowed,
            ),
          if (selection.terms.rules.isNotEmpty)
            AppText(selection.terms.rules.join('\n')),
          if (historical) AppText(LocaleKeys.rentalHistoricalTerms),
        ],
      ),
    ),
  );
}
