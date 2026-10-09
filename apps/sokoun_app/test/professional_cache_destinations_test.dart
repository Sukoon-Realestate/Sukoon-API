import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/exceptions.dart';
import 'package:melos_core/core/extensions/error_handler_extension.dart';
import 'package:sokoun_app/features/tenant/home/data/public_property_cache.dart';
import 'package:sokoun_app/features/shared/destinations/data/destination_resolver.dart';
import 'package:sokoun_app/features/shared/destinations/data/models/app_destination.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/app_notification_content.dart';
import 'package:sokoun_app/features/owner/visits/data/models/owner_availability_content.dart';
import 'package:sokoun_app/features/owner/visits/data/owner_availability_draft_data.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'helpers/rental_offer_fixtures.dart';

void main() {
  test('public cache preserves an identified rental bed and its terms', () {
    final property = rentalProperty(
      inventory: rentalInventory(),
    ).copyWith(status: 'published', isSaved: true);
    final cached = PublicPropertyCache.sanitize(property.toJson());
    final restored = PropertyDetailsModel.fromJson(cached);
    final inventory = restored.rentalInventory!;
    expect(inventory.isSupported, isTrue);
    expect(inventory.revision, property.rentalInventory!.revision);
    expect(inventory.offers.single.id, bedOffer.id);
    expect(inventory.offers.single.bedRef, 'bed-a1');
    expect(inventory.offers.single.roomRefs, ['room-a']);
    expect(inventory.offers.single.terms, offerTerms);
    expect(inventory.rooms.first.beds.first.id, 'bed-a1');
    expect(restored.ownershipProof, isEmpty);
    expect(restored.isSaved, isFalse);
    expect(inventory.offers.single.canArchive, isFalse);
  });
  test(
    'public cache removes nested contact, proof, permission and favorite fields',
    () {
      final json = PublicPropertyCache.sanitize({
        'id': 'property-1',
        'title': 'Apartment',
        'is_saved': true,
        'owner_phone': 'private',
        'ownership_proof': 'private-url',
        'owner': {
          'id': 'owner-1',
          'name': 'Published name',
          'phone_number': 'private',
          'national_id': 'private',
          'allowed_actions': {'delete': true},
        },
        'offers': [
          {
            'id': 'offer-1',
            'monthly_price': 5000,
            'can_book': true,
            'contact': {'phone': 'private'},
            'document': 'private',
          },
        ],
      });
      expect(json, {
        'id': 'property-1',
        'title': 'Apartment',
        'owner': {'id': 'owner-1', 'name': 'Published name'},
        'offers': [
          {'id': 'offer-1', 'monthly_price': 5000},
        ],
      });
      expect(
        PublicPropertyCache.sanitize({
          'id': 'owner-draft',
          'status': 'under_review',
          'ownership_proof': 'private',
        }),
        isEmpty,
      );
    },
  );

  for (final code in [401, 403, 404, 410, 423]) {
    test('HTTP $code invalidates saved content and never falls back', () async {
      bool invalidated = false, read = false;
      final result =
          await Future<BaseModel<String>>.error(
            ServerException('Unavailable', statusCode: code),
          ).handleCallbackWithCache(
            cacheKey: 'property',
            fromCacheJson: (json) => json['title'] as String,
            toJson: (value) => {'title': value},
            onSave: (_, _) {},
            onRead: (_) {
              read = true;
              return {'title': 'Stale'};
            },
            onInvalidate: (_) => invalidated = true,
          );
      expect(result.isError(), isTrue);
      expect(invalidated, isTrue);
      expect(read, isFalse);
    });
  }
  test('a transient refresh failure preserves valid saved content', () async {
    final result =
        await Future<BaseModel<String>>.error(
          const ServerException('Temporary', statusCode: 503),
        ).handleCallbackWithCache(
          cacheKey: 'property',
          fromCacheJson: (json) => json['title'] as String,
          toJson: (value) => {'title': value},
          onSave: (_, _) {},
          onRead: (_) => {'title': 'Saved apartment'},
        );
    expect(result.tryGetSuccess()?.data, 'Saved apartment');
    expect(result.tryGetSuccess()?.key, 'fromCache');
  });

  test(
    'only supported property hosts, routes and resource IDs can navigate',
    () {
      final valid = DestinationResolver.propertyLink(
        Uri.parse('https://sokoun.app/properties/p-1/offers/o-2'),
      );
      expect(valid?.id, 'p-1');
      expect(valid?.offerId, 'o-2');
      for (final link in [
        'http://sokoun.app/properties/p-1',
        'https://evil.example/properties/p-1',
        'https://someone@sokoun.app/properties/p-1',
        'https://sokoun.app:444/properties/p-1',
        '//evil.example/properties/p-1',
        'https://sokoun.app/properties/null',
        'https://sokoun.app/properties/p%2F1',
        'https://sokoun.app/visits/v-1',
        'https://sokoun.app/properties/p-1?offer_id=a&offer_id=b',
        'https://sokoun.app/properties/p-1/offers/a?offer_id=b',
      ]) {
        expect(
          DestinationResolver.propertyLink(Uri.parse(link)),
          isNull,
          reason: link,
        );
      }
    },
  );

  test(
    'review notification uses a typed real visit ID and safely handles missing IDs',
    () {
      final valid = DestinationResolver.notification(
        AppNotificationContent.fromPushPayload({
          'type': 'visit_review',
          'notification_id': 'n-1',
          'visit_id': 'visit-8',
          'property_id': 'property-9',
        }),
      );
      expect(valid.kind, DestinationKind.tenantVisit);
      expect(valid.id, 'visit-8');
      expect(valid.openReview, isTrue);
      final missing = DestinationResolver.notification(
        AppNotificationContent.fromPushPayload({
          'type': 'visit_review',
          'notification_id': 'n-2',
          'target_id': 'property-9',
        }),
      );
      expect(missing.kind, DestinationKind.tenantVisits);
      expect(missing.openReview, isFalse);
    },
  );

  test(
    'fresh booked or locked availability cannot be overwritten by a restored draft',
    () {
      final draft = [
        OwnerAvailabilitySlotContent.fromJson({
          'time': '14:00:00',
          'is_enabled': false,
        }),
        OwnerAvailabilitySlotContent.fromJson({
          'time': '15:00:00',
          'is_enabled': true,
        }),
      ];
      final fresh = [
        OwnerAvailabilitySlotContent.fromJson({
          'id': 'slot-1',
          'time': '14:00:00',
          'is_enabled': true,
          'state': 'booked',
          'visit': {'id': 'visit-1'},
        }),
        OwnerAvailabilitySlotContent.fromJson({
          'id': 'slot-2',
          'time': '15:00:00',
          'is_enabled': false,
          'is_locked': true,
        }),
      ];
      final result = OwnerAvailabilityDraftData.reconcile(draft, fresh);
      expect(result.conflict, isTrue);
      expect(result.slots, fresh);
    },
  );
}
