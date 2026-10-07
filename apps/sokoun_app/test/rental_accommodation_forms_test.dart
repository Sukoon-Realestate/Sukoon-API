import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_property_draft.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/data/owner_accommodation_draft_data.dart';
import 'package:sokoun_app/features/owner/home/data/owner_add_property_mapper.dart';
import 'package:sokoun_app/features/owner/home/data/owner_draft_data.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_scope.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_accommodation_draft_details.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_inventory.dart';
import 'helpers/rental_offer_fixtures.dart';

void main() {
  for (final scope in RentalScope.values) {
    test(
      '$scope prepares the advertised accommodation and retains shared location',
      () {
        final base = rentalForm(
          rentalInventory(),
        ).copyWith(clearRentalInventory: true);
        final form = OwnerAccommodationDraftData.chooseScope(base, scope);
        expect(form.rentalScope, scope);
        expect(form.propertyTypeApiValue, 'apartment');
        expect(form.location, base.location);
        expect(form.street, base.street);
        expect(form.selectedOfferRef, form.selectedOffer!.reference);
        switch (scope) {
          case RentalScope.entireProperty:
            expect(form.selectedOffer!.roomRefs, isEmpty);
            expect(form.selectedOffer!.bedRef, isEmpty);
          case RentalScope.room:
            expect(form.selectedOffer!.roomRefs, hasLength(1));
            expect(form.rentalInventory!.rooms, hasLength(1));
            expect(form.isAccommodationReady, isFalse);
          case RentalScope.roomGroup:
            expect(form.selectedOffer!.roomRefs.toSet(), hasLength(2));
            expect(form.rentalInventory!.offers, hasLength(1));
            expect(form.isAccommodationReady, isFalse);
          case RentalScope.bed:
            final room = form.rentalInventory!.roomByRef(
              form.selectedOffer!.roomRefs.single,
            )!;
            expect(room.beds.single.reference, form.selectedOffer!.bedRef);
            expect(room.capacity, 0); // No invented capacity/occupancy.
            expect(form.isAccommodationReady, isFalse);
        }
      },
    );
  }
  for (final offer in [independentRooms.first, groupOffer, bedOffer]) {
    test(
      '${offer.scope} needs property context, without requiring property area or bedroom totals',
      () {
        final form = rentalForm(
          rentalInventory(offers: [offer]),
        ).copyWith(bedrooms: '', bathrooms: '', space: '', floor: '3');
        expect(form.isBasicsReady, isTrue);
        expect(form.isPricingReady, isTrue);
        final body = form.toJson(capabilities: offersEnabled);
        expect(body.containsKey('area'), isFalse);
        expect(body.containsKey('bedrooms'), isFalse);
        expect(body.containsKey('bathrooms'), isFalse);
        expect(body['floor'], 3);
        expect(body['property_type'], 'apartment');
        expect(body.containsKey('price'), isFalse);
        final inventory = jsonDecode(body['rental_inventory'] as String) as Map;
        final saved = (inventory['offers'] as List).single as Map;
        expect(saved['rental_scope'], offer.scopeValue);
        expect(
          (saved['term_overrides'] as Map)['price_period'],
          offer.terms.pricePeriod,
        );
        expect(
          (saved['term_overrides'] as Map)['rental_period'],
          offer.terms.minimumMonths,
        );
      },
    );
  }
  test('whole property still requires physical specifications', () {
    final form = rentalForm(
      rentalInventory(offers: [wholeOffer], mode: 'whole'),
    );
    expect(form.isBasicsReady, isTrue);
    expect(form.copyWith(space: '').isBasicsReady, isFalse);
    expect(form.copyWith(bedrooms: '').isBasicsReady, isFalse);
  });
  test(
    'partial scope ignores incompatible hidden count input while preserving it in the draft',
    () {
      final form = rentalForm(
        rentalInventory(),
      ).copyWith(bedrooms: '-1', space: 'invalid', bathrooms: '');
      expect(form.isBasicsReady, isTrue);
      final body = form.toJson(capabilities: offersEnabled);
      expect(body.containsKey('bedrooms'), isFalse);
      expect(body.containsKey('area'), isFalse);
      expect(
        OwnerDraftFormCodec.decode(OwnerDraftFormCodec.encode(form)).space,
        'invalid',
      );
    },
  );
  test(
    'switching bed to room excludes an unused blank bed and preserves its local draft details',
    () {
      var form = OwnerAccommodationDraftData.chooseScope(
        OwnerAddPropertyFormState.initial(),
        RentalScope.bed,
      );
      final room = form.rentalInventory!.rooms.single.copyWith(
        name: 'Window room',
        capacity: 2,
      );
      final localBed = room.beds.single.copyWith(
        draftDetails: const RentalBedDraftDetails(
          type: 'Single',
          storage: 'Locker',
        ),
      );
      form = form.copyWith(
        rentalInventory: form.rentalInventory!.copyWith(
          rooms: [
            room.copyWith(beds: [localBed]),
          ],
        ),
      );
      final changed = OwnerAccommodationDraftData.chooseScope(
        form,
        RentalScope.room,
      );
      expect(changed.selectedOffer!.bedRef, isEmpty);
      expect(changed.isAccommodationReady, isTrue);
      expect(changed.submissionInventory!.rooms.single.beds, isEmpty);
      expect(
        changed.rentalInventory!.rooms.single.beds.single.draftDetails.storage,
        'Locker',
      );
      final request = changed.submissionInventory!.toRequestJson();
      expect((request['offers'] as List).single.containsKey('bed_id'), isFalse);
    },
  );
  test('inactive local room fields cannot block a whole-property offer', () {
    final partial = OwnerAccommodationDraftData.chooseScope(
      OwnerAddPropertyFormState.initial(),
      RentalScope.roomGroup,
    );
    final whole = OwnerAccommodationDraftData.chooseScope(
      partial,
      RentalScope.entireProperty,
    );
    expect(whole.isAccommodationReady, isTrue);
    expect(whole.submissionInventory!.rooms, isEmpty);
    expect(whole.rentalInventory!.rooms, hasLength(2));
    expect(
      whole.rentalInventory!.parkedOffers.single.scope,
      RentalScope.roomGroup,
    );
  });
  test('independent offers remain distinct from a room group', () {
    final room = OwnerAccommodationDraftData.chooseScope(
      OwnerAddPropertyFormState.initial(),
      RentalScope.room,
    );
    final independent = OwnerAccommodationDraftData.addIndependentOffer(
      room,
      RentalScope.room,
    );
    expect(independent.rentalInventory!.offers, hasLength(2));
    expect(
      independent.rentalInventory!.offers.every(
        (offer) =>
            offer.scope == RentalScope.room && offer.roomRefs.length == 1,
      ),
      isTrue,
    );
    expect(
      independent.rentalInventory!.offers.expand((o) => o.roomRefs).toSet(),
      hasLength(2),
    );
    final group = OwnerAccommodationDraftData.chooseScope(
      OwnerAddPropertyFormState.initial(),
      RentalScope.roomGroup,
    );
    expect(group.rentalInventory!.offers.single.scope, RentalScope.roomGroup);
    expect(group.rentalInventory!.offers.single.roomRefs, hasLength(2));
  });
  test(
    'local room area, contents, bed provisions and group facilities round trip without entering API JSON',
    () {
      final inventory =
          rentalInventory(
            offers: [
              groupOffer.copyWith(
                draftDetails: const RentalOfferDraftDetails(
                  groupFacilities: ['Exclusive balcony'],
                ),
              ),
            ],
          ).copyWith(
            draftDetails: const RentalSharedDraftDetails(
              facilities: ['Kitchen'],
              rules: ['Quiet after ten'],
            ),
            rooms: [
              rentalRooms.first.copyWith(
                draftDetails: const RentalRoomDraftDetails(
                  area: '18.5',
                  furnished: true,
                  contents: ['Bed', 'Desk'],
                  features: ['Balcony'],
                  photoRefs: ['local-photo'],
                ),
                beds: [
                  rentalRooms.first.beds.first.copyWith(
                    draftDetails: const RentalBedDraftDetails(
                      type: 'Single',
                      storage: 'Locker',
                      description: 'Near window',
                    ),
                  ),
                ],
              ),
              rentalRooms[1],
            ],
          );
      final form = rentalForm(inventory);
      final recovered = OwnerDraftFormCodec.decode(
        OwnerDraftFormCodec.encode(form),
      );
      expect(recovered.rentalInventory, inventory);
      expect(recovered.selectedOfferRef, form.selectedOfferRef);
      expect(recovered.canSaveToServer(offersEnabled), isFalse);
      expect(
        () => recovered.toJson(capabilities: offersEnabled),
        throwsStateError,
      );
      expect(() => inventory.toRequestJson(), throwsStateError);
      final json = inventory.toJson();
      expect(jsonEncode(json), isNot(contains('local_details')));
      expect(RentalInventory.fromJson(json).hasLocalOnlyDetails, isFalse);
    },
  );
  test(
    'group area requires all included areas; invalid entered area fails accommodation validation',
    () {
      var form = rentalForm(rentalInventory(offers: [groupOffer]));
      final room = form.rentalInventory!.rooms.first.copyWith(
        draftDetails: const RentalRoomDraftDetails(area: 'NaN'),
      );
      form = form.copyWith(
        rentalInventory: OwnerAccommodationDraftData.replaceRoom(
          form.rentalInventory!,
          room,
        ),
      );
      expect(form.isAccommodationReady, isFalse);
      expect(room.draftDetails.knownArea, isNull);
      expect(const RentalRoomDraftDetails(area: '').isValid, isTrue);
      expect(const RentalRoomDraftDetails(area: '0').isValid, isFalse);
    },
  );
  for (final offer in [
    wholeOffer,
    independentRooms.last,
    groupOffer,
    bedOffer,
  ]) {
    test(
      'edit restoration retains exact ${offer.scope} identity and values',
      () {
        final inventory = rentalInventory(
          offers: [offer],
          mode: offer.scope == RentalScope.entireProperty ? 'whole' : 'partial',
        );
        final seed = OwnerAddPropertyMapper.fromProperty(
          rentalProperty(inventory: inventory),
          offerId: offer.id,
        ).form;
        expect(seed.rentalScope, offer.scope);
        expect(seed.selectedOffer!.id, offer.id);
        expect(seed.selectedOffer!.roomRefs, offer.roomRefs);
        expect(seed.selectedOffer!.bedRef, offer.bedRef);
        expect(
          OwnerAccommodationDraftData.chooseScope(
            seed,
            RentalScope.bed,
          ).rentalInventory,
          inventory,
        );
      },
    );
  }
  test(
    'durable draft copying preserves selected offer, unit values and photo associations',
    () async {
      final root = await Directory.systemTemp.createTemp('sokoun-unit-draft');
      addTearDown(() => root.delete(recursive: true));
      final image = await File(
        '${root.path}/picker.jpg',
      ).writeAsBytes([1, 2, 3]);
      final room = rentalRooms.first.copyWith(
        draftDetails: const RentalRoomDraftDetails(
          area: '20',
          contents: ['Desk'],
          photoRefs: ['unit-photo'],
        ),
      );
      final form =
          rentalForm(
            rentalInventory(
              offers: [independentRooms.first],
            ).copyWith(rooms: [room]),
          ).copyWith(
            selectedOfferRef: independentRooms.first.id,
            photoDrafts: [
              OwnerPropertyPhotoDraft(file: image, draftKey: 'unit-photo'),
            ],
          );
      final store = OwnerDraftData(
        accountId: 'unit-owner',
        propertyId: 'unit-property',
        supportDirectory: () async => root,
      );
      await store.write(OwnerPropertyDraft(form: form));
      await image.delete();
      final restored = (await store.read()).form!;
      expect(restored.rentalScope, RentalScope.room);
      expect(restored.selectedOffer!.id, independentRooms.first.id);
      expect(restored.rentalInventory!.rooms.single.draftDetails.area, '20');
      expect(
        restored.rentalInventory!.rooms.single.draftDetails.photoRefs.single,
        restored.photoDrafts.single.reference,
      );
      expect(await restored.photoDrafts.single.file!.readAsBytes(), [1, 2, 3]);
    },
  );
}
