import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';
import '../../data/models/comparison_property.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import '../../data/models/property_cost_breakdown.dart';
import 'property_cost_card.dart';

class ComparisonTable extends StatelessWidget {
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
  Widget build(BuildContext context) {
    final rows = <(String, String Function(ComparisonProperty))>[
      (
        LocaleKeys.freeRent,
        (item) =>
            '${item.property.formattedPrice} ${item.property.pricePeriodLabel}',
      ),
      (
        LocaleKeys.freeDeposit,
        (item) => item.property.deposit.isEmpty
            ? LocaleKeys.freeAskOwner
            : PropertyDetailsModel.depositLabelFor(item.property.deposit),
      ),
      (
        LocaleKeys.ownerAddPropertyMinimumRentalMonths,
        (item) => item.property.rentalPeriod > 0
            ? '${item.property.rentalPeriod} ${item.property.rentalPeriodUnitLabel}'
            : LocaleKeys.freeAskOwner,
      ),
      (
        LocaleKeys.ownerAddPropertyType,
        (item) => item.property.propertyTypeLabel,
      ),
      (
        LocaleKeys.ownerAddPropertyBedrooms,
        (item) => '${item.property.bedrooms}',
      ),
      (
        LocaleKeys.ownerAddPropertyBathrooms,
        (item) => '${item.property.bathrooms}',
      ),
      (
        LocaleKeys.ownerAddPropertySpace,
        (item) =>
            '${item.property.space.isEmpty ? item.property.area : item.property.space} ${LocaleKeys.freeSquareMeters}',
      ),
      (
        LocaleKeys.tenantPropertyDetailsAmenities,
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
                              ),
                              periodLabel: item.property.pricePeriodLabel,
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
