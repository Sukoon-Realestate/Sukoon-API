from pathlib import Path
base=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/tenant/favorites/presentation/widgets')
p=base/'favorite_property_card.dart'
s=p.read_text().replace("import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_search_results/amenity.dart';\n", '')
a=s.index('                metadata: Wrap(')
b=s.index('                tags: AppText(', a)
s=s[:a]+'                metadata: FavoritePropertyFacts(item: item),\n'+s[b:]
p.write_text(s)
p=base/'favorite_property_summary.dart'
s=p.read_text()
s="""import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_labels.dart';
import '../../data/models/favorites_content.dart';
"""+s
s+='''
class FavoritePropertyFacts extends StatelessWidget {
  const FavoritePropertyFacts({super.key, required this.item});
  final FavoritePropertyContent item;

  @override
  Widget build(BuildContext context) => Wrap(
    spacing: 8,
    runSpacing: 8,
    children: [
      if (item.bedrooms > 0)
        _Fact(
          icon: Icons.bed_outlined,
          value: '${item.bedrooms} ${LocaleKeys.tenantSearchResultsBeds}',
          description: item.hasRentalOffers
            ? LocaleKeys.rentalTotalRooms.replaceAll('{count}', '${item.bedrooms}')
            : '${item.bedrooms} ${LocaleKeys.tenantSearchResultsBeds}',
        ),
      if (item.bathrooms > 0)
        _Fact(
          icon: Icons.bathtub_outlined,
          value: '${item.bathrooms} ${LocaleKeys.tenantSearchResultsBaths}',
          description: item.hasRentalOffers
            ? '${LocaleKeys.rentalParentPropertyBathrooms}: ${item.bathrooms}'
            : '${item.bathrooms} ${LocaleKeys.tenantSearchResultsBaths}',
        ),
      if (item.area > 0)
        _Fact(
          icon: Icons.square_foot_rounded,
          value: '${item.area == item.area.truncateToDouble() ? item.area.toInt() : item.area} ${LocaleKeys.tenantSearchResultsSquareMeters}',
          description: RentalOfferLabels.propertyArea(item.area, hasOffers: item.hasRentalOffers),
        ),
    ],
  );
}

class _Fact extends StatelessWidget {
  const _Fact({required this.icon, required this.value, required this.description});
  final IconData icon;
  final String value, description;
  @override
  Widget build(BuildContext context) => Semantics(
    label: description,
    excludeSemantics: true,
    child: Tooltip(
      message: description,
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerLow,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 16, color: context.appColor(AppColors.sokoonMuted)),
              const SizedBox(width: 5),
              Flexible(child: AppText(value, style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: context.appColor(AppColors.sokoonMuted), height: 1.5))),
            ],
          ),
        ),
      ),
    ),
  );
}
'''
p.write_text(s)
p=Path('/Users/demo23home/code/sukoon/sokoun/docs/ui-refactor/REFERENCE-ADAPTATION.md')
s=p.read_text()+'''\n\n## Saved property card — 2026-11-15\n\n| Existing capability | Revised placement and outcome |\n| --- | --- |\n| Open saved property and image transition | Same image and parent card destination, property/category context and transition ownership. Title and location lead; compact fact chips describe the whole property, with full parent-property wording retained in semantics and tooltips. |\n| Saved offers and missing snapshots | Separate inset offer section; named accommodation, valid snapshot price, capacity/bathroom facts and authoritative availability remain. Missing snapshot copy stays visible and receives ordinary body typography; invalid/absent amounts no longer display a synthetic dash with a currency. Unknown scope remains explicit in the offer, without repeating it in the parent type line. |\n| Remove, organize and discovery memory | Offer removal and organization now share one aligned footer next to memory badges; existing removal loading/error/retry, freshness, capabilities, offer identity, folder/pin persistence and return callbacks remain. Legacy property-level remove/organize behavior stays available. |\n'''
p.write_text(s)
