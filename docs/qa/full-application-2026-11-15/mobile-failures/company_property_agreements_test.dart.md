# company_property_agreements_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/company_property_agreements_test.dart
```

## MOB-c8b855e20966

company and exact physical property are requested independently of public offer

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_property_agreements_test.dart 88:5     main.<fn>

```

## MOB-786117115d61

bundle totals and private scope at 320 with doubled text in ar

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_property_agreements_test.dart 88:5     main.<fn>

```

## MOB-aaf5bd9b8c03

bundle totals and private scope at 320 with doubled text in en

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_property_agreements_test.dart 88:5     main.<fn>

```

## MOB-c2b2fe9224c3

switching company cannot carry private terms or a late response

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_property_agreements_test.dart 88:5     main.<fn>

```

## MOB-7651c9681c0e

a company viewing context cannot silently target another selected company

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_property_agreements_test.dart 88:5     main.<fn>

```

## MOB-34fa5545a1b8

invalid property context is hidden: workspace

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_property_agreements_test.dart 88:5     main.<fn>

```

## MOB-0a13275e9777

invalid property context is hidden: followed_at

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_property_agreements_test.dart 88:5     main.<fn>

```

## MOB-d47d787a8026

invalid property context is hidden: blocking_reasons

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_property_agreements_test.dart 88:5     main.<fn>

```

## MOB-bc13f52483f7

invalid property context is hidden: expires_at

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_property_agreements_test.dart 88:5     main.<fn>

```

## MOB-725366e89ba5

invalid property context is hidden: inventory

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: true
  Actual: <false>

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_property_agreements_test.dart 88:5     main.<fn>

```
