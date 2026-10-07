import 'dart:async';
import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/owner/home/presentation/cubits/property_submission_cubit.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_accommodation_draft_details.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/cubits/rental_inventory_mutation_cubit.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_save_cubit.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'helpers/rental_offer_fixtures.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _RentalRepository repository;
  late RentalSelection selection;
  setUp(() async {
    await injector.reset();
    repository = _RentalRepository();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
    selection = RentalSelection.fromOffer(
      propertyId: 'property-a',
      inventory: rentalInventory(),
      offer: bedOffer,
    );
  });
  tearDown(() => injector.reset());
  Future<void> mountFailurePresentation(WidgetTester tester) async {
    await tester.pumpWidget(
      ScreenUtilInit(
        designSize: const Size(390, 844),
        builder: (_, _) => MaterialApp(
          navigatorKey: Go.navigatorKey,
          home: const Scaffold(body: SizedBox()),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<bool> book(BookVisitCubit cubit, {RentalSelection? chosen}) async {
    var successful = false;
    await cubit.bookVisit(
      propertyId: 'property-a',
      visitDate: '2099-10-07',
      visitHour: 14,
      visitMinute: 30,
      note: 'Viewing only',
      selection: chosen ?? selection,
      hasRentalOffers: true,
      onSuccess: () => successful = true,
    );
    return successful;
  }

  test(
    'unsupported publishing is an error and makes no network request',
    () async {
      final cubit = PropertySubmissionCubit();
      addTearDown(cubit.close);
      var saved = false;
      await cubit.save(
        form: rentalForm(rentalInventory()),
        propertyId: 'property-a',
        onSuccess: (_) => saved = true,
      );
      expect(saved, isFalse);
      expect(cubit.state.isError, isTrue);
      expect(repository.requests, isEmpty);
    },
  );
  test(
    'enabling v1 writes cannot discard locally entered unit details',
    () async {
      final inventories = [
        rentalInventory(offers: [independentRooms.first]).copyWith(
          rooms: [
            rentalRooms.first.copyWith(
              draftDetails: const RentalRoomDraftDetails(area: '18.5'),
            ),
          ],
        ),
        rentalInventory(
          offers: [
            groupOffer.copyWith(
              draftDetails: const RentalOfferDraftDetails(
                groupFacilities: ['Private lounge for this group'],
              ),
            ),
          ],
        ),
        rentalInventory().copyWith(
          rooms: [
            rentalRooms.first.copyWith(
              beds: [
                rentalRooms.first.beds.first.copyWith(
                  draftDetails: const RentalBedDraftDetails(
                    storage: 'Locker A',
                  ),
                ),
                rentalRooms.first.beds.last,
              ],
            ),
          ],
        ),
      ];
      for (final inventory in inventories) {
        final cubit = PropertySubmissionCubit(capabilities: offersEnabled);
        addTearDown(cubit.close);
        var saved = false;
        await cubit.save(
          form: rentalForm(inventory),
          propertyId: 'property-a',
          onSuccess: (_) => saved = true,
        );
        expect(saved, isFalse);
        expect(cubit.state.isError, isTrue);
        expect(repository.requests, isEmpty);
      }
    },
  );
  test(
    'confirmed offer edit uses existing property PATCH with retained media and inventory revision',
    () async {
      final cubit = PropertySubmissionCubit(capabilities: offersEnabled);
      addTearDown(cubit.close);
      PropertyDetailsModel? saved;
      await cubit.save(
        form: rentalForm(rentalInventory()),
        propertyId: 'property-a',
        onSuccess: (property) => saved = property,
      );
      expect(saved?.rentalInventory?.offers.single.id, bedOffer.id);
      final request = repository.requests.single;
      expect(request.httpRequestType, HttpRequestType.patch);
      expect(request.api, 'properties/property-a/');
      expect(request.body!['retained_image_ids'], contains('photo-a'));
      expect(
        jsonDecode(request.body!['rental_inventory'])['expected_revision'],
        12,
      );
      expect(request.headers!['X-Rental-Offers-Version'], '1');
      expect(request.headers!.containsKey('Idempotency-Key'), isFalse);
    },
  );
  testWidgets('failed save keeps caller data and cannot report persistence', (
    tester,
  ) async {
    await mountFailurePresentation(tester);
    repository.failWrites = true;
    final cubit = PropertySubmissionCubit(capabilities: offersEnabled);
    addTearDown(cubit.close);
    final form = rentalForm(rentalInventory());
    var saved = false;
    await cubit.save(
      form: form,
      propertyId: 'property-a',
      onSuccess: (_) => saved = true,
    );
    expect(saved, isFalse);
    expect(cubit.state.isError, isTrue);
    expect(form.rentalInventory?.offers.single.id, bedOffer.id);
    expect(form.submissionKey, 'stable-submission-key');
    await tester.pump(const Duration(seconds: 5));
    await tester.pumpAndSettle();
  });
  testWidgets(
    'ignored offer fields fail confirmation but retain returned property ID for recovery',
    (tester) async {
      await mountFailurePresentation(tester);
      repository.property = rentalProperty();
      final cubit = PropertySubmissionCubit(capabilities: offersEnabled);
      addTearDown(cubit.close);
      var saved = false;
      await cubit.save(
        form: rentalForm(rentalInventory(), creating: true),
        onSuccess: (_) => saved = true,
      );
      expect(saved, isFalse);
      expect(cubit.state.isError, isTrue);
      expect(cubit.recoveryProperty?.id, 'property-a');
      // The flow persists this ID and resumes with PATCH, while the same create key
      // protects an ambiguous network failure where no response ID was received.
      expect(
        repository.requests.single.headers!['Idempotency-Key'],
        'stable-submission-key',
      );
      await tester.pump(const Duration(seconds: 5));
      await tester.pumpAndSettle();
    },
  );
  testWidgets(
    'server changing the submitted bed to a room fails save confirmation',
    (tester) async {
      await mountFailurePresentation(tester);
      repository.property = rentalProperty(
        inventory: rentalInventory(
          offers: [bedOffer.copyWith(scopeValue: 'room')],
        ),
      );
      final cubit = PropertySubmissionCubit(capabilities: offersEnabled);
      addTearDown(cubit.close);
      var saved = false;
      await cubit.save(
        form: rentalForm(rentalInventory()),
        propertyId: 'property-a',
        onSuccess: (_) => saved = true,
      );
      expect(saved, isFalse);
      expect(cubit.state.isError, isTrue);
      await tester.pump(const Duration(seconds: 5));
      await tester.pumpAndSettle();
    },
  );
  test(
    'unsupported offer viewing never falls back to a legacy property POST',
    () async {
      final cubit = BookVisitCubit();
      addTearDown(cubit.close);
      expect(await book(cubit), isFalse);
      expect(repository.requests, isEmpty);
    },
  );
  test(
    'viewing refreshes exact offer and posts its stable ID and expected revision',
    () async {
      final cubit = BookVisitCubit(capabilities: offersEnabled);
      addTearDown(cubit.close);
      expect(await book(cubit), isTrue);
      expect(repository.requests.map((r) => r.httpRequestType), [
        HttpRequestType.get,
        HttpRequestType.post,
      ]);
      expect(repository.requests.first.api, 'properties/property-a/');
      final body = repository.requests.last.body!;
      expect(body['offer_id'], 'offer-bed-a1');
      expect(body['expected_offer_revision'], 7);
      expect(body['visit_time'], '14:30:00');
      expect(body.containsKey('availability'), isFalse);
      expect(body.containsKey('lease_id'), isFalse);
    },
  );
  test('cached offer details cannot authorize a viewing', () async {
    repository.cachedReads = true;
    final cubit = BookVisitCubit(capabilities: offersEnabled);
    addTearDown(cubit.close);
    expect(await book(cubit), isFalse);
    expect(
      repository.requests.every(
        (r) => r.httpRequestType == HttpRequestType.get,
      ),
      isTrue,
    );
  });
  for (final entry in {
    'price changed': bedOffer.copyWith(
      terms: offerTerms.copyWith(price: '1800'),
    ),
    'revision changed': bedOffer.copyWith(revision: 8),
    'became rented': bedOffer.copyWith(availability: 'rented'),
    'archived': bedOffer.copyWith(archived: true),
    'became unknown': bedOffer.copyWith(scopeValue: 'future_scope'),
  }.entries) {
    test('viewing requires another review when offer ${entry.key}', () async {
      repository.property = rentalProperty(
        inventory: rentalInventory(offers: [entry.value]),
      );
      final cubit = BookVisitCubit(capabilities: offersEnabled);
      addTearDown(cubit.close);
      expect(await book(cubit), isFalse);
      expect(
        repository.requests.where(
          (r) => r.httpRequestType == HttpRequestType.post,
        ),
        isEmpty,
      );
    });
  }
  test(
    'concurrent clicks during fresh-offer validation send one request',
    () async {
      repository.pauseRead = Completer<void>();
      final cubit = BookVisitCubit(capabilities: offersEnabled);
      addTearDown(cubit.close);
      final first = book(cubit);
      expect(await book(cubit), isFalse);
      repository.pauseRead!.complete();
      expect(await first, isTrue);
      expect(
        repository.requests.where(
          (r) => r.httpRequestType == HttpRequestType.post,
        ),
        hasLength(1),
      );
    },
  );
  testWidgets(
    'a concurrent server conflict is an error, with no inventory mutation',
    (tester) async {
      await mountFailurePresentation(tester);
      repository.failWrites = true;
      final before = repository.property.toJson();
      final cubit = BookVisitCubit(capabilities: offersEnabled);
      addTearDown(cubit.close);
      expect(await book(cubit), isFalse);
      expect(cubit.state.isError, isTrue);
      expect(repository.property.toJson(), before);
      await tester.pump(const Duration(seconds: 5));
      await tester.pumpAndSettle();
    },
  );
  test(
    'account changes during validation prevent an offer viewing POST',
    () async {
      repository.pauseRead = Completer<void>();
      final cubit = BookVisitCubit(capabilities: offersEnabled);
      addTearDown(cubit.close);
      AccountSession.begin('tenant-a');
      addTearDown(AccountSession.end);
      final request = book(cubit);
      AccountSession.begin('tenant-b');
      repository.pauseRead!.complete();
      expect(await request, isFalse);
      expect(repository.requests.map((r) => r.httpRequestType), [
        HttpRequestType.get,
      ]);
    },
  );
  test(
    'account changes during owner validation prevent an inventory PATCH',
    () async {
      repository.pauseRead = Completer<void>();
      final cubit = RentalInventoryMutationCubit(capabilities: offersEnabled);
      addTearDown(cubit.close);
      AccountSession.begin('owner-a');
      addTearDown(AccountSession.end);
      var saved = false;
      final request = cubit.updateOffer(
        selection: selection,
        availability: 'rented',
        onSuccess: (_) => saved = true,
      );
      AccountSession.begin('owner-b');
      repository.pauseRead!.complete();
      await request;
      expect(saved, isFalse);
      expect(repository.requests.map((r) => r.httpRequestType), [
        HttpRequestType.get,
      ]);
    },
  );
  test('owner acceptance updates the appointment only', () async {
    final before = repository.property.rentalInventory;
    final cubit = OwnerVisitStatusCubit();
    addTearDown(cubit.close);
    var accepted = false;
    await cubit.acceptVisitRequest(
      requestId: 'visit-a',
      onSuccess: () => accepted = true,
    );
    expect(accepted, isTrue);
    final request = repository.requests.single;
    expect(request.api, 'properties/owner/visits/requests/visit-a/accept/');
    expect(request.body, isNull);
    expect(repository.property.rentalInventory, before);
    expect(
      repository.property.rentalInventory!.offers.single.isAvailable,
      isTrue,
    );
  });
  test(
    'favorites cannot save or remove an offer through legacy requests',
    () async {
      final cubit = PropertySaveCubit();
      addTearDown(cubit.close);
      var failed = false;
      await cubit.saveProperty(
        propertyId: 'property-a',
        hasRentalOffers: true,
        selection: selection,
        onError: (_) => failed = true,
      );
      expect(failed, isTrue);
      expect(repository.requests, isEmpty);
      await cubit.unsaveProperty(
        propertyId: 'property-a',
        hasRentalOffers: true,
        onError: (_) {},
      );
      expect(repository.requests, isEmpty);
    },
  );
  test(
    'supported favorites save and remove precisely the selected offer',
    () async {
      final cubit = PropertySaveCubit(capabilities: offersEnabled);
      addTearDown(cubit.close);
      await cubit.saveProperty(
        propertyId: 'property-a',
        hasRentalOffers: true,
        selection: selection,
        onError: (_) {},
      );
      expect(cubit.state.isSuccess, isTrue);
      expect(repository.requests.single.body, {'offer_id': bedOffer.id});
      await cubit.unsaveProperty(
        propertyId: 'property-a',
        hasRentalOffers: true,
        selection: selection,
        onError: (_) {},
      );
      expect(repository.requests.last.httpRequestType, HttpRequestType.delete);
      expect(repository.requests.last.body, {'offer_id': bedOffer.id});
    },
  );
  test(
    'inventory actions require capabilities and fresh server permissions',
    () async {
      final disabled = RentalInventoryMutationCubit();
      addTearDown(disabled.close);
      await disabled.updateOffer(
        selection: selection,
        availability: 'rented',
        onSuccess: (_) => fail('Unexpected success'),
      );
      expect(repository.requests, isEmpty);
      repository.property = rentalProperty(
        inventory: rentalInventory(
          offers: [bedOffer.copyWith(canSetAvailability: false)],
        ),
      );
      final enabled = RentalInventoryMutationCubit(capabilities: offersEnabled);
      addTearDown(enabled.close);
      await enabled.updateOffer(
        selection: selection,
        availability: 'rented',
        onSuccess: (_) => fail('Unexpected success'),
      );
      expect(repository.requests, hasLength(1));
      expect(repository.requests.single.httpRequestType, HttpRequestType.get);
    },
  );
  test(
    'one confirmed rented bed leaves other non-overlapping offers available',
    () async {
      final second = bedOffer.copyWith(id: 'offer-bed-a2', bedRef: 'bed-a2');
      repository.property = rentalProperty(
        inventory: rentalInventory(offers: [bedOffer, second]),
      );
      repository.applyOfferChanges = true;
      final cubit = RentalInventoryMutationCubit(capabilities: offersEnabled);
      addTearDown(cubit.close);
      PropertyDetailsModel? saved;
      await cubit.updateOffer(
        selection: selection,
        availability: 'rented',
        onSuccess: (property) => saved = property,
      );
      expect(
        saved?.rentalInventory?.offerById(bedOffer.id)?.availability,
        'rented',
      );
      expect(saved?.rentalInventory?.offerById(second.id)?.isAvailable, isTrue);
      expect(repository.requests.last.api, 'properties/property-a/');
      expect(repository.requests.last.httpRequestType, HttpRequestType.patch);
      expect(
        repository.requests.any((request) => request.api.contains('/delete/')),
        isFalse,
      );
    },
  );
}

class _RentalRepository implements BaseRepository {
  final List<CrudBaseParmas> requests = [];
  PropertyDetailsModel property = rentalProperty(inventory: rentalInventory());
  bool failWrites = false, cachedReads = false, applyOfferChanges = false;
  Completer<void>? pauseRead;
  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    requests.add(params);
    if (params.httpRequestType == HttpRequestType.get && pauseRead != null) {
      await pauseRead!.future;
    }
    if (failWrites && params.httpRequestType != HttpRequestType.get) {
      return Error(ServerFailure('inventory_conflict'));
    }
    Map<String, dynamic> response;
    if (params.api.endsWith('/save/') || params.api.endsWith('/unsave/')) {
      response = {
        'offer_id': params.body?['offer_id'],
        'is_saved': params.httpRequestType == HttpRequestType.post,
      };
    } else if (params.api == 'properties/property-a/visits/') {
      response = {'id': 'visit-a', 'offer_id': params.body?['offer_id']};
    } else if (params.api.contains('/accept/')) {
      response = {'status': 'accepted'};
    } else {
      if (applyOfferChanges &&
          params.httpRequestType == HttpRequestType.patch) {
        final data = jsonDecode(params.body!['rental_inventory']) as Map;
        final incoming = data['offers'] as List;
        final inventory = property.rentalInventory!;
        property = property.copyWith(
          rentalInventory: inventory.copyWith(
            offers: [
              for (final old in inventory.offers)
                old.copyWith(
                  availability: incoming.firstWhere(
                    (item) => item['id'] == old.id,
                  )['availability'],
                  archived: incoming.firstWhere(
                    (item) => item['id'] == old.id,
                  )['archived'],
                ),
            ],
          ),
        );
      }
      response = property.toJson();
    }
    try {
      return Success(
        BaseModel<T>(
          key: cachedReads && params.httpRequestType == HttpRequestType.get
              ? 'fromCache'
              : '',
          msg: '',
          data: params.mapper!(response),
        ),
      );
    } catch (error) {
      return Error(ServerFailure(error.toString()));
    }
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}
