import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/shared/recovery/data/preference_write_queue.dart';
import 'package:sokoun_app/features/tenant/home/data/models/favorite_target.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/favorite_coordinator.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/favorite_projection.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';

Result<BaseModel<bool>, Failure> success(bool value) =>
    Success(BaseModel(key: '', msg: '', data: value));
void main() {
  setUp(() async {
    AccountSession.end();
    await AccountSession.finishCleanup();
    AccountSession.begin('alice');
  });
  tearDown(() async {
    AccountSession.end();
    await AccountSession.finishCleanup();
  });

  test(
    'a late Saved list cannot resurrect a removed offer or hide its sibling',
    () async {
      final coordinator = FavoriteCoordinator.instance;
      const target = FavoriteTarget('property-1', 'offer-1');
      coordinator.seed(target, true);
      await coordinator.request(
        target: target,
        desired: false,
        send: (_) async => success(false),
      );
      final stale = const FavoritePropertyContent.initial().copyWith(
        id: 'property-1',
        savedOffers: [
          const RentalSelection.initial().copyWith(
            propertyId: 'property-1',
            offerId: 'offer-1',
          ),
          const RentalSelection.initial().copyWith(
            propertyId: 'property-1',
            offerId: 'offer-2',
          ),
        ],
      );
      final visible = FavoriteProjection.apply([stale]);
      expect(visible.single.savedOffers.map((offer) => offer.offerId), [
        'offer-2',
      ]);
      expect(
        FavoriteProjection.apply([
          stale.copyWith(savedOffers: [stale.savedOffers.first]),
        ]),
        isEmpty,
      );
    },
  );

  test(
    'unsave and rapid Undo serialize and converge on the confirmed saved state',
    () async {
      final coordinator = FavoriteCoordinator();
      const target = FavoriteTarget('property-1');
      coordinator.seed(target, true);
      final first = Completer<Result<BaseModel<bool>, Failure>>();
      final sent = <bool>[];
      Future<Result<BaseModel<bool>, Failure>> send(bool value) {
        sent.add(value);
        return sent.length == 1 ? first.future : Future.value(success(value));
      }

      final remove = coordinator.request(
        target: target,
        desired: false,
        send: send,
      );
      await Future<void>.delayed(Duration.zero);
      final undo = coordinator.request(
        target: target,
        desired: true,
        send: send,
      );
      expect(coordinator.value(target)?.desired, isTrue);
      expect(sent, [false]);
      first.complete(success(false));
      await Future.wait([remove, undo]);
      expect(sent, [false, true]);
      expect(coordinator.value(target)?.confirmed, isTrue);
      expect(coordinator.value(target)?.busy, isFalse);
      await coordinator.close();
    },
  );

  test(
    'an old failure and an old read cannot roll back newer favorite intent',
    () async {
      final coordinator = FavoriteCoordinator();
      const target = FavoriteTarget('property-1');
      coordinator.seed(target, true);
      final first = Completer<Result<BaseModel<bool>, Failure>>();
      final remove = coordinator.request(
        target: target,
        desired: false,
        send: (_) => first.future,
      );
      await Future<void>.delayed(Duration.zero);
      final undo = coordinator.request(
        target: target,
        desired: true,
        send: (_) => Future.value(success(true)),
      );
      first.complete(const Error(Failure('Unsave failed')));
      await Future.wait([remove, undo]);
      coordinator.reconcile(target, false, 0);
      expect(coordinator.value(target)?.confirmed, isTrue);
      expect(coordinator.value(target)?.desired, isTrue);
      await coordinator.close();
    },
  );

  test('latest failure rolls back only its exact property and offer', () async {
    final coordinator = FavoriteCoordinator();
    const one = FavoriteTarget('property-1', 'offer-1');
    const other = FavoriteTarget('property-1', 'offer-2');
    coordinator.seed(one, false);
    coordinator.seed(other, true);
    final result = await coordinator.request(
      target: one,
      desired: true,
      send: (_) async => const Error(Failure('Unavailable')),
    );
    expect(result.isError(), isTrue);
    expect(coordinator.value(one)?.desired, isFalse);
    expect(coordinator.value(other)?.desired, isTrue);
    await coordinator.close();
  });

  test('a late favorite result cannot enter the next account', () async {
    final coordinator = FavoriteCoordinator();
    const target = FavoriteTarget('property-1');
    coordinator.seed(target, false);
    final pending = Completer<Result<BaseModel<bool>, Failure>>();
    final result = coordinator.request(
      target: target,
      desired: true,
      send: (_) => pending.future,
    );
    await Future<void>.delayed(Duration.zero);
    AccountSession.end();
    await AccountSession.finishCleanup();
    AccountSession.begin('bob');
    pending.complete(success(true));
    await result;
    expect(coordinator.value(target), isNull);
    await coordinator.close();
  });

  test(
    'preference toggles serialize and an earlier failure preserves the latest value',
    () async {
      final queue = PreferenceWriteQueue();
      final first = Completer<bool>();
      final sent = <bool>[];
      Future<bool> send(String _, bool value) {
        sent.add(value);
        return first.future;
      }

      final off = queue.update(
        key: 'visit_notifications',
        baseline: true,
        value: false,
        send: send,
      );
      await Future<void>.delayed(Duration.zero);
      final on = queue.update(
        key: 'visit_notifications',
        baseline: true,
        value: true,
        send: send,
      );
      first.complete(false);
      expect(await off, isTrue);
      expect(await on, isTrue);
      expect(sent, [false]);
      expect(queue.valueFor('visit_notifications', false), isTrue);
    },
  );

  test(
    'a failed final preference save is reported as failed and rolls back',
    () async {
      final queue = PreferenceWriteQueue();
      expect(
        await queue.update(
          key: 'owner_messages',
          baseline: true,
          value: false,
          send: (_, _) async => false,
        ),
        isFalse,
      );
      expect(queue.valueFor('owner_messages', false), isTrue);
    },
  );
}
