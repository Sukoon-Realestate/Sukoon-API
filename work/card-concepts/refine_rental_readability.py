from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app')
p=root/'lib/features/shared/rental_offers/presentation/widgets/rental_selection_panel.dart'
s=p.read_text().replace("import 'rental_accommodation_details.dart';", "import 'rental_accommodation_details.dart';\nimport 'rental_price_text.dart';")
a=s.index('            AppText(\n              RentalOfferLabels.price(selection),')
b=s.index('            if (!historical)',a)
s=s[:a]+'''            RentalPriceText(
              price: RentalOfferLabels.pricePresentation(selection),
              amountSize: 20,
            ),
'''+s[b:]
s=s.replace('title: LocaleKeys.rentalOfferDescription,', '''title: selection.scope == RentalScope.entireProperty
                    ? LocaleKeys.rentalPropertyDescription
                    : LocaleKeys.rentalOfferDescription,''')
s=s.replace('title: LocaleKeys.rentalRules,','title: LocaleKeys.rentalHouseRules,')
p.write_text(s)
p=root/'test/rental_selection_readability_test.dart'
s=p.read_text().replace('LocaleKeys.rentalOfferDescription','LocaleKeys.rentalPropertyDescription').replace('LocaleKeys.rentalRules','LocaleKeys.rentalHouseRules')
p.write_text(s)
