import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_picker.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';
import '../../data/models/comparison_property.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import '../../data/models/property_cost_breakdown.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_price_period.dart';
import 'property_cost_card.dart';

class ComparisonTable extends StatefulWidget {
  const ComparisonTable({
    super.key,
    required this.properties,
    required this.onRemove,
    this.savedTitles = const {},
  });
  final List<ComparisonProperty> properties;
  final ValueChanged<String> onRemove;
  final Map<String, String> savedTitles;
  @override
  State<ComparisonTable> createState() => _ComparisonTableState();
}

class _ComparisonTableState extends State<ComparisonTable> {
  final ValueNotifier<Map<String, String>> _offers = ValueNotifier(const {});
  List<ComparisonProperty> get properties => widget.properties;
  ValueChanged<String> get onRemove => widget.onRemove;
  Map<String, String> get savedTitles => widget.savedTitles;
  RentalSelection? _selectionFor(ComparisonProperty item) {
    final inventory = item.property.rentalInventory;
    final offer = inventory?.offerById(_offers.value[item.propertyId] ?? '');
    return offer == null
        ? null
        : RentalSelection.fromOffer(
            propertyId: item.propertyId,
            inventory: inventory!,
            offer: offer,
          );
  }

  @override
  void dispose() {
    _offers.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) =>
      ValueListenableBuilder<Map<String, String>>(
        valueListenable: _offers,
        builder: (_, _, _) => _build(context),
      );
  Widget _build(BuildContext context) {
    final rows = <(String, String Function(ComparisonProperty))>[
      (
        LocaleKeys.rentalOfferedAccommodation,
        (item) => _selectionFor(item) != null
            ? RentalOfferLabels.accommodation(_selectionFor(item)!)
            : item.property.hasRentalOffers
            ? LocaleKeys.rentalSelectOffer
            : LocaleKeys.rentalLegacyScope,
      ),
      (
        LocaleKeys.freeRent,
        (item) => _selectionFor(item) != null
            ? RentalOfferLabels.price(_selectionFor(item)!)
            : item.property.rentalInventory != null
            ? LocaleKeys.rentalSelectForPrice
            : '${item.property.formattedPrice} ${item.property.pricePeriodLabel}',
      ),
      (
        LocaleKeys.freeDeposit,
        (item) =>
            item.property.rentalInventory != null && _selectionFor(item) == null
            ? LocaleKeys.rentalSelectForPrice
            : (_selectionFor(item)?.terms.deposit ?? item.property.deposit)
                  .isEmpty
            ? LocaleKeys.freeAskOwner
            : PropertyDetailsModel.depositLabelFor(
                _selectionFor(item)?.terms.deposit ?? item.property.deposit,
              ),
      ),
      (
        LocaleKeys.ownerAddPropertyMinimumRentalMonths,
        (item) =>
            item.property.rentalInventory != null && _selectionFor(item) == null
            ? LocaleKeys.rentalSelectForPrice
            : (_selectionFor(item)?.terms.minimumMonths ??
                      item.property.rentalPeriod) >
                  0
            ? '${_selectionFor(item)?.terms.minimumMonths ?? item.property.rentalPeriod} ${item.property.rentalPeriodUnitLabel}'
            : LocaleKeys.freeAskOwner,
      ),
      (
        LocaleKeys.ownerAddPropertyType,
        (item) => item.property.propertyTypeLabel,
      ),
      (
        properties.any((item) => item.property.rentalInventory != null)
            ? LocaleKeys.rentalPropertyRooms
            : LocaleKeys.ownerAddPropertyBedrooms,
        (item) => item.property.bedrooms > 0
            ? '${item.property.bedrooms}'
            : LocaleKeys.rentalUnspecified,
      ),
      (
        LocaleKeys.rentalParentPropertyBathrooms,
        (item) => item.property.bathrooms > 0
            ? '${item.property.bathrooms}'
            : LocaleKeys.rentalUnspecified,
      ),
      (
        LocaleKeys.rentalParentPropertyArea,
        (item) => item.property.area > 0
            ? '${item.property.area} ${LocaleKeys.freeSquareMeters}'
            : LocaleKeys.rentalUnspecified,
      ),
      (
        LocaleKeys.rentalSharedSpaces,
        (item) => item.property.amenityLabels.isEmpty
            ? LocaleKeys.freeAskOwner
            : item.property.amenityLabels.join(' • '),
      ),
      (
        LocaleKeys.freeListingVerified,
        (item) => item.property.isVerified
            ? LocaleKeys.freeYes
            : LocaleKeys.freeNotVerified,
      ),
      (
        LocaleKeys.freeOwnerVerified,
        (item) => item.property.isOwnerVerified
            ? LocaleKeys.freeYes
            : LocaleKeys.freeNotVerified,
      ),
      (
        LocaleKeys.freeOwnershipVerified,
        (item) => item.property.isOwnershipVerified
            ? LocaleKeys.freeYes
            : LocaleKeys.freeNotVerified,
      ),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final item in properties)
          if (item.property.rentalInventory != null)
            ExpansionTile(
              title: AppText(item.property.title),
              children: [
                RentalOfferPicker(
                  propertyId: item.propertyId,
                  inventory: item.property.rentalInventory!,
                  selectedId: _offers.value[item.propertyId],
                  onSelected: (id) =>
                      _offers.value = {..._offers.value, item.propertyId: id},
                ),
              ],
            ),
        AppText(LocaleKeys.freeComparisonExplanation),
        const SizedBox(height: 16),
        AppText(LocaleKeys.freeComparisonScroll),
        const SizedBox(height: 8),
        _ComparisonScroll(
          child: Table(
            defaultVerticalAlignment: TableCellVerticalAlignment.top,
            columnWidths: {
              0: const FixedColumnWidth(150),
              for (var index = 0; index < properties.length; index++)
                index + 1: const FixedColumnWidth(230),
            },
            border: TableBorder.all(
              color: context.appColor(AppColors.sokoonBorder),
            ),
            children: [
              TableRow(
                children: [
                  const SizedBox(),
                  for (final item in properties)
                    Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          AppText(
                            item.isAvailable
                                ? item.property.title
                                : savedTitles[item.propertyId]
                                          ?.trim()
                                          .isNotEmpty ==
                                      true
                                ? savedTitles[item.propertyId]!
                                : LocaleKeys.freeListingUnavailable,
                            fontWeight: FontWeight.bold,
                          ),
                          if (item.isCached)
                            AppText(LocaleKeys.freeCachedListing),
                          if (!item.isAvailable &&
                              savedTitles[item.propertyId]?.trim().isNotEmpty ==
                                  true)
                            AppText(LocaleKeys.freeListingUnavailable),
                          if (item.isAvailable)
                            TextButton(
                              onPressed: () => Go.to(
                                PropertyDetailsScreen(
                                  propertyId: item.propertyId,
                                  offerId: _offers.value[item.propertyId],
                                ),
                              ),
                              child: AppText(LocaleKeys.freeOpenListing),
                            ),
                          TextButton.icon(
                            onPressed: () => onRemove(item.propertyId),
                            icon: const Icon(Icons.close, size: 18),
                            label: AppText(LocaleKeys.freeRemove),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
              for (final row in rows)
                TableRow(
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(12),
                      child: AppText(row.$1, fontWeight: FontWeight.w600),
                    ),
                    for (final item in properties)
                      Padding(
                        padding: const EdgeInsets.all(12),
                        child: AppText(
                          item.isAvailable
                              ? row.$2(item)
                              : LocaleKeys.freeListingUnavailable,
                        ),
                      ),
                  ],
                ),
              TableRow(
                children: [
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: AppText(
                      LocaleKeys.freeKnownCosts,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  for (final item in properties)
                    Padding(
                      padding: const EdgeInsets.all(8),
                      child: item.isAvailable
                          ? PropertyCostCard(
                              cost: PropertyCostBreakdown.fromProperty(
                                item.property,
                                selection: _selectionFor(item),
                              ),
                              periodLabel: _selectionFor(item) != null
                                  ? PropertyPricePeriod.fromValue(
                                          _selectionFor(
                                            item,
                                          )!.terms.pricePeriod,
                                        )?.label ??
                                        ''
                                  : item.property.rentalInventory != null
                                  ? ''
                                  : item.property.pricePeriodLabel,
                            )
                          : AppText(LocaleKeys.freeListingUnavailable),
                    ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ComparisonScroll extends StatefulWidget {
  const _ComparisonScroll({required this.child});
  final Widget child;
  @override
  State<_ComparisonScroll> createState() => _ComparisonScrollState();
}

class _ComparisonScrollState extends State<_ComparisonScroll> {
  final ScrollController _controller = ScrollController();
  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scrollbar(
    controller: _controller,
    thumbVisibility: true,
    child: SingleChildScrollView(
      controller: _controller,
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.only(bottom: 16),
      child: widget.child,
    ),
  );
}
