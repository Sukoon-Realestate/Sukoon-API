from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun')
base=root/'apps/sokoun_app/lib/features/tenant/favorites/presentation/widgets'
p=base/'favorite_property_card.dart'
s=p.read_text().replace("import 'package:sokoun_app/shared_widgets/property_card_summary.dart';", "import 'favorite_property_summary.dart';")
s=s.replace('PropertyCardSummary(', 'FavoritePropertySummary(')
s=s.replace('                price: price.label,\n', '')
s=s.replace('                    ...item.savedOffers\n                        .map(', '                    ...item.savedOffers\n                        .where((offer) => offer.scope != null)\n                        .map(')

s=s.replace('priceContent: RentalPriceText(price: price),', '''priceContent: price.hasAmount
                    ? RentalPriceText(price: price)
                    : AppText(
                        price.label,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: context.appColor(AppColors.sokoonMuted),
                          height: 1.5,
                        ),
                      ),''')
s=s.replace('borderRadius: BorderRadius.circular(14.r)', 'borderRadius: BorderRadius.circular(18)')
s=s.replace('''              if (item.hasRentalOffers) ...[
                AppText(LocaleKeys.rentalSavedOffers).paddingAll(12),''', '''              if (item.hasRentalOffers) ...[
                Divider(height: 1, color: context.appColor(AppColors.sokoonBorder)),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 14, 16, 4),
                  child: AppText(
                    LocaleKeys.rentalSavedOffers,
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: context.appColor(AppColors.sokoonMuted),
                    ),
                  ),
                ),''')
s=s.replace('''                  current: item.fromCache''', '''                  contentPadding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                  current: item.fromCache''')
s=s.replace('''                Align(
                  alignment: AlignmentDirectional.centerEnd,
                  child: FavoriteOrganizeButton(''', '''                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  child: Align(
                    alignment: AlignmentDirectional.centerEnd,
                    child: FavoriteOrganizeButton(''')
s=s.replace('''                    title: item.title,
                  ),
                ),''', '''                      title: item.title,
                    ),
                  ),
                ),''')
p.write_text(s)
(base/'favorite_property_summary.dart').write_text('''import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

/// Saved cards give property identity and facts priority over price guidance.
class FavoritePropertySummary extends StatelessWidget {
  const FavoritePropertySummary({
    super.key,
    required this.title,
    required this.metadata,
    required this.priceContent,
    this.location = '',
    this.tags,
  });
  final String title, location;
  final Widget metadata, priceContent;
  final Widget? tags;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      AppText(
        title,
        style: Theme.of(context).textTheme.titleSmall?.copyWith(
          color: context.appColor(AppColors.sokoonNavy),
          fontWeight: FontWeight.w700,
          height: 1.5,
        ),
        maxLines: 3,
        overflow: TextOverflow.ellipsis,
      ),
      if (location.trim().isNotEmpty) ...[
        const SizedBox(height: 6),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.location_on_outlined, size: 16,
              color: context.appColor(AppColors.sokoonMuted)),
            const SizedBox(width: 4),
            Expanded(child: AppText(location,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: context.appColor(AppColors.sokoonMuted), height: 1.5),
            )),
          ],
        ),
      ],
      const SizedBox(height: 12),
      metadata,
      if (tags != null) ...[const SizedBox(height: 6), tags!],
      const SizedBox(height: 12),
      priceContent,
    ],
  );
}
''')
p=base/'favorite_offer_row.dart'
s=p.read_text().replace("import 'package:melos_core/core/extensions/padding_extension.dart';", "import 'package:melos_core/config/res/config_imports.dart';")
s=s.replace("import 'package:flutter_screenutil/flutter_screenutil.dart';\n", '')
a=s.index('  Widget _row(')
b=s.index('  @override\n  Widget build', a)
s=s[:a]+'''  void _openOffer() => Go.to(
    PropertyDetailsScreen(
      propertyId: widget.propertyId,
      offerId: widget.offer.offerId,
    ),
  );

  Widget _row({bool loading = false, String? error}) {
    final theme = Theme.of(context);
    final muted = context.appColor(AppColors.sokoonMuted);
    final offer = widget.offer;
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 4, 12, 8),
      child: Container(
        decoration: BoxDecoration(
          color: theme.colorScheme.surfaceContainerLow,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: offer.offerId.isEmpty ? null : _openOffer,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(12, 12, 12, 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    AppText(
                      RentalOfferLabels.accommodation(offer),
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: context.appColor(AppColors.sokoonNavy),
                        fontWeight: offer.scope == null ? FontWeight.w400 : FontWeight.w600,
                        height: 1.5,
                      ),
                    ),
                    if (offer.terms.hasValidPrice) ...[
                      const SizedBox(height: 6),
                      AppText(RentalOfferLabels.price(offer),
                        style: theme.textTheme.titleSmall?.copyWith(height: 1.5)),
                    ],
                    if (RentalOfferLabels.snapshotFacts(offer).isNotEmpty) ...[
                      const SizedBox(height: 6),
                      AppText(RentalOfferLabels.snapshotFacts(offer).join(' · '),
                        style: theme.textTheme.bodySmall?.copyWith(color: muted, height: 1.5)),
                    ],
                    const SizedBox(height: 6),
                    AppText(
                      RentalOfferLabels.availability(offer.availability, archived: offer.archived),
                      style: theme.textTheme.bodySmall?.copyWith(color: muted, height: 1.5),
                    ),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: Row(
                children: [
                  Expanded(
                    child: PropertyMemoryBadge(
                      propertyId: widget.propertyId,
                      offerId: offer.offerId,
                      contentPadding: const EdgeInsetsDirectional.only(start: 8, end: 4),
                      current: widget.fresh ? FavoriteSnapshot.selection(offer) : null,
                    ),
                  ),
                  IconButtonTheme(
                    data: IconButtonThemeData(style: IconButton.styleFrom(
                      minimumSize: const Size(48, 48), foregroundColor: muted)),
                    child: FavoriteOrganizeButton(
                      propertyId: widget.propertyId,
                      offerId: offer.offerId,
                      title: offer.name,
                    ),
                  ),
                  if (_cubit != null)
                    IconButton(
                      tooltip: LocaleKeys.favoriteRemoveSemanticLabel,
                      onPressed: loading ? null : _remove,
                      style: IconButton.styleFrom(minimumSize: const Size(48, 48), foregroundColor: muted),
                      icon: const Icon(Icons.bookmark_remove_outlined),
                    ),
                ],
              ),
            ),
            if (loading) const LinearProgressIndicator(),
            if (error != null)
              Padding(padding: const EdgeInsets.all(12), child: AppText(error)),
          ],
        ),
      ),
    );
  }
''' + s[b:]
p.write_text(s)
