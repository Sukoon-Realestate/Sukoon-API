import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../../data/enums/rental_scope.dart';
import '../../data/models/rental_inventory.dart';
import '../../data/models/rental_room.dart';
import '../../data/models/rental_selection.dart';
import 'rental_offer_labels.dart';

/// Only facts of the selected accommodation. Never substitutes parent area,
/// bedroom totals, furnishing or other rooms when unit information is missing.
class RentalAccommodationDetails extends StatelessWidget {
  const RentalAccommodationDetails({
    super.key,
    required this.selection,
    required this.inventory,
    this.showHeading = true,
  });
  final RentalSelection selection;
  final RentalInventory inventory;
  final bool showHeading;

  @override
  Widget build(BuildContext context) {
    final rooms = [
      for (final ref in selection.roomIds)
        if (inventory.roomByRef(ref) case final room?) room,
    ];
    final bed = selection.scope == RentalScope.bed && rooms.length == 1
        ? rooms.single.beds
              .where((bed) => bed.reference == selection.bedId)
              .firstOrNull
        : null;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 12,
      children: [
        if (selection.scope == RentalScope.bed) ...[
          if (showHeading)
            AppText(LocaleKeys.rentalBedDetails, fontWeight: FontWeight.bold),
          if (bed != null) ...[
            AppText(bed.name),
            if (bed.draftDetails.type.isNotEmpty)
              AppText('${LocaleKeys.rentalBedType}: ${bed.draftDetails.type}'),
            if (bed.draftDetails.storage.isNotEmpty)
              AppText(
                '${LocaleKeys.rentalBedStorage}: ${bed.draftDetails.storage}',
              ),
            if (bed.draftDetails.description.isNotEmpty)
              AppText(bed.draftDetails.description),
          ],
          AppText(
            LocaleKeys.rentalSharedRoomDetails,
            fontWeight: FontWeight.bold,
          ),
          AppText(LocaleKeys.rentalCapacityHelp),
        ] else if (selection.scope == RentalScope.roomGroup) ...[
          if (showHeading) ...[
            AppText(
              LocaleKeys.rentalRoomGroupDetails,
              fontWeight: FontWeight.bold,
            ),
            AppText(
              LocaleKeys.rentalIncludedRooms.replaceAll(
                '{count}',
                '${selection.roomIds.length}',
              ),
            ),
            AppText(LocaleKeys.rentalGroupPriceBasis),
          ],
          if (inventory.offers
                  .where(
                    (offer) =>
                        (offer.id == selection.offerId ||
                            offer.reference == selection.offerId) &&
                        offer.roomRefs.length == selection.roomIds.length &&
                        offer.roomRefs.toSet().containsAll(selection.roomIds),
                  )
                  .firstOrNull
              case final offer?)
            if (offer.draftDetails.groupFacilities.isNotEmpty)
              AppText(
                '${LocaleKeys.rentalGroupFacilities}\n${offer.draftDetails.groupFacilities.join(' · ')}',
              ),
          if (rooms.length == selection.roomIds.length &&
              rooms.isNotEmpty &&
              rooms.every((room) => room.draftDetails.knownArea != null))
            AppText(
              '${LocaleKeys.rentalGroupCombinedArea}: ${rooms.fold<num>(0, (sum, room) => sum + room.draftDetails.knownArea!)}',
            ),
        ],
        for (final room in rooms)
          _RoomFacts(
            key: ValueKey(room.reference),
            room: room,
            shared: selection.scope == RentalScope.bed,
          ),
        if (rooms.isEmpty && selection.scope != RentalScope.entireProperty)
          AppText(LocaleKeys.rentalNoAccommodationDetails),
      ],
    );
  }
}

class _RoomFacts extends StatelessWidget {
  const _RoomFacts({super.key, required this.room, required this.shared});
  final RentalRoom room;
  final bool shared;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(
      border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
      borderRadius: BorderRadius.circular(12),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 8,
      children: [
        AppText(
          room.name.isEmpty ? LocaleKeys.rentalUnspecified : room.name,
          fontWeight: FontWeight.bold,
        ),
        if (room.draftDetails.knownArea case final area?)
          AppText('${LocaleKeys.rentalRoomArea}: $area'),
        if (room.capacity > 0)
          AppText(
            '${shared ? LocaleKeys.rentalParentRoomCapacity : LocaleKeys.rentalRoomCapacity}: ${room.capacity}',
          ),
        if (shared && room.beds.any((bed) => bed.name.trim().isNotEmpty))
          AppText(
            '${LocaleKeys.rentalPhysicalBedCount}: ${room.beds.where((bed) => bed.name.trim().isNotEmpty).length}',
          ),
        if (room.draftDetails.furnished != null)
          AppText(
            room.draftDetails.furnished!
                ? LocaleKeys.ownerAddPropertyFurnished
                : LocaleKeys.rentalUnfurnished,
          ),
        if (room.draftDetails.contents.isNotEmpty)
          AppText(
            '${LocaleKeys.rentalRoomContents}\n${room.draftDetails.contents.join(' · ')}',
          ),
        if (room.bathroomAccess.isNotEmpty)
          AppText(
            '${LocaleKeys.rentalBathroomAccess}: ${RentalOfferLabels.bathroom(room.bathroomAccess)}',
          ),
        if (room.draftDetails.features.isNotEmpty)
          AppText(
            '${LocaleKeys.rentalRoomFeatures}\n${room.draftDetails.features.join(' · ')}',
          ),
        if (room.description.isNotEmpty) AppText(room.description),
      ],
    ),
  );
}
