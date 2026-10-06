import 'package:flutter_test/flutter_test.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/decision_tools_data.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/models/decision_notebook.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/models/property_cost_breakdown.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/cubits/decision_tools_cubit.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/visits/data/visit_schedule_rules.dart';

void main() {
  test('costs distinguish absent terms from a stated zero deposit', () {
    const property = PropertyDetailsModel.initial();
    expect(PropertyCostBreakdown.fromProperty(property).knownSubtotal, isNull);
    final noDeposit = PropertyCostBreakdown.fromProperty(
      property.copyWith(
        price: '18000',
        pricePeriod: 'monthly',
        deposit: 'none',
      ),
    );
    expect(noDeposit.deposit, 0);
    expect(noDeposit.knownSubtotal, 18000);
    final deposit = PropertyCostBreakdown.fromProperty(
      property.copyWith(
        price: '18000',
        pricePeriod: 'monthly',
        deposit: 'two_months',
      ),
    );
    expect(deposit.knownSubtotal, 54000);
    expect(PropertyCostBreakdown.fromJson(deposit.toJson()), deposit);
    expect(
      PropertyCostBreakdown.fromProperty(
        property.copyWith(
          price: '1000',
          pricePeriod: 'daily',
          deposit: 'one_month',
        ),
      ).deposit,
      isNull,
    );
    expect(
      PropertyCostBreakdown.fromProperty(
        property.copyWith(price: '-1', deposit: '-10'),
      ).knownSubtotal,
      isNull,
    );
  });

  test('appointment rules reject malformed and past times in Egypt time', () {
    final instant = DateTime.utc(2026, 6, 15, 11);
    expect(VisitScheduleRules.now(instant: instant).hour, 14);
    expect(
      VisitScheduleRules.isFuture('2026-06-15', '14:00:00', instant: instant),
      isFalse,
    );
    expect(
      VisitScheduleRules.isFuture('2026-06-15', '14:01:00', instant: instant),
      isTrue,
    );
    expect(
      VisitScheduleRules.isFuture('2026-02-31', '15:00:00', instant: instant),
      isFalse,
    );
    expect(
      VisitScheduleRules.isFuture('2026-06-16', '24:00:00', instant: instant),
      isFalse,
    );
    expect(
      VisitScheduleRules.isFuture('2026-06-16', '15:99:00', instant: instant),
      isFalse,
    );
  });

  test(
    'rapid mutations preserve every property and enforce comparison capacity',
    () async {
      final store = _Store();
      final cubit = DecisionToolsCubit(accountId: 'alice', store: store);
      await cubit.load();
      await Future.wait([
        for (final id in ['a', 'b', 'c'])
          cubit.toggleComparison(PropertyDecision(propertyId: id, title: id)),
      ]);
      expect(cubit.state.comparisonIds, ['a', 'b', 'c']);
      expect(
        await cubit.toggleComparison(
          const PropertyDecision(propertyId: 'd', title: 'D'),
        ),
        isFalse,
      );
      await cubit.saveDecision(
        const PropertyDecision(
          propertyId: 'b',
          title: 'B',
          list: 'Near work',
          note: 'Check daylight',
          checkedItems: {'water'},
        ),
      );
      await cubit.toggleComparison(
        const PropertyDecision(propertyId: 'b', title: 'B'),
      );
      expect(cubit.state.decisionFor('b', '').note, 'Check daylight');
      expect(
        await cubit.toggleComparison(
          const PropertyDecision(propertyId: 'd', title: 'D'),
        ),
        isTrue,
      );
      final restarted = DecisionToolsCubit(accountId: 'alice', store: store);
      final otherAccount = DecisionToolsCubit(accountId: 'bob', store: store);
      await restarted.load();
      await otherAccount.load();
      expect(restarted.state.comparisonIds, ['a', 'c', 'd']);
      expect(restarted.state.decisionFor('b', '').checkedItems, {'water'});
      expect(otherAccount.state, const DecisionNotebook.initial());
      expect(
        DecisionToolsData.keyFor('alice'),
        isNot(DecisionToolsData.keyFor('bob')),
      );
      await cubit.close();
      await restarted.close();
      await otherAccount.close();
    },
  );

  test(
    'saved search retains all filters and replaces a duplicate query',
    () async {
      final cubit = DecisionToolsCubit(accountId: 'alice', store: _Store());
      await cubit.load();
      const filters = PropertySearchFilters.initial(
        search: 'Maadi',
        city: 'Cairo',
        district: 'Degla',
        priceMin: '1000',
        priceMax: '20000',
        pricePeriod: 'monthly',
        propertyType: 'apartment',
        amenities: {'wifi', 'near_metro'},
        smokingAllowed: 'false',
        bedrooms: '2',
        page: 4,
      );
      await cubit.saveSearch('Near work', filters);
      await cubit.saveSearch('Updated name', filters.copyWith(page: 1));
      final saved = DecisionNotebook.fromJson(cubit.state.toJson());
      expect(saved.searches, hasLength(1));
      expect(saved.searches.single.name, 'Updated name');
      expect(saved.searches.single.filters, filters.copyWith(page: 1));
      await cubit.close();
    },
  );

  test(
    'failed storage preserves the previous notebook and permits retry',
    () async {
      final store = _Store();
      final cubit = DecisionToolsCubit(accountId: 'alice', store: store);
      await cubit.load();
      store.fail = true;
      const decision = PropertyDecision(
        propertyId: 'a',
        title: 'A',
        note: 'Keep this draft',
      );
      await expectLater(cubit.saveDecision(decision), throwsStateError);
      expect(cubit.state.properties, isEmpty);
      store.fail = false;
      await cubit.saveDecision(decision);
      expect(cubit.state.properties.single, decision);
      await cubit.close();
    },
  );
}

class _Store implements DecisionToolsStore {
  final Map<String, DecisionNotebook> notebooks = {};
  bool fail = false;
  @override
  Future<DecisionNotebook> read(String accountId) async =>
      notebooks[accountId] ?? const DecisionNotebook.initial();
  @override
  Future<void> write(String accountId, DecisionNotebook notebook) async {
    if (fail) throw StateError('Storage full');
    notebooks[accountId] = DecisionNotebook.fromJson(notebook.toJson());
  }
}
