import 'dart:async';
import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/shared/recovery/data/private_recovery_data.dart';
import 'package:sokoun_app/features/shared/recovery/data/recovery_scope.dart';
import 'package:sokoun_app/features/shared/recovery/presentation/cubits/draft_cubit.dart';

PrivateDraftStore<String> store(
  String account,
  String environment, {
  RecoveryStorage storage = const ProtectedRecoveryStorage(),
}) => PrivateDraftStore(
  scope: () async => RecoveryScope(
    environment: environment,
    accountId: account,
    flow: 'review',
    entityId: 'visit-1',
  ),
  encode: (value) => {'comment': value},
  decode: (json) => json['comment'] as String,
  storage: storage,
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
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
    'protected draft survives reopening and isolates account and environment',
    () async {
      await store('alice', 'prod').write('My unfinished review');
      expect(
        (await store('alice', 'prod').read())?.value,
        'My unfinished review',
      );
      expect(await store('alice', 'dev').read(), isNull);
      expect(await store('bob', 'prod').read(), isNull);
      expect(
        (await SecureStorage.readAll()).values.any(
          (value) => value.contains('My unfinished review'),
        ),
        isTrue,
      );
    },
  );

  test(
    'logout deletes protected records and late old-session saves cannot recreate them',
    () async {
      final previous = store('alice', 'prod');
      await previous.write('Private note');
      AccountSession.end();
      await AccountSession.finishCleanup();
      AccountSession.begin('bob');
      expect(await previous.read(), isNull);
      await expectLater(previous.write('Late write'), throwsStateError);
      expect(
        (await SecureStorage.readAll()).values.any(
          (value) => value.contains('Private note'),
        ),
        isFalse,
      );
      expect(await store('bob', 'prod').read(), isNull);
    },
  );

  test(
    'a slow save cannot overwrite the newest input and both writes finish in order',
    () async {
      final storage = _Storage()..hold = Completer<void>();
      final cubit = DraftCubit(store('alice', 'prod', storage: storage));
      cubit.schedule('Old');
      final first = cubit.flush();
      await Future<void>.delayed(Duration.zero);
      cubit.schedule('Newest');
      final second = cubit.flush();
      expect(cubit.state.status, LocalSaveStatus.saving);
      storage.hold!.complete();
      await Future.wait([first, second]);
      expect(cubit.state.status, LocalSaveStatus.saved);
      expect(
        (await store('alice', 'prod', storage: storage).read())?.value,
        'Newest',
      );
      final payloads = storage.writes
          .where((value) => value.containsKey('value'))
          .toList();
      expect(payloads.map((value) => value['value']['comment']), [
        'Old',
        'Newest',
      ]);
      expect(
        payloads.last['sequence'],
        greaterThan(payloads.first['sequence'] as int),
      );
      await cubit.close();
    },
  );

  test(
    'storage failure remains unsaved until a successful explicit retry',
    () async {
      final storage = _Storage()..fail = true;
      final cubit = DraftCubit(store('alice', 'prod', storage: storage));
      cubit.schedule('Keep my text');
      await cubit.flush();
      expect(cubit.state.status, LocalSaveStatus.failed);
      expect(cubit.state.record, isNull);
      storage.fail = false;
      await cubit.retry();
      expect(cubit.state.status, LocalSaveStatus.saved);
      expect(cubit.state.record?.value, 'Keep my text');
      await cubit.clear();
      await cubit.close();
      expect(await store('alice', 'prod', storage: storage).read(), isNull);
    },
  );

  test('debounced work stops when its session expires', () async {
    final storage = _Storage();
    final cubit = DraftCubit(store('alice', 'prod', storage: storage));
    cubit.schedule('Never send this under Bob');
    AccountSession.end();
    await AccountSession.finishCleanup();
    AccountSession.begin('bob');
    await cubit.flush();
    await cubit.close();
    expect(storage.writes, isEmpty);
  });
}

class _Storage implements RecoveryStorage {
  final Map<String, String> records = {};
  final List<Map<String, dynamic>> writes = [];
  Completer<void>? hold;
  bool fail = false;
  @override
  Future<String?> read(String key) async => records[key];
  @override
  Future<void> delete(String key) async {
    records.remove(key);
  }

  @override
  Future<void> write(String key, String value) async {
    if (fail) throw StateError('Disk full');
    if (hold != null) await hold!.future;
    writes.add(jsonDecode(value) as Map<String, dynamic>);
    records[key] = value;
  }
}
