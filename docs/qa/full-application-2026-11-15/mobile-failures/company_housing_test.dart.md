# company_housing_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/company_housing_test.dart
```

## MOB-82a48ab7bf2d

new child receipt is independent of parent optimistic revision

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: 'item'
  Actual: 'failed'
   Which: is different.
          Expected: item
            Actual: failed
                    ^
           Differ at offset 0

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_housing_test.dart 215:7                main.<fn>

```

## MOB-9a3ab414698d

company details are erased immediately on account cleanup

Result: `failure`.

```text
[🌎 Easy Localization] [WARNING] Localization key [planning_unavailable] not found
Expected: 'Private company'
  Actual: ''
   Which: is different. Both strings start the same, but the actual value is missing the following trailing characters: Private co ...

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/company_housing_test.dart 228:5                main.<fn>

```
