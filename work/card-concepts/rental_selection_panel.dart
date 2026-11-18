import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_tenant_type.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/shared_widgets/sokoun_palette.dart';
import '../../data/models/rental_selection.dart';
import '../../data/enums/rental_scope.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_labels.dart';
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
  Widget build(BuildContext context) {
    final palette = SokounPalette.of(context);
    final terms = <Widget>[
      if (selection.terms.minimumMonths > 0)
        _TermRow(
          label: LocaleKeys.ownerAddPropertyMinimumRentalMonths,
          value: '${selection.terms.minimumMonths}',
        ),
      if (selection.terms.deposit.isNotEmpty)
        _TermRow(
          label: LocaleKeys.rentalOfferDeposit,
          value: PropertyDetailsModel.depositLabelFor(selection.terms.deposit),
        ),
      if ((inventory == null || historical) && selection.capacity != null)
        _TermRow(
          label: switch (selection.scope) {
            RentalScope.bed => LocaleKeys.rentalParentRoomCapacity,
            RentalScope.roomGroup => LocaleKeys.rentalGroupCapacity,
            _ => LocaleKeys.rentalRoomCapacity,
          },
          value: '${selection.capacity}',
        ),
      if ((inventory == null || historical) && selection.bathroomAccess.isNotEmpty)
        _TermRow(
          label: LocaleKeys.rentalBathroomAccess,
          value: selection.bathroomAccess.map((value) => switch (value) {
            'private' => LocaleKeys.rentalPrivateBathroom,
            'shared' => LocaleKeys.rentalSharedBathroom,
            _ => LocaleKeys.rentalUnspecified,
          }).join(' · '),
        ),
      if (selection.terms.suitableFor.isNotEmpty)
        _TermRow(
          label: LocaleKeys.rentalOfferSuitability,
          value: PropertyTenantType.fromValue(selection.terms.suitableFor)?.label ?? selection.terms.suitableFor,
        ),
    ];
    final rules = <String>[
      if (selection.terms.smokingAllowed != null)
        selection.terms.smokingAllowed == true
          ? LocaleKeys.tenantPropertyDetailsSmokingAllowed
          : LocaleKeys.tenantPropertyDetailsSmokingNotAllowed,
      ...selection.terms.rules,
    ];
    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: palette.line),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppText(
              RentalOfferLabels.detailsHeading(selection.scope),
              style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            AppText(
              RentalOfferLabels.accommodation(selection),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: palette.muted, height: 1.6),
            ),
            if (selection.scope == RentalScope.bed && selection.roomNames.isNotEmpty) ...[
              const SizedBox(height: 6),
              AppText('${LocaleKeys.rentalParentRoom}: ${selection.roomNames.join(' · ')}'),
            ] else if (selection.roomIds.isNotEmpty) ...[
              const SizedBox(height: 6),
              AppText(LocaleKeys.rentalIncludedRooms.replaceAll('{count}', '${selection.roomIds.length}')),
            ],
            const SizedBox(height: 16),
            AppText(
              RentalOfferLabels.price(selection),
              style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700, height: 1.5),
            ),
            if (!historical) ...[
              const SizedBox(height: 6),
              AppText(
                RentalOfferLabels.availability(selection.availability, archived: selection.archived),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: palette.muted),
              ),
            ],
            if (terms.isNotEmpty) ...[
              const SizedBox(height: 20),
              Divider(height: 1, color: palette.line),
              const SizedBox(height: 16),
              Column(crossAxisAlignment: CrossAxisAlignment.stretch, spacing: 14, children: terms),
            ],
            if (inventory != null && !historical && selection.scope != RentalScope.entireProperty) ...[
              const SizedBox(height: 24),
              RentalAccommodationDetails(selection: selection, inventory: inventory!, showHeading: false),
            ],
            if (selection.terms.description.isNotEmpty)
              _PanelSection(
                title: LocaleKeys.rentalOfferDescription,
                child: AppText(
                  selection.terms.description,
                  textAlign: TextAlign.start,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.85, fontWeight: FontWeight.w400),
                ),
              ),
            if (rules.isNotEmpty)
              _PanelSection(
                title: LocaleKeys.rentalRules,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  spacing: 10,
                  children: [
                    for (final rule in rules)
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Padding(
                            padding: const EdgeInsetsDirectional.only(top: 8, end: 10),
                            child: Icon(Icons.circle, size: 4, color: palette.muted),
                          ),
                          Expanded(child: AppText(rule, style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.7))),
                        ],
                      ),
                  ],
                ),
              ),
            if (historical) ...[
              const SizedBox(height: 20),
              AppText(LocaleKeys.rentalHistoricalTerms, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: palette.muted, height: 1.6)),
            ],
          ],
        ),
      ),
    );
  }
}

class _TermRow extends StatelessWidget {
  const _TermRow({required this.label, required this.value});
  final String label, value;

  @override
  Widget build(BuildContext context) {
    final labelWidget = AppText(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: SokounPalette.of(context).muted, height: 1.6));
    final valueWidget = AppText(value, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w500, height: 1.6));
    return LayoutBuilder(builder: (context, constraints) {
      if (constraints.maxWidth < 270 || MediaQuery.textScalerOf(context).scale(14) > 20) {
        return Column(crossAxisAlignment: CrossAxisAlignment.start, spacing: 4, children: [labelWidget, valueWidget]);
      }
      return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Expanded(flex: 3, child: labelWidget),
        const SizedBox(width: 16),
        Expanded(flex: 2, child: Align(alignment: AlignmentDirectional.centerEnd, child: valueWidget)),
      ]);
    });
  }
}

class _PanelSection extends StatelessWidget {
  const _PanelSection({required this.title, required this.child});
  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 24),
    child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, spacing: 10, children: [
      AppText(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
      child,
    ]),
  );
}
