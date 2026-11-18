# feature_architecture_test.dart

Status: reproduced by the broad suite; root cause requires classification.

Run from the relevant Flutter package:

```sh
flutter test --no-pub --timeout 60s --reporter expanded test/feature_architecture_test.dart
```

## MOB-8c5f7e2bf78b

Sokoun feature architecture presentation uses translations and semantic colors

Result: `failure`.

```text
Expected: empty
  Actual: [
            'lib/features/main_view/presentation/widgets/home_navigation_item.dart has raw colors',
            'lib/features/tenant/home/presentation/widgets/tenant_search/search_chip.dart has raw colors'
          ]
lib/features/main_view/presentation/widgets/home_navigation_item.dart has raw colors
lib/features/tenant/home/presentation/widgets/tenant_search/search_chip.dart has raw colors

package:matcher                                     expect
package:flutter_test/src/widget_tester.dart 473:18  expect
test/feature_architecture_test.dart 221:7           main.<fn>.<fn>

```
