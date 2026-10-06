import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_price_period.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import '../../data/models/listing_ai_facts.dart';

class ListingAiFactsView extends StatelessWidget {
  const ListingAiFactsView({super.key, required this.facts});
  final ListingAiFacts facts;
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(facts.title, fontWeight: FontWeight.bold),
          AppText(facts.description),
          AppText('${facts.governorate} ${facts.district}'),
          if (facts.propertyType.isNotEmpty)
            AppText(
              '${LocaleKeys.ownerAddPropertyType} ${PropertyDetailsModel.propertyTypeLabelFor(facts.propertyType)}',
            ),
          if (facts.price.isNotEmpty)
            AppText(
              '${LocaleKeys.freeRent} ${facts.price} ${PropertyPricePeriod.fromValue(facts.pricePeriod)?.label ?? ''}',
            ),
          if (facts.deposit.isNotEmpty)
            AppText(
              '${LocaleKeys.freeDeposit} ${PropertyDetailsModel.depositLabelFor(facts.deposit)}',
            ),
          if (facts.bedrooms > 0)
            AppText('${LocaleKeys.ownerAddPropertyBedrooms} ${facts.bedrooms}'),
          if (facts.bathrooms > 0)
            AppText(
              '${LocaleKeys.ownerAddPropertyBathrooms} ${facts.bathrooms}',
            ),
          AppText('${LocaleKeys.ownerAddPropertySpace} ${facts.space}'),
        ],
      ),
    ),
  );
}
