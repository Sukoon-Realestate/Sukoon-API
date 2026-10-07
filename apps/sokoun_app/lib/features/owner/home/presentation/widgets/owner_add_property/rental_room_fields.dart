import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_room.dart';
import '../../../data/owner_accommodation_draft_data.dart';
import 'add_property_section_card.dart';
import 'rental_terms_fields.dart';

/// The same identified room editor is used for a room, each group member, and
/// the shared-room context of a bed. Property area is never used here.
class RentalRoomFields extends StatelessWidget {
  const RentalRoomFields({
    super.key,
    required this.room,
    required this.onChanged,
    this.sharedRoom = false,
    this.onRemove,
  });
  final RentalRoom room;
  final ValueChanged<RentalRoom> onChanged;
  final bool sharedRoom;
  final VoidCallback? onRemove;

  @override
  Widget build(BuildContext context) => AddPropertySectionCard(
    title: sharedRoom
        ? LocaleKeys.rentalSharedRoomDetails
        : room.name.trim().isEmpty
        ? LocaleKeys.rentalRoomDetails
        : room.name,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 12,
      children: [
        RentalDraftField(
          fieldId: '${room.reference}:name',
          label: '${LocaleKeys.rentalRoomName} *',
          value: room.name,
          validator: (v) => v?.trim().isNotEmpty == true
              ? null
              : LocaleKeys.rentalRoomIdentityRequired,
          onChanged: (v) => onChanged(room.copyWith(name: v)),
        ),
        RentalDraftField(
          fieldId: '${room.reference}:area',
          label: LocaleKeys.rentalRoomArea,
          value: room.draftDetails.area,
          numeric: true,
          validator: (_) => room.draftDetails.isValid
              ? null
              : LocaleKeys.rentalRoomAreaInvalid,
          onChanged: (v) => onChanged(
            room.copyWith(draftDetails: room.draftDetails.copyWith(area: v)),
          ),
        ),
        RentalDraftField(
          fieldId: '${room.reference}:capacity',
          label:
              '${sharedRoom ? LocaleKeys.rentalParentRoomCapacity : LocaleKeys.rentalRoomCapacity} *',
          value: room.capacity > 0 ? '${room.capacity}' : '',
          numeric: true,
          integer: true,
          helperText: LocaleKeys.rentalCapacityHelp,
          validator: (_) => room.capacity >= (sharedRoom ? 2 : 1)
              ? null
              : sharedRoom
              ? LocaleKeys.rentalSharedRoomCapacityInvalid
              : LocaleKeys.rentalRoomCapacityInvalid,
          onChanged: (v) =>
              onChanged(room.copyWith(capacity: int.tryParse(v) ?? 0)),
        ),
        AppText(LocaleKeys.rentalRoomFurnishing),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final furnished in [true, false, null])
              ChoiceChip(
                label: AppText(
                  furnished == true
                      ? LocaleKeys.ownerAddPropertyFurnished
                      : furnished == false
                      ? LocaleKeys.rentalUnfurnished
                      : LocaleKeys.rentalUnspecified,
                ),
                selected: room.draftDetails.furnished == furnished,
                onSelected: (_) => onChanged(
                  room.copyWith(
                    draftDetails: room.draftDetails.copyWith(
                      furnished: furnished,
                      clearFurnished: furnished == null,
                    ),
                  ),
                ),
              ),
          ],
        ),
        RentalDraftField(
          fieldId: '${room.reference}:contents',
          label: LocaleKeys.rentalRoomContents,
          value: room.draftDetails.contents.join('\n'),
          multiline: true,
          helperText: LocaleKeys.rentalOneItemPerLine,
          onChanged: (v) => onChanged(
            room.copyWith(
              draftDetails: room.draftDetails.copyWith(
                contents: OwnerAccommodationDraftData.lines(v),
              ),
            ),
          ),
        ),
        AppText(LocaleKeys.rentalBathroomAccess),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final entry in {
              'private': LocaleKeys.rentalPrivateBathroom,
              'shared': LocaleKeys.rentalSharedBathroom,
              '': LocaleKeys.rentalUnspecified,
            }.entries)
              ChoiceChip(
                label: AppText(entry.value),
                selected: room.bathroomAccess == entry.key,
                onSelected: (_) =>
                    onChanged(room.copyWith(bathroomAccess: entry.key)),
              ),
          ],
        ),
        RentalDraftField(
          fieldId: '${room.reference}:features',
          label: LocaleKeys.rentalRoomFeatures,
          value: room.draftDetails.features.join('\n'),
          multiline: true,
          helperText: LocaleKeys.rentalOneItemPerLine,
          onChanged: (v) => onChanged(
            room.copyWith(
              draftDetails: room.draftDetails.copyWith(
                features: OwnerAccommodationDraftData.lines(v),
              ),
            ),
          ),
        ),
        RentalDraftField(
          fieldId: '${room.reference}:description',
          label: LocaleKeys.rentalRoomDescription,
          value: room.description,
          multiline: true,
          onChanged: (v) => onChanged(room.copyWith(description: v)),
        ),
        if (sharedRoom && room.beds.any((bed) => bed.name.trim().isNotEmpty))
          AppText(
            '${LocaleKeys.rentalPhysicalBedCount}: ${room.beds.where((bed) => bed.name.trim().isNotEmpty).length}',
          ),
        if (onRemove != null)
          TextButton.icon(
            onPressed: onRemove,
            icon: const Icon(Icons.remove_circle_outline),
            label: AppText(LocaleKeys.ownerPropertiesDelete),
          ),
      ],
    ),
  );
}
