import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_scope.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_inventory.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_offer.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_room.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_draft_editing.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import '../../../data/owner_accommodation_draft_data.dart';
import '../../../data/models/owner_add_property_content.dart';
import 'add_property_section_card.dart';
import 'rental_terms_fields.dart';
import 'rental_room_fields.dart';
import 'rental_bed_fields.dart';

/// Accommodation first. Terms and property context are composed by their own
/// sections instead of burying this editor inside the pricing page.
class RentalInventoryEditor extends StatelessWidget {
  const RentalInventoryEditor({
    super.key,
    required this.inventory,
    this.totalRooms,
    required this.photos,
    required this.onChanged,
    this.selectedOfferRef = '',
    this.onOfferSelected,
    this.onAddOffer,
  });
  final RentalInventory inventory;
  final int? totalRooms;
  final List<OwnerPropertyPhotoDraft> photos;
  final ValueChanged<RentalInventory> onChanged;
  final String selectedOfferRef;
  final ValueChanged<String>? onOfferSelected;
  final ValueChanged<RentalScope>? onAddOffer;

  RentalOffer? get _selected => selectedOfferRef.isEmpty
      ? inventory.offers.firstOrNull
      : inventory.offers
            .where((offer) => offer.reference == selectedOfferRef)
            .firstOrNull;
  void _offer(RentalOffer offer) =>
      onChanged(OwnerAccommodationDraftData.replaceOffer(inventory, offer));
  void _room(RentalRoom room) =>
      onChanged(OwnerAccommodationDraftData.replaceRoom(inventory, room));

