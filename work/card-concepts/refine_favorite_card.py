from pathlib import Path
base=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/tenant/favorites/presentation/widgets')
p=base/'favorite_property_card.dart'
s=p.read_text()
a=s.index('                tags: AppText(')
b=s.index('                priceContent:', a)
s=s[:a]+'''                tags: Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    if (item.rating > 0)
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.star_outline_rounded, size: 16,
                            color: context.appColor(AppColors.sokoonMuted)),
                          const SizedBox(width: 3),
                          AppText(item.ratingLabel, style: Theme.of(context).textTheme.bodySmall),
                        ],
                      ),
                    AppText(
                      [
                        if (item.propertyType.isNotEmpty)
                          PropertyDetailsModel.propertyTypeLabelFor(item.propertyType),
                        ...item.savedOffers.where((offer) => offer.scope != null)
                          .map((offer) => offer.scope!.label).toSet(),
                      ].join(' · '),
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
''' +s[b:]
s=s.replace('                    offer: offer,', '                    offer: offer,\n                    showPrice: item.savedOffers.length != 1 || !price.hasAmount,')
p.write_text(s)
p=base/'favorite_offer_row.dart'
s=p.read_text().replace('    this.fresh = true,', '    this.fresh = true,\n    this.showPrice = true,')
s=s.replace('  final bool fresh;', '  final bool fresh;\n\n  /// A single confirmed offer can share the price already shown above it.\n  final bool showPrice;')
s=s.replace('if (offer.terms.hasValidPrice)', 'if (widget.showPrice && offer.terms.hasValidPrice)')
p.write_text(s)
