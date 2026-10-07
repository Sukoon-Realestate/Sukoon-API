import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_price_period.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_scope.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'rental_home_section.dart';

class RentalHomeSections extends StatefulWidget {
  const RentalHomeSections({
    super.key,
    this.refreshGeneration = 0,
    this.capabilities = RentalOfferCapabilities.configured,
  });

  final int refreshGeneration;
  final RentalOfferCapabilities capabilities;

  @override
  State<RentalHomeSections> createState() => _RentalHomeSectionsState();
}

class _RentalHomeSectionsState extends State<RentalHomeSections> {
  final ValueNotifier<PropertyPricePeriod> _period = ValueNotifier(
    PropertyPricePeriod.monthly,
  );

  @override
  void dispose() {
    _period.dispose();
    super.dispose();
  }

  Widget _section(RentalScope scope, PropertyPricePeriod period) {
    // Replaces the query owner, closing its Cubit on filter changes/refresh.
    final queryResetKey = (scope, period, widget.refreshGeneration);
    return RentalHomeSection(
      key: ValueKey(queryResetKey),
      scope: scope,
      period: period,
      capabilities: widget.capabilities,
    );
  }

  @override
  Widget build(BuildContext context) => !widget.capabilities.canSearch
      ? const SizedBox.shrink()
      : Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppText(
              LocaleKeys.rentalHomeDiscovery,
              style: AppTextStyles.bold16,
            ),
            10.szH,
            AppText(LocaleKeys.rentalHomePricePeriod),
            ValueListenableBuilder<PropertyPricePeriod>(
              valueListenable: _period,
              builder: (context, period, _) => Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Wrap(
                    spacing: 8,
                    runSpacing: 6,
                    children: [
                      for (final choice in PropertyPricePeriod.values)
                        ChoiceChip(
                          label: AppText(choice.label),
                          selected: period == choice,
                          onSelected: (_) => _period.value = choice,
                        ),
                    ],
                  ),
                  12.szH,
                  for (final scope in RentalScope.values)
                    _section(scope, period),
                ],
              ),
            ),
          ],
        );
}
