from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app')
p=root/'lib/features/tenant/home/presentation/widgets/tenant_search_results/amenity_row.dart'
s=p.read_text().replace('}.take(2);','}.take(3);')
s=s.replace("label: item.hasRentalOffers\n                ? '${LocaleKeys.rentalParentPropertyArea}: ${item.area}'\n                : '${item.area} ${LocaleKeys.tenantSearchResultsSquareMeters}',", "label: '${LocaleKeys.ownerAnalyticsInterestArea}: ${item.area} ${LocaleKeys.tenantSearchResultsSquareMeters}',")
p.write_text(s)
p=root/'test/property_amenity_row_test.dart'
s=p.read_text().replace("import 'package:flutter_test/flutter_test.dart';", "import 'package:flutter_test/flutter_test.dart';\nimport 'package:melos_core/config/language/locale_keys.g.dart';")
s=s.replace('area and at most two features fit narrow widths','short area label and three features fit narrow widths')
s=s.replace("                            'elevator',", "                            'elevator',\n                            'garage',")
s=s.replace('expect(find.byIcon(Icons.elevator_outlined), findsNothing);','expect(find.byIcon(Icons.elevator_outlined), findsOneWidget);')
s=s.replace('expect(find.byType(Icon), findsNWidgets(3));', "expect(find.byType(Icon), findsNWidgets(4));\n      expect(find.text('${LocaleKeys.ownerAnalyticsInterestArea}: 180 ${LocaleKeys.tenantSearchResultsSquareMeters}'), findsOneWidget);")
p.write_text(s)
