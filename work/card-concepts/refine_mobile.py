from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app')
p=root/'lib/features/tenant/home/presentation/widgets/tenant_search_results/amenity_row.dart'
s=p.read_text()
block='''        for (final feature in item.amenities.toSet())
          Amenity(
            icon: _featureIcon(feature),
            label: item.copyWith(amenities: [feature]).amenityLabels.single,
          ),
'''
assert s.count(block)==1
s=s.replace(block,'').replace('      ],\n',block+'      ],\n',1)
p.write_text(s)
p=root/'lib/features/tenant/home/presentation/widgets/tenant_search_results/search_result_card.dart'
s=p.read_text()
s=s.replace('      if (!item.hasRentalOffers) ...labelResolver.amenityLabels(item).take(2),\n','')
p.write_text(s)
