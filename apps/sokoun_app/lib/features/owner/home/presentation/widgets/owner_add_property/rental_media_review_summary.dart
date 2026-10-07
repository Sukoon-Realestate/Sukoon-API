import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../../../data/models/owner_add_property_content.dart';

/// Names the unit associated with photos without presenting unrelated property
/// photos as pictures of that room or bed.
class RentalMediaReviewSummary extends StatelessWidget {
  const RentalMediaReviewSummary({super.key, required this.form});

  final OwnerAddPropertyFormState form;

  List<String> _photoNames(List<String> serverIds, List<String> localRefs) => [
    for (final (index, photo) in form.photoDrafts.indexed)
      if ((photo.existingId.isNotEmpty &&
              serverIds.contains(photo.existingId)) ||
          localRefs.contains(photo.reference))
        photo.name.trim().isNotEmpty
            ? photo.name
            : LocaleKeys.ownerAddPropertyPhotoNumber.replaceAll(
                '{number}',
                '${index + 1}',
              ),
  ];

  @override
  Widget build(BuildContext context) {
    final inventory = form.submissionInventory;
    if (inventory == null || !inventory.isPartial) {
      return const SizedBox.shrink();
    }
    final includedRooms = inventory.offers
        .expand((offer) => offer.roomRefs)
        .toSet();
    final includedBeds = inventory.offers.map((offer) => offer.bedRef).toSet();
    final groups = <(String, List<String>)>[
      for (final room in inventory.rooms.where(
        (room) => includedRooms.contains(room.reference),
      )) ...[
        (
          '${LocaleKeys.rentalRoomDetails} · ${room.name}',
          _photoNames(room.mediaIds, room.draftDetails.photoRefs),
        ),
        for (final bed in room.beds.where(
          (bed) => includedBeds.contains(bed.reference),
        ))
          (
            '${LocaleKeys.rentalBedDetails} · ${bed.name} · ${room.name}',
            _photoNames(bed.mediaIds, bed.draftDetails.photoRefs),
          ),
      ],
      (
        LocaleKeys.rentalSharedPhotos,
        _photoNames(inventory.sharedMediaIds, inventory.draftDetails.photoRefs),
      ),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 8,
      children: [
        AppText(LocaleKeys.rentalUnitPhotoHelp),
        for (final (title, names) in groups.where(
          (group) => group.$2.isNotEmpty,
        ))
          AppText('$title\n${names.join(' · ')}'),
      ],
    );
  }
}
