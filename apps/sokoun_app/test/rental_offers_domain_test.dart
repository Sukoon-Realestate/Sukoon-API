import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_scope.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_inventory.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_listing_summary.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_offer.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_property_link.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_draft_editing.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_inventory_confirmation.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_inventory_validation.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import 'package:sokoun_app/features/shared/finance/presentation/egyptian_pound_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_property_draft.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/data/owner_property_photos_data.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/property_form_validation.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_room.dart';
import 'package:sokoun_app/features/tenant/home/data/rental_property_gallery_data.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/owner/home/data/owner_add_property_mapper.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/models/property_cost_breakdown.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';
import 'package:sokoun_app/features/tenant/visits/data/models/book_visit_body.dart';
import 'package:sokoun_app/features/tenant/visits/data/models/tenant_visit_details_content.dart';
import 'package:sokoun_app/features/tenant/visits/data/models/visit_property_content.dart';
import 'package:sokoun_app/features/owner/visits/data/models/owner_visit_request_details_content.dart';
import 'package:sokoun_app/features/owner/visits/data/models/owner_visit_calendar_content.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/notification_payload_content.dart';
import 'helpers/rental_offer_fixtures.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('scope and room changes clear stale bed and accommodation media', () {
    final group = groupOffer.copyWith(id: '', mediaIds: ['photo-a']);
    final room = RentalDraftEditing.changeScope(group, RentalScope.room);
    expect(room.roomRefs, isEmpty);
    expect(room.mediaIds, isEmpty);
    expect(room.terms, group.terms);
    final bed = RentalDraftEditing.selectRoom(
      bedOffer.copyWith(id: ''),
      roomRef: 'room-b',
      selected: true,
    );
    expect(bed.roomRefs, ['room-b']);
    expect(bed.bedRef, isEmpty);
    expect(bed.mediaIds, isEmpty);
    final whole = RentalDraftEditing.changeScope(
      bedOffer,
      RentalScope.entireProperty,
    );
    expect(whole.roomRefs, isEmpty);
    expect(whole.bedRef, isEmpty);
    expect(whole.terms.price, offerTerms.price);
  });
  test('local mode changes cannot replace published accommodation', () {
    final existing = rentalInventory();
    expect(
      RentalDraftEditing.chooseScope(existing, RentalScope.entireProperty),
      same(existing),
    );
    final parked = existing.copyWith(offers: [], parkedOffers: [bedOffer]);
    expect(
      RentalDraftEditing.chooseScope(parked, RentalScope.room),
      same(parked),
    );
  });
  test('empty room references cannot authorize a named accommodation', () {
    final selection = RentalSelection.fromOffer(
      propertyId: 'property-a',
      inventory: rentalInventory(),
      offer: bedOffer,
    );
    expect(selection.canIdentify, isTrue);
    expect(selection.copyWith(roomIds: ['']).canIdentify, isFalse);
    expect(selection.copyWith(propertyId: ' ').canIdentify, isFalse);
    expect(selection.copyWith(offerId: ' ').canIdentify, isFalse);
    expect(selection.copyWith(bedId: ' ').canIdentify, isFalse);
  });
  test(
    'unfinished partial room drafts do not block a new whole-property offer',
    () {
      final inventory = rentalInventory(
        offers: [wholeOffer.copyWith(id: '', draftKey: 'whole-local')],
        mode: 'whole',
      ).copyWith(rooms: const [RentalRoom(draftKey: 'unfinished-room')]);
      final form = rentalForm(inventory);
      expect(form.rentalInventory!.rooms, hasLength(1));
      expect(form.submissionInventory!.rooms, isEmpty);
      expect(form.isInventoryReady, isTrue);
      final request = form.toJson(capabilities: offersEnabled);
      expect(jsonDecode(request['rental_inventory'])['rooms'], isEmpty);
    },
  );
  test('removing a property photo clears active and parked associations', () {
    final inventory = rentalInventory().copyWith(
      parkedOffers: [
        groupOffer.copyWith(mediaIds: ['photo-a']),
      ],
      offers: [
        bedOffer.copyWith(mediaIds: ['photo-a']),
      ],
    );
    final updated = RentalDraftEditing.withoutMedia(inventory, 'photo-a')!;
    expect(updated.rooms.first.mediaIds, isEmpty);
    expect(updated.offers.single.mediaIds, isEmpty);
    expect(updated.parkedOffers.single.mediaIds, isEmpty);
    expect(updated.sharedMediaIds, ['photo-shared']);
  });
  test(
    'copied photo files are detected and checksums survive local draft recovery',
    () async {
      final directory = await Directory.systemTemp.createTemp(
        'sokoun-photo-check',
      );
      addTearDown(() => directory.delete(recursive: true));
      final first = await File(
        '${directory.path}/first.jpg',
      ).writeAsBytes([1, 2, 3]);
      final copy = await File(
        '${directory.path}/copy.jpg',
      ).writeAsBytes([1, 2, 3]);
      final other = await File(
        '${directory.path}/other.jpg',
      ).writeAsBytes([4, 5, 6]);
      final checked = await OwnerPropertyPhotosData.check([
        OwnerPropertyPhotoDraft(file: first),
        OwnerPropertyPhotoDraft(file: copy),
        OwnerPropertyPhotoDraft(file: other),
      ]);
      expect(checked.hasDuplicates, isTrue);
      final repeated = await OwnerPropertyPhotosData.check(checked.photos);
      for (var index = 0; index < checked.photos.length; index++) {
        expect(repeated.photos[index], same(checked.photos[index]));
      }
      expect(
        checked.photos.first.contentFingerprint,
        checked.photos[1].contentFingerprint,
      );
      final form = rentalForm(
        rentalInventory(),
      ).copyWith(photoDrafts: checked.photos);
      expect(form.hasDuplicatePhotos, isTrue);
      final recovered = OwnerDraftFormCodec.decode(
        OwnerDraftFormCodec.encode(form),
      );
      expect(recovered.hasDuplicatePhotos, isTrue);
      final request = form.toJson(capabilities: offersEnabled);
      expect(request.toString(), isNot(contains('local_sha256')));
      expect(
        request.toString(),
        isNot(contains(checked.photos.first.contentFingerprint)),
      );
    },
  );
  test('known remote video durations obey the property media limits', () {
    final remote = rentalForm(rentalInventory())
        .copyWith(clearVideo: true)
        .copyWith(videoUrl: 'https://example.com/tour.mp4');
    for (final seconds in [0, 61]) {
      final invalid = remote.copyWith(videoDuration: seconds);
      expect(invalid.isVideoReady, isFalse);
      expect(PropertyFormValidation.video(invalid), isNotNull);
    }
    for (final seconds in [1, 60]) {
      final valid = remote.copyWith(videoDuration: seconds);
      expect(valid.isVideoReady, isTrue);
      expect(PropertyFormValidation.video(valid), isNull);
    }
    // Existing remote media without duration metadata stays server-validated.
    expect(remote.isVideoReady, isTrue);
  });
  test(
    'general property fallback labels context and excludes known unrelated rooms',
    () {
      final offer = independentRooms.last;
      final inventory = rentalInventory(offers: [offer]).copyWith(
        rooms: [
          rentalRooms.first,
          rentalRooms[1].copyWith(mediaIds: []),
          rentalRooms.last,
        ],
      );
      final property = rentalProperty(inventory: inventory).copyWith(
        images: [
          ...rentalProperty().images,
          PropertyImageModel.initial().copyWith(
            id: 'photo-general',
            image: 'https://example.com/building.jpg',
          ),
        ],
      );
      final selection = RentalSelection.fromOffer(
        propertyId: property.id,
        inventory: inventory,
        offer: offer,
      );
      final gallery = RentalPropertyGallery.fromProperty(
        property,
        selection: selection,
      );
      expect(
        gallery.images.map((photo) => photo.id),
        containsAll(['photo-general', 'photo-shared']),
      );
      expect(
        gallery.images.map((photo) => photo.id),
        isNot(contains('photo-a')),
      );
      expect(gallery.hasGeneralPhotos, isTrue);
      final content = TenantPropertyDetailsContent.fromModel(
        property,
        selection: selection,
      );
      expect(content.title, offer.name);
      expect(content.description, offer.terms.description);
      expect(content.propertyDescription, property.description);
      expect(content.galleryHasGeneralPhotos, isTrue);
    },
  );
  test(
    'before confirmation links preserve the chosen offer but do not authorize actions',
    () {
      final inventory = rentalInventory(offers: [bedOffer.copyWith(link: '')]);
      final property = rentalProperty(
        inventory: inventory,
      ).copyWith(propertyLink: 'https://sokoun.app/properties/property-a');
      final selection = RentalSelection.fromOffer(
        propertyId: property.id,
        inventory: inventory,
        offer: inventory.offers.single,
      );
      final content = TenantPropertyDetailsContent.fromModel(
        property,
        selection: selection,
      );
      expect(content.selectionConfirmed, isFalse);
      expect(
        RentalPropertyLink.parse(Uri.parse(content.shareUrl))?.offerId,
        bedOffer.id,
      );
      expect(
        selection.sameTermsAs(selection.copyWith(bedName: 'Changed bed')),
        isFalse,
      );
      final withoutChoice = TenantPropertyDetailsContent.fromModel(property);
      expect(withoutChoice.price, isEmpty);
      expect(withoutChoice.description, isEmpty);
      expect(withoutChoice.pricePeriodLabel, isEmpty);
      expect(withoutChoice.propertyDescription, property.description);
    },
  );
  test(
    'summary price must be valid and match scope and price-period context',
    () {
      const summary = RentalListingSummary(
        count: 2,
        scopes: ['bed'],
        price: '1500',
        pricePeriod: 'monthly',
        priceScope: 'bed',
        startingFrom: true,
      );
      expect(summary.matchesContext(scope: 'bed', period: 'monthly'), isTrue);
      expect(summary.matchesContext(scope: 'bed', period: 'weekly'), isFalse);
      for (final invalid in [
        summary.copyWith(count: 0),
        summary.copyWith(price: 'NaN'),
        summary.copyWith(price: '-100'),
        summary.copyWith(priceScope: 'unknown'),
        summary.copyWith(pricePeriod: 'unknown'),
      ]) {
        expect(
          RentalOfferLabels.listingPrice(
            invalid,
            hasInventory: true,
            legacyPrice: '9000',
            legacyPeriod: 'monthly',
          ),
          LocaleKeys.rentalSelectForPrice,
        );
      }
      expect(
        RentalOfferLabels.listingPrice(
          summary,
          hasInventory: true,
          legacyPrice: '9000',
          legacyPeriod: 'monthly',
          contextPricePeriod: 'weekly',
        ),
        LocaleKeys.rentalSelectForPrice,
      );
    },
  );
  Set<RentalInventoryIssue> issues(RentalInventory inventory) =>
      RentalInventoryValidation.validate(inventory, totalBedrooms: 3);
  for (final entry in {
    'entire property': rentalInventory(offers: [wholeOffer], mode: 'whole'),
    'one room': rentalInventory(offers: [independentRooms.first]),
    'rooms together': rentalInventory(offers: [groupOffer]),
    'independent rooms': rentalInventory(offers: independentRooms),
    'bed inside a shared room': rentalInventory(),
  }.entries) {
    test('validates ${entry.key} and retains the physical property count', () {
      expect(issues(entry.value), isEmpty);
      final property = rentalProperty(inventory: entry.value);
      expect(property.bedrooms, 3);
      expect(property.propertyType, 'apartment');
      expect(PropertyDetailsModel.fromJson(property.toJson()), property);
    });
  }
  test(
    'two rooms together have one combined price; independent rooms keep two prices and periods',
    () {
      final group = rentalInventory(offers: [groupOffer]);
      final separate = rentalInventory(offers: independentRooms);
      expect(group.offers.single.roomRefs, hasLength(2));
      expect(group.resolved(group.offers.single).terms.price, '5000');
      expect(separate.offers.map((offer) => offer.terms.price), [
        '1500',
        '2200',
      ]);
      expect(separate.offers.map((offer) => offer.terms.pricePeriod), [
        'monthly',
        'weekly',
      ]);
    },
  );
  test(
    'two distinct beds remain independent and a rented bed does not hide the other',
    () {
      final second = bedOffer.copyWith(id: 'offer-bed-a2', bedRef: 'bed-a2');
      final inventory = rentalInventory(
        offers: [
          bedOffer.copyWith(availability: 'rented'),
          second,
        ],
      );
      expect(issues(inventory), isEmpty);
      expect(
        inventory.offers
            .where((offer) => offer.isAvailable)
            .map((offer) => offer.id),
        ['offer-bed-a2'],
      );
      expect(
        inventory.offers.first.roomRefs.single,
        inventory.offers.last.roomRefs.single,
      );
      expect(
        inventory.offers.first.bedRef,
        isNot(inventory.offers.last.bedRef),
      );
    },
  );
  final conflicting = {
    'same whole room': [
      independentRooms.first,
      independentRooms.first.copyWith(id: 'another'),
    ],
    'room and group': [independentRooms.first, groupOffer],
    'whole room and its bed': [independentRooms.first, bedOffer],
    'duplicate bed': [bedOffer, bedOffer.copyWith(id: 'another')],
    'rented room and bed': [
      independentRooms.first.copyWith(availability: 'rented'),
      bedOffer,
    ],
  };
  for (final entry in conflicting.entries) {
    test(
      'rejects overlap for ${entry.key}',
      () => expect(
        issues(rentalInventory(offers: entry.value)),
        contains(RentalInventoryIssue.overlap),
      ),
    );
  }
  test('whole and partial offering modes are exclusive', () {
    expect(
      issues(rentalInventory(offers: [wholeOffer, bedOffer])),
      contains(RentalInventoryIssue.mode),
    );
    expect(
      issues(rentalInventory(offers: [bedOffer], mode: 'whole')),
      contains(RentalInventoryIssue.mode),
    );
  });
  test(
    'groups require distinct rooms; a bed must belong to its selected room',
    () {
      expect(
        issues(
          rentalInventory(
            offers: [
              groupOffer.copyWith(roomRefs: ['room-a', 'room-a']),
            ],
          ),
        ),
        contains(RentalInventoryIssue.roomGroup),
      );
      expect(
        issues(
          rentalInventory(
            offers: [
              bedOffer.copyWith(roomRefs: ['room-b']),
            ],
          ),
        ),
        contains(RentalInventoryIssue.selection),
      );
      expect(
        issues(
          rentalInventory(offers: [bedOffer.copyWith(bedRef: 'missing-bed')]),
        ),
        contains(RentalInventoryIssue.selection),
      );
    },
  );
  test('stable identities and physical capacity are validated', () {
    final duplicateRooms = rentalInventory().copyWith(
      rooms: [rentalRooms.first, rentalRooms.first],
    );
    expect(issues(duplicateRooms), contains(RentalInventoryIssue.roomIdentity));
    final tooSmall = rentalInventory().copyWith(
      rooms: [rentalRooms.first.copyWith(capacity: 1)],
    );
    expect(issues(tooSmall), contains(RentalInventoryIssue.capacity));
  });
  test(
    'unknown scopes remain unknown and cannot become entire-property offers',
    () {
      final future = RentalOffer.fromJson({
        ...bedOffer.toJson(),
        'rental_scope': 'floor_fraction',
      });
      expect(future.scope, isNull);
      expect(future.hasUnknownScope, isTrue);
      expect(future.toJson()['rental_scope'], 'floor_fraction');
      expect(
        issues(rentalInventory(offers: [future])),
        contains(RentalInventoryIssue.unsupported),
      );
      expect(RentalOffer.fromJson({}).hasUnknownScope, isFalse);
    },
  );
  test(
    'legacy room listings stay legacy and never receive fabricated offer IDs',
    () {
      final legacy = rentalProperty().copyWith(propertyType: 'room');
      final restored = PropertyDetailsModel.fromJson(legacy.toJson());
      expect(restored.rentalInventory, isNull);
      expect(restored.propertyType, 'room');
      expect(
        OwnerAddPropertyMapper.fromProperty(restored).form.rentalInventory,
        isNull,
      );
      expect(RentalSelection.fromRecord({'property': legacy.toJson()}), isNull);
      expect(
        RentalInventory.read({'rental_inventory': null})!.isSupported,
        isFalse,
      );
      expect(
        RentalInventory.read({'rental_schema_version': 99})!.isSupported,
        isFalse,
      );
    },
  );
  test('scope-dependent payloads exclude parked and irrelevant data', () {
    final bed = bedOffer.toRequestJson();
    expect(bed['room_ids'], ['room-a']);
    expect(bed['bed_id'], 'bed-a1');
    final room = RentalDraftEditing.changeScope(
      bedOffer,
      RentalScope.room,
    ).toRequestJson();
    expect(room['room_ids'], ['room-a']);
    expect(room.containsKey('bed_id'), isFalse);
    final whole = RentalDraftEditing.changeScope(
      bedOffer,
      RentalScope.entireProperty,
    ).toRequestJson();
    expect(whole.containsKey('bed_id'), isFalse);
    expect(whole.containsKey('room_ids'), isFalse);
    expect(
      rentalInventory()
          .copyWith(parkedOffers: [wholeOffer])
          .toRequestJson()
          .containsKey('parked_offers'),
      isFalse,
    );
  });
  test(
    'partial property payload keeps three bedrooms and sends no legacy price or terms',
    () {
      final form = rentalForm(rentalInventory(offers: [groupOffer]));
      final body = form.toJson(isEditing: true, capabilities: offersEnabled);
      expect(body['bedrooms'], 3);
      for (final key in [
        'price',
        'price_period',
        'rental_period',
        'description',
        'suitable_for',
        'deposit',
        'smoking_allowed',
      ]) {
        expect(body.containsKey(key), isFalse, reason: key);
      }
      final submitted = jsonDecode(body['rental_inventory'] as String) as Map;
      expect(
        (submitted['offers'] as List).single['term_overrides']['price'],
        '5000',
      );
      expect((submitted['offers'] as List).single['room_ids'], hasLength(2));
      expect(submitted['expected_revision'], 12);
    },
  );
  test(
    'entire property editing uses the offer price and retains minimum months separately',
    () {
      final form = rentalForm(
        rentalInventory(offers: [wholeOffer], mode: 'whole'),
      );
      expect(form.monthlyPrice, '1500');
      expect(form.rentalDuration, '3');
      final body = form
          .copyWith(rentalDuration: '8', rentalUnit: 'weekly')
          .toJson(capabilities: offersEnabled);
      final inventory = jsonDecode(body['rental_inventory'] as String) as Map;
      final terms = (inventory['offers'] as List).single['term_overrides'];
      expect(terms['rental_period'], 8);
      expect(terms['price_period'], 'weekly');
    },
  );
  test(
    'media associations are omitted for servers without that capability',
    () {
      final inventory = rentalInventory();
      final body = rentalForm(inventory).toJson(
        capabilities: const RentalOfferCapabilities(
          contractVersion: 1,
          inventoryWrites: true,
        ),
      );
      final payload = jsonDecode(body['rental_inventory'] as String) as Map;
      expect(payload.containsKey('shared_media_ids'), isFalse);
      expect(
        (payload['offers'] as List).single.containsKey('media_ids'),
        isFalse,
      );
      expect(
        (payload['rooms'] as List).first.containsKey('media_ids'),
        isFalse,
      );
      expect(
        ((payload['rooms'] as List).first['beds'] as List).first.containsKey(
          'media_ids',
        ),
        isFalse,
      );
    },
  );
  test(
    'shared defaults are explicit and an independent price cannot be inherited',
    () {
      final offer = bedOffer.copyWith(
        inheritedFields: {'rental_period', 'deposit'},
        terms: offerTerms.copyWith(minimumMonths: 1, deposit: 'none'),
      );
      final inventory = rentalInventory(offers: [offer]).copyWith(
        defaults: offerTerms.copyWith(
          price: '99999',
          minimumMonths: 9,
          deposit: 'two_months',
        ),
      );
      expect(inventory.resolved(offer).terms.price, '1500');
      expect(inventory.resolved(offer).terms.minimumMonths, 9);
      expect(inventory.resolved(offer).terms.deposit, 'two_months');
      expect(
        (offer.toRequestJson()['term_overrides'] as Map).containsKey('deposit'),
        isFalse,
      );
      expect(
        (inventory.toRequestJson()['shared_defaults'] as Map).containsKey(
          'price',
        ),
        isFalse,
      );
    },
  );
  test(
    'local draft round-trip preserves inventory, parked mode and idempotency key',
    () {
      final partial = RentalDraftEditing.chooseScope(null, RentalScope.bed);
      final whole = RentalDraftEditing.chooseScope(
        partial,
        RentalScope.entireProperty,
      );
      final restored = RentalDraftEditing.chooseScope(whole, RentalScope.bed);
      expect(restored.offers.single.reference, partial.offers.single.reference);
      expect(restored.offers.single.id, isEmpty);
      final form = rentalForm(restored);
      final decoded = OwnerDraftFormCodec.decode(
        OwnerDraftFormCodec.encode(form),
      );
      expect(decoded.rentalInventory, form.rentalInventory);
      expect(decoded.submissionKey, 'stable-submission-key');
    },
  );
  test(
    'unsupported capability and unsupported inventory cannot serialize a new write',
    () {
      final form = rentalForm(rentalInventory());
      expect(() => form.toJson(), throwsStateError);
      expect(
        () => form
            .copyWith(
              rentalInventory: rentalInventory().copyWith(schemaVersion: 77),
            )
            .toJson(capabilities: offersEnabled),
        throwsStateError,
      );
      expect(
        const RentalOfferCapabilities(
          contractVersion: 2,
          inventoryWrites: true,
        ).canWrite,
        isFalse,
      );
    },
  );
  test('publication photo and video requirements remain property-level', () {
    final form = rentalForm(rentalInventory(offers: independentRooms));
    expect(form.photoCount, 10);
    expect(form.isPhotosReady, isTrue);
    expect(
      form
          .copyWith(photoDrafts: form.photoDrafts.take(9).toList())
          .isPhotosReady,
      isFalse,
    );
    expect(
      form.copyWith(videoFile: null, clearVideo: true).isPhotosReady,
      isFalse,
    );
  });
  test(
    'server projection controls grouped-card prices rather than physical property price',
    () {
      const summary = RentalListingSummary(
        price: '1500',
        pricePeriod: 'monthly',
        priceScope: 'bed',
        count: 1,
      );
      final label = RentalOfferLabels.listingPrice(
        summary,
        hasInventory: true,
        legacyPrice: '9000',
        legacyPeriod: 'monthly',
      );
      expect(
        label,
        contains(EgyptianPoundText.format('1500', period: 'monthly')),
      );
      expect(
        label,
        isNot(contains(EgyptianPoundText.format('9000', period: 'monthly'))),
      );
      expect(
        RentalOfferLabels.listingPrice(
          null,
          hasInventory: true,
          legacyPrice: '9000',
          legacyPeriod: 'monthly',
        ),
        isNot(contains('9000')),
      );
    },
  );
  test(
    'search scope stays separate from property type and prices require one period',
    () {
      final filters = const PropertySearchFilters.initial().copyWith(
        propertyType: 'apartment',
        rentalScope: 'bed',
        priceMin: '1000',
        pricePeriod: 'monthly',
        ordering: 'price',
      );
      final query = filters.toQueryParameters(capabilities: offersEnabled);
      expect(query['property_type'], 'apartment');
      expect(query['rental_scope'], 'bed');
      expect(query['price_min'], '1000');
      expect(query['price_period'], 'monthly');
      expect(query['rental_offers_version'], 1);
      expect(
        () => filters
            .copyWith(pricePeriod: '')
            .toQueryParameters(capabilities: offersEnabled),
        throwsStateError,
      );
      expect(() => filters.toQueryParameters(), throwsStateError);
      expect(
        filters.cacheKey,
        isNot(filters.copyWith(rentalScope: 'room').cacheKey),
      );
    },
  );
  test(
    'details and costs use the chosen bed and exclude unrelated room media and private evidence',
    () {
      final inventory = rentalInventory();
      final property = rentalProperty(inventory: inventory);
      final selected = RentalSelection.fromOffer(
        propertyId: property.id,
        inventory: inventory,
        offer: bedOffer,
      );
      final content = TenantPropertyDetailsContent.fromModel(
        property,
        selection: selected,
      );
      expect(content.imageUrls, [
        'https://example.com/a.jpg',
        'https://example.com/shared.jpg',
      ]);
      expect(content.imageUrls, isNot(contains('https://example.com/b.jpg')));
      expect(content.metrics.first.value, '3');
      expect(selected.capacity, 2);
      expect(selected.bedName, 'السرير أ١');
      expect(selected.toJson().toString(), isNot(contains('private.example')));
      expect(PropertyCostBreakdown.fromProperty(property).rent, isNull);
      expect(
        PropertyCostBreakdown.fromProperty(property, selection: selected).rent,
        1500,
      );
      expect(
        PropertyCostBreakdown.fromProperty(
          property,
          selection: selected,
        ).deposit,
        1500,
      );
      expect(content.shareUrl, bedOffer.link);
    },
  );
  test(
    'selected bed survives the viewing route and typed body without becoming a property request',
    () {
      final inventory = rentalInventory();
      final property = rentalProperty(inventory: inventory);
      final selected = RentalSelection.fromOffer(
        propertyId: property.id,
        inventory: inventory,
        offer: bedOffer,
      );
      final route = VisitPropertyContent.fromPropertyDetails(
        TenantPropertyDetailsContent.fromModel(property, selection: selected),
      );
      final restored = VisitPropertyContent.fromJson(route.toJson());
      expect(restored, route);
      expect(restored.selection, selected);
      final body = BookVisitBody.fromTime(
        visitDate: '2030-10-07',
        hour: 14,
        minute: 30,
        note: '',
        selection: restored.selection,
      );
      expect(
        body.toJson(capabilities: offersEnabled)['offer_id'],
        'offer-bed-a1',
      );
      expect(
        body.toJson(capabilities: offersEnabled)['expected_offer_revision'],
        7,
      );
      expect(() => body.toJson(), throwsStateError);
      expect(
        const BookVisitBody.initial().toJson().containsKey('offer_id'),
        isFalse,
      );
    },
  );
  test(
    'historical request identity and terms survive offer changes and caching',
    () {
      final selected = RentalSelection.fromOffer(
        propertyId: 'property-a',
        inventory: rentalInventory(),
        offer: bedOffer,
      );
      final record = {
        'id': 'visit-a',
        'offer_id': selected.offerId,
        'offer_snapshot': selected.toJson(),
        'property': rentalProperty(
          inventory: rentalInventory(
            offers: [
              bedOffer.copyWith(
                name: 'Changed',
                terms: offerTerms.copyWith(price: '8000'),
                archived: true,
              ),
            ],
          ),
        ).toJson(),
        'status': 'accepted',
      };
      final tenant = TenantVisitDetailsContent.fromJson(record);
      final owner = OwnerVisitRequestDetailsContent.fromJson(record);
      final calendar = OwnerCalendarVisitContent.fromJson(record);
      expect(tenant.rentalSelection, selected);
      expect(owner.rentalSelection, selected);
      expect(calendar.rentalSelection, selected);
      expect(
        TenantVisitDetailsContent.fromJson(tenant.toJson()).rentalSelection,
        selected,
      );
      expect(
        OwnerVisitRequestDetailsContent.fromJson(
          owner.toJson(),
        ).rentalSelection,
        selected,
      );
      expect(
        OwnerCalendarVisitContent.fromJson(calendar.toJson()).rentalSelection,
        selected,
      );
      final incomplete = RentalSelection.fromRecord({
        'offer_id': 'original-bed',
        'property': {'id': 'property-a', 'price': '9000'},
      })!;
      expect(incomplete.offerId, 'original-bed');
      expect(incomplete.terms.price, isEmpty);
      expect(incomplete.scope, isNull);
    },
  );
  test(
    'favorites preserve a specific unavailable offer under one parent property',
    () {
      final snapshot = RentalSelection.fromOffer(
        propertyId: 'property-a',
        inventory: rentalInventory(),
        offer: bedOffer.copyWith(availability: 'rented'),
      );
      final favorite = FavoritePropertyContent.fromJson({
        'id': 'property-a',
        'rental_schema_version': 1,
        'saved_offers': [snapshot.toJson()],
      });
      expect(favorite.savedOffers.single.offerId, bedOffer.id);
      expect(favorite.savedOffers.single.isAvailable, isFalse);
      expect(FavoritePropertyContent.fromJson(favorite.toJson()), favorite);
    },
  );
  test('notifications preserve offer references and encoded snapshots', () {
    final snapshot = RentalSelection.fromOffer(
      propertyId: 'property-a',
      inventory: rentalInventory(),
      offer: bedOffer,
    );
    final payload = NotificationPayloadContent.fromJson({
      'property_id': 'property-a',
      'offer_id': bedOffer.id,
      'offer_snapshot': jsonEncode(snapshot.toJson()),
    });
    expect(payload.rentalSelection, snapshot);
    expect(NotificationPayloadContent.fromJson(payload.toJson()), payload);
  });
  test(
    'older links open the property; offer links retain exact identities',
    () {
      expect(
        RentalPropertyLink.parse(
          Uri.parse('https://sokoun.app/properties/property-a'),
        )?.offerId,
        isNull,
      );
      expect(
        RentalPropertyLink.parse(
          Uri.parse('/properties/property-a?offer_id=offer-bed-a1'),
        )?.offerId,
        bedOffer.id,
      );
      expect(
        RentalPropertyLink.parse(Uri.parse(bedOffer.link))?.offerId,
        bedOffer.id,
      );
      expect(
        RentalPropertyLink.parse(
          Uri.parse('https://evil.example/properties/property-a'),
        ),
        isNull,
      );
      expect(
        RentalPropertyLink.parse(Uri.parse('/properties/property-a/offers/')),
        isNull,
      );
    },
  );
  test(
    'a response with a different scope or price cannot confirm persistence',
    () {
      final submitted = rentalInventory();
      expect(RentalInventoryConfirmation.matches(submitted, submitted), isTrue);
      expect(
        RentalInventoryConfirmation.matches(
          submitted,
          submitted.copyWith(
            offers: [bedOffer.copyWith(scopeValue: 'entire_property')],
          ),
        ),
        isFalse,
      );
      expect(
        RentalInventoryConfirmation.matches(
          submitted,
          submitted.copyWith(
            offers: [
              bedOffer.copyWith(terms: offerTerms.copyWith(price: '999')),
            ],
          ),
        ),
        isFalse,
      );
      expect(RentalInventoryConfirmation.matches(submitted, null), isFalse);
    },
  );
  test(
    'creation confirmation resolves draft references to real server identities',
    () {
      final room = rentalRooms.first.copyWith(
        id: '',
        draftKey: 'client-room',
        beds: [
          rentalRooms.first.beds.first.copyWith(id: '', draftKey: 'client-bed'),
        ],
      );
      final offer = bedOffer.copyWith(
        id: '',
        draftKey: 'client-offer',
        roomRefs: ['client-room'],
        bedRef: 'client-bed',
      );
      final draft = rentalInventory(offers: [offer]).copyWith(rooms: [room]);
      final saved = draft.copyWith(
        rooms: [
          room.copyWith(
            id: 'server-room',
            beds: [room.beds.single.copyWith(id: 'server-bed')],
          ),
        ],
        offers: [
          offer.copyWith(
            id: 'server-offer',
            roomRefs: ['server-room'],
            bedRef: 'server-bed',
          ),
        ],
      );
      expect(issues(draft), isEmpty);
      expect(RentalInventoryConfirmation.matches(draft, saved), isTrue);
      expect(saved.offerById('client-offer'), isNull);
      expect(saved.offerById('server-offer')?.bedRef, 'server-bed');
      expect(RentalInventoryConfirmation.matches(draft, draft), isFalse);
    },
  );
  test(
    'unknown or price inheritance cannot silently create contradictory terms',
    () {
      for (final field in ['price', 'price_period', 'future_default']) {
        expect(
          issues(
            rentalInventory(
              offers: [
                bedOffer.copyWith(inheritedFields: {field}),
              ],
            ),
          ),
          contains(RentalInventoryIssue.terms),
        );
      }
    },
  );
  test(
    'ignored accommodation metadata or media cannot confirm a successful save',
    () {
      final submitted = rentalInventory();
      expect(
        RentalInventoryConfirmation.matches(
          submitted,
          submitted.copyWith(offers: [bedOffer.copyWith(name: 'Another bed')]),
        ),
        isFalse,
      );
      expect(
        RentalInventoryConfirmation.matches(
          submitted,
          submitted.copyWith(
            rooms: [
              rentalRooms.first.copyWith(bathroomAccess: 'private'),
              ...rentalRooms.skip(1),
            ],
          ),
        ),
        isFalse,
      );
      final noMedia = submitted.copyWith(sharedMediaIds: []);
      expect(RentalInventoryConfirmation.matches(submitted, noMedia), isFalse);
      expect(
        RentalInventoryConfirmation.matches(
          submitted,
          noMedia,
          includeMedia: false,
        ),
        isTrue,
      );
    },
  );
}
