import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_content.dart';
import 'package:sokoun_app/features/tenant/home/data/tenant_search_data.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/tenant_recent_searches_cubit.dart';

void main() {
  late _HistorySource source;
  late TenantRecentSearchesCubit cubit;
  setUp(() async {
    await injector.reset();
    source = _HistorySource();
    injector.registerSingleton<TenantSearchDataSource>(source);
    cubit = TenantRecentSearchesCubit();
  });
  tearDown(() async {
    await cubit.close();
    await injector.reset();
  });

  test(
    'normalizes duplicate queries and retains the five most recent',
    () async {
      await cubit.addRecentSearch('  Maadi  ');
      await cubit.addRecentSearch('Nasr    City');
      await cubit.addRecentSearch('MAADI');
      expect(cubit.state.map((e) => e.title), ['MAADI', 'Nasr City']);
      for (int i = 0; i < 6; i++) {
        await cubit.addRecentSearch('Area $i');
      }
      expect(source.saved.map((e) => e.title), [
        'Area 5',
        'Area 4',
        'Area 3',
        'Area 2',
        'Area 1',
      ]);
    },
  );

  test('removal and undo persist and survive reopening', () async {
    await cubit.addRecentSearch('Maadi');
    await cubit.addRecentSearch('Zamalek');
    final snapshot = cubit.state;
    await cubit.removeRecentSearch(snapshot.last);
    expect(source.saved.map((e) => e.title), ['Zamalek']);
    await cubit.restoreRecentSearches(snapshot);
    await cubit.clearRecentSearches();
    expect(source.saved, isEmpty);
    await cubit.restoreRecentSearches(snapshot);
    final reopened = TenantRecentSearchesCubit()..loadRecentSearches();
    expect(reopened.state, snapshot);
    await reopened.close();
  });

  test(
    'rapid mutations write in order and undo retains newer searches',
    () async {
      source.pending = Completer<void>();
      final first = cubit.addRecentSearch('Maadi');
      final clear = cubit.clearRecentSearches();
      final last = cubit.addRecentSearch('Zamalek');
      await Future<void>.delayed(Duration.zero);
      expect(source.writeCount, 1);
      source.pending!.complete();
      await Future.wait([first, clear, last]);
      expect(source.saved.map((e) => e.title), ['Zamalek']);
      await cubit.restoreRecentSearches(const [
        RecentSearchContent(title: 'Maadi'),
      ]);
      expect(source.saved.map((e) => e.title), ['Zamalek', 'Maadi']);
    },
  );

  test(
    'a failed save restores the visible history and the next operation can retry',
    () async {
      await cubit.addRecentSearch('Maadi');
      source.fail = true;
      expect(await cubit.clearRecentSearches(), isFalse);
      expect(cubit.state.single.title, 'Maadi');
      source.fail = false;
      expect(await cubit.clearRecentSearches(), isTrue);
      expect(source.saved, isEmpty);
    },
  );

  test('queued failures restore the last persisted history', () async {
    await cubit.addRecentSearch('Maadi');
    source.pending = Completer<void>();
    source.fail = true;
    final first = cubit.clearRecentSearches();
    final second = cubit.addRecentSearch('Zamalek');
    source.pending!.complete();
    expect(await Future.wait([first, second]), [false, false]);
    expect(cubit.state, source.saved);
    expect(cubit.state.single.title, 'Maadi');
  });
}

class _HistorySource implements TenantSearchDataSource {
  List<RecentSearchContent> saved = [];
  int writeCount = 0;
  bool fail = false;
  Completer<void>? pending;
  @override
  int get maxRecentSearches => 5;
  @override
  List<RecentSearchContent> getRecentSearches() => saved;
  @override
  Future<void> saveRecentSearches(List<RecentSearchContent> searches) async {
    writeCount++;
    await pending?.future;
    if (fail) throw StateError('Storage unavailable');
    saved = List.of(searches);
  }
}
