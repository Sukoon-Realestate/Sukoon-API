# Behavioral Validation Scenarios

Use these isolated cases when maintaining the skill. They validate decision rules, not exact report wording. Do not load this file for an ordinary feature assessment.

## Case 1: Runtime Fake Data

### Evidence

```dart
Future<List<Order>> loadOrders() async {
  try {
    return await api.fetchOrders();
  } catch (_) {
    return const [Order(id: 'sample', total: 120)];
  }
}
```

No API contract or repository documentation is available in the fixture.

### Expected behavior

- Identify a confirmed runtime fallback that conceals failure with fabricated user-visible data.
- Explain its execution path and impact; do not merely flag the numeric or string literal.
- Do not invent a replacement endpoint or response fields.
- Classify the replacement source as `Not verified` unless the fixture proves it is missing.
- Treat false successful order data as a release blocker and produce `Not ready`.

## Case 2: Mock Data Confined to Tests

### Evidence

```dart
// test/orders_cubit_test.dart
final fakeOrders = [const Order(id: 'fixture-1', total: 10)];
when(() => repository.loadOrders()).thenAnswer((_) async => fakeOrders);
```

The test file is not imported by runtime code.

### Expected behavior

- Classify the list as a legitimate test fixture, not a runtime placeholder defect.
- Do not demand replacement with a real service in the unit test.
- Do not declare the feature ready merely because this test passes; assess requirements, reachability, integration, states, and remaining verification.

## Case 3: Registered but Unreachable Screen

### Evidence

The confirmed requirement says a signed-in customer can open Loyalty from the home screen. `LoyaltyScreen` has a registered generated route, but the home destinations, buttons, deep links, and role menus contain no path to that route. Inspection of the generated route registry finds registration only.

### Expected behavior

- Conclude that route registration alone does not make the feature accessible.
- Cite the confirmed entry-point requirement and traced navigation, not only a text search.
- Record a confirmed release blocker and produce `Not ready`.
- If the requirement were absent, report the intended entry point as unresolved instead of automatically calling the disconnected screen a blocker.

## Case 4: Test Cannot Execute

### Evidence

The only end-to-end test requires a device, a customer account, and a sandbox service credential that are unavailable. Static analysis and unit tests pass. No other blocker is confirmed.

### Expected behavior

- Record the end-to-end check as `Not verified`, explain the missing prerequisites, and provide a manual test sheet.
- Distinguish unit-test mocks and static analysis from real-service verification.
- Produce `Verification incomplete` when the unexecuted journey is critical to establishing readiness.
- Do not infer readiness from the passing unit tests or analysis.

## Mode and Source Invariants

- In `Review`, propose fixes and missing tests without editing application code, tests, or configuration.
- In `Fix & Verify`, inspect before editing, stay feature-scoped, add risk-based tests, and separate resolved findings from remaining gaps.
- Never invent endpoints, schemas, business values, roles, platforms, or flavors.
- Never claim that any outcome proves the feature has no defects.
