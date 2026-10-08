import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_scope.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import '../../../data/owner_accommodation_draft_data.dart';
import '../../../data/models/owner_add_property_content.dart';
import 'add_property_section_card.dart';
import 'property_photo_tile.dart';

class RentalAccommodationMediaSection extends StatelessWidget {
  const RentalAccommodationMediaSection({
    super.key,
    required this.form,
    required this.onChanged,
  });
  final OwnerAddPropertyFormState form;
  final ValueChanged<OwnerAddPropertyFormState> onChanged;

  @override
  Widget build(BuildContext context) {
    final inventory = form.rentalInventory;
    final offer = form.selectedOffer;
    if (inventory == null || offer == null || !inventory.isPartial) {
      return const SizedBox.shrink();
    }
    final rooms = [
      for (final ref in offer.roomRefs)
        if (inventory.roomByRef(ref) case final room?) room,
    ];
    final bed = offer.scope == RentalScope.bed && rooms.length == 1
        ? rooms.single.beds
              .where((bed) => bed.reference == offer.bedRef)
              .firstOrNull
        : null;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 12,
      children: [
        AppText(LocaleKeys.rentalUnitPhotoHelp),
        if (inventory.offers.length > 1)
          Wrap(
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
                  selected: item.reference == offer.reference,
                  onSelected: (_) => onChanged(
                    form.copyWith(selectedOfferRef: item.reference),
                  ),
                ),
            ],
          ),
        if (bed != null)
          _PhotoAssociation(
            title: '${LocaleKeys.rentalBedDetails} · ${bed.name}',
            photos: form.photoDrafts,
            serverIds: bed.mediaIds,
            draftRefs: bed.draftDetails.photoRefs,
            onChanged: (server, local) {
              final changed = bed.copyWith(
                mediaIds: server,
                draftDetails: bed.draftDetails.copyWith(photoRefs: local),
              );
              onChanged(
                form.copyWith(
                  rentalInventory: OwnerAccommodationDraftData.replaceRoom(
                    inventory,
                    rooms.single.copyWith(
                      beds: [
                        for (final item in rooms.single.beds)
                          item.reference == bed.reference ? changed : item,
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        for (final room in rooms)
          _PhotoAssociation(
            key: ValueKey(room.reference),
            title:
                '${offer.scope == RentalScope.bed ? LocaleKeys.rentalSharedRoomDetails : LocaleKeys.rentalRoomDetails} · ${room.name}',
            photos: form.photoDrafts,
            serverIds: room.mediaIds,
            draftRefs: room.draftDetails.photoRefs,
            onChanged: (server, local) => onChanged(
              form.copyWith(
                rentalInventory: OwnerAccommodationDraftData.replaceRoom(
                  inventory,
                  room.copyWith(
                    mediaIds: server,
                    draftDetails: room.draftDetails.copyWith(photoRefs: local),
                  ),
                ),
              ),
            ),
          ),
        _PhotoAssociation(
          title: LocaleKeys.rentalSharedPhotos,
          photos: form.photoDrafts,
          serverIds: inventory.sharedMediaIds,
          draftRefs: inventory.draftDetails.photoRefs,
          onChanged: (server, local) => onChanged(
            form.copyWith(
              rentalInventory: inventory.copyWith(
                sharedMediaIds: server,
                draftDetails: inventory.draftDetails.copyWith(photoRefs: local),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _PhotoAssociation extends StatelessWidget {
  const _PhotoAssociation({
    super.key,
    required this.title,
    required this.photos,
    required this.serverIds,
    required this.draftRefs,
    required this.onChanged,
  });
  final String title;
  final List<OwnerPropertyPhotoDraft> photos;
  final List<String> serverIds, draftRefs;
  final void Function(List<String>, List<String>) onChanged;
  @override
  Widget build(BuildContext context) => AddPropertySectionCard(
    title: title,
    child: Column(
      children: [
        for (final (index, photo) in photos.indexed)
          Material(
            key: ValueKey(photo.reference),
            type: MaterialType.transparency,
            child: CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              title: AppText(
                photo.name.isEmpty
                    ? LocaleKeys.ownerAddPropertyPhotoNumber.replaceAll(
                        '{number}',
                        '${index + 1}',
                      )
                    : photo.name,
              ),
              subtitle: photo.description.isEmpty
                  ? null
                  : AppText(photo.description),
              secondary: SizedBox(
                width: 48,
                height: 48,
                child: PhotoTile(photo: photo),
              ),
              value:
                  (photo.existingId.isNotEmpty &&
                      serverIds.contains(photo.existingId)) ||
                  draftRefs.contains(photo.reference),
              onChanged: (selected) {
                final server = [...serverIds]..remove(photo.existingId);
                final local = [...draftRefs]..remove(photo.reference);
                if (selected == true) {
                  if (RentalOfferCapabilities.configured.canAssociateMedia &&
                      photo.existingId.isNotEmpty) {
                    server.add(photo.existingId);
                  } else {
                    local.add(photo.reference);
                  }
                }
                onChanged(server, local);
              },
            ),
          ),
      ],
    ),
  );
}