  @override
  Widget build(BuildContext context) {
    final offer = _selected;
    final scope = offer?.scope;
    final rooms = offer == null
        ? <RentalRoom>[]
        : [
            for (final ref in offer.roomRefs)
              if (inventory.roomByRef(ref) case final room?) room,
          ];
    final bed = scope == RentalScope.bed && rooms.length == 1
        ? rooms.single.beds
              .where((bed) => bed.reference == offer!.bedRef)
              .firstOrNull
        : null;
    final locked = offer?.id.isNotEmpty == true;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 16,
      children: [
        if (inventory.offers.length > 1 || offer == null)
          AddPropertySectionCard(
            title: LocaleKeys.rentalEditAccommodation,
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final item in inventory.offers)
                  ChoiceChip(
                    label: AppText(
                      RentalOfferLabels.accommodation(
                        RentalSelection.fromOffer(
                          propertyId: '',
                          inventory: inventory,
                          offer: item,
                        ),
                      ),
                    ),
                    selected: item.reference == offer?.reference,
                    onSelected: (_) => onOfferSelected?.call(item.reference),
                  ),
              ],
            ),
          ),
        if (offer == null || scope == null)
          AppText(LocaleKeys.rentalChooseAccommodationToEdit)
        else ...[
          AddPropertySectionCard(
            title: RentalOfferLabels.detailsHeading(scope),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              spacing: 12,
              children: [
                AppText(scope.priceBasis),
                RentalDraftField(
                  fieldId: '${offer.reference}:name',
                  label: LocaleKeys.rentalAccommodationTitle,
                  value: offer.name,
                  onChanged: (v) => _offer(offer.copyWith(name: v)),
                ),
                if (offer.inheritedFields.contains('description'))
                  CheckboxListTile(
                    contentPadding: EdgeInsets.zero,
                    title: AppText(
                      '${LocaleKeys.rentalOfferDescription} · ${LocaleKeys.rentalInherited}',
                    ),
                    value: true,
                    onChanged: (_) => _offer(
                      offer.copyWith(
                        inheritedFields: {...offer.inheritedFields}
                          ..remove('description'),
                        terms: offer.terms.copyWith(
                          description: inventory
                              .resolved(offer)
                              .terms
                              .description,
                        ),
                      ),
                    ),
                  ),
                RentalDraftField(
                  fieldId: '${offer.reference}:description',
                  label: scope == RentalScope.roomGroup
                      ? LocaleKeys.rentalGroupDescription
                      : LocaleKeys.rentalOfferDescription,
                  validator: (value) => (value?.trim().length ?? 0) >= 10
                      ? null
                      : LocaleKeys.propertyDescriptionMinimum,
                  value: inventory.resolved(offer).terms.description,
                  multiline: true,
                  onChanged: (v) => _offer(
                    offer.copyWith(
                      terms: offer.terms.copyWith(description: v),
                      inheritedFields: {...offer.inheritedFields}
                        ..remove('description'),
                    ),
                  ),
                ),
                if (scope != RentalScope.entireProperty) ...[
                  AppText(
                    scope == RentalScope.bed
                        ? LocaleKeys.rentalSelectSharedRoom
                        : scope == RentalScope.roomGroup
                        ? LocaleKeys.rentalSelectGroupRooms
                        : LocaleKeys.rentalSelectRoom,
                  ),
                  if (scope == RentalScope.roomGroup) ...[
                    AppText(LocaleKeys.rentalGroupSelectionHelp),
                    RentalDraftField(
                      fieldId: '${offer.reference}:group-facilities',
                      label: LocaleKeys.rentalGroupFacilities,
                      value: offer.draftDetails.groupFacilities.join('\n'),
                      multiline: true,
                      onChanged: (v) => _offer(
                        offer.copyWith(
                          draftDetails: offer.draftDetails.copyWith(
                            groupFacilities: OwnerAccommodationDraftData.lines(
                              v,
                            ),
                          ),
                        ),
                      ),
                    ),
                    AppText(
                      LocaleKeys.rentalIncludedRooms.replaceAll(
                        '{count}',
                        '${rooms.length}',
                      ),
                    ),
                    if (rooms.any((room) => room.name.isNotEmpty))
                      AppText(
                        LocaleKeys.rentalGroupIncludedNames.replaceAll(
                          '{rooms}',
                          rooms
                              .map((r) => r.name)
                              .where((name) => name.isNotEmpty)
                              .join(' · '),
                        ),
                      ),
                  ],
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (final room in inventory.rooms)
                        FilterChip(
                          label: AppText(
                            room.name.isEmpty
                                ? LocaleKeys.rentalDefineNewRoom
                                : room.name,
                          ),
                          selected: offer.roomRefs.contains(room.reference),
                          onSelected: locked
                              ? null
                              : (selected) => _offer(
                                  RentalDraftEditing.selectRoom(
                                    offer,
                                    roomRef: room.reference,
                                    selected: selected,
                                  ),
                                ),
                        ),
                    ],
                  ),
                  if (!locked)
                    OutlinedButton.icon(
                      icon: const Icon(Icons.add),
                      label: AppText(LocaleKeys.rentalDefineNewRoom),
                      onPressed: () => onChanged(
                        OwnerAccommodationDraftData.addRoom(inventory, offer),
                      ),
                    ),
                  if (scope == RentalScope.bed && rooms.length == 1) ...[
                    AppText(LocaleKeys.rentalChooseBed),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        for (final item in rooms.single.beds)
                          ChoiceChip(
                            label: AppText(
                              item.name.isEmpty
                                  ? LocaleKeys.rentalBedName
                                  : item.name,
                            ),
                            selected: offer.bedRef == item.reference,
                            onSelected: locked
                                ? null
                                : (_) => _offer(
                                    offer.copyWith(
                                      bedRef: item.reference,
                                      mediaIds: const [],
                                    ),
                                  ),
                          ),
                      ],
                    ),
                    if (!locked)
                      OutlinedButton.icon(
                        icon: const Icon(Icons.add),
                        label: AppText(LocaleKeys.rentalAddBed),
                        onPressed: () {
                          final newBed = RentalBed(
                            draftKey: RentalDraftEditing.key(),
                          );
                          final updated =
                              OwnerAccommodationDraftData.replaceRoom(
                                inventory,
                                rooms.single.copyWith(
                                  beds: [...rooms.single.beds, newBed],
                                ),
                              );
                          onChanged(
                            OwnerAccommodationDraftData.replaceOffer(
                              updated,
                              offer.copyWith(bedRef: newBed.reference),
                            ),
                          );
                        },
                      ),
                  ],
                ],
              ],
            ),
          ),
          if (bed != null)
            RentalBedFields(
              key: ValueKey(bed.reference),
              bed: bed,
              onChanged: (changed) => _room(
                rooms.single.copyWith(
                  beds: [
                    for (final item in rooms.single.beds)
                      item.reference == changed.reference ? changed : item,
                  ],
                ),
              ),
            ),
          for (final room in rooms)
            RentalRoomFields(
              key: ValueKey(room.reference),
              room: room,
              sharedRoom: scope == RentalScope.bed,
              onChanged: _room,
              onRemove: scope == RentalScope.roomGroup && !locked
                  ? () => _offer(
                      RentalDraftEditing.selectRoom(
                        offer,
                        roomRef: room.reference,
                        selected: false,
                      ),
                    )
                  : null,
            ),
          if (scope == RentalScope.roomGroup)
            AppText(
              rooms.length >= 2 &&
                      rooms.every((room) => room.draftDetails.knownArea != null)
                  ? '${LocaleKeys.rentalGroupCombinedArea}: ${rooms.fold<num>(0, (sum, room) => sum + room.draftDetails.knownArea!)}'
                  : LocaleKeys.rentalGroupAreaUnknown,
            ),
          if (offer.id.isEmpty && inventory.offers.length > 1)
            TextButton.icon(
              icon: const Icon(Icons.delete_outline),
              label: AppText(LocaleKeys.rentalRemoveDraft),
              onPressed: () {
                final remaining = inventory.offers
                    .where((item) => item.reference != offer.reference)
                    .toList();
                onChanged(inventory.copyWith(offers: remaining));
                onOfferSelected?.call(remaining.first.reference);
              },
            ),
        ],
        if (inventory.isPartial && onAddOffer != null)
          AddPropertySectionCard(
            title: LocaleKeys.rentalAddIndependentOffer,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              spacing: 8,
              children: [
                AppText(LocaleKeys.rentalIndependentOfferHelp),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final type in RentalScope.values.where(
                      (scope) => scope != RentalScope.entireProperty,
                    ))
                      OutlinedButton.icon(
                        icon: const Icon(Icons.add),
                        label: AppText(type.label),
                        onPressed: () => onAddOffer!(type),
                      ),
                  ],
                ),
              ],
            ),
          ),
        AppText(LocaleKeys.rentalDraftDetailsHelp),
      ],
    );
  }
}
