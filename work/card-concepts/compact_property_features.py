from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app')
p=root/'lib/features/tenant/home/presentation/widgets/tenant_search_results/amenity_row.dart'
s=p.read_text()
a=s.index('        if (item.bedrooms > 0)')
b=s.index('        if (item.area > 0)',a)
s=s[:a]+s[b:]
s=s.replace('    return Wrap(', '''    final features = {
      if (item.amenities.contains('wifi')) 'wifi',
      if (item.amenities.contains('air_conditioning')) 'air_conditioning',
      ...item.amenities,
    }.take(2);
    return Wrap(''',1)
s=s.replace('for (final feature in item.amenities.toSet())','for (final feature in features)')
p.write_text(s)
p=root/'test/property_amenity_row_test.dart'
s=p.read_text().replace("'amenities wrap at narrow widths in $direction'", "'area and at most two features fit narrow widths in $direction'")
s=s.replace('expect(find.byIcon(Icons.elevator_outlined), findsOneWidget);','''expect(find.byIcon(Icons.elevator_outlined), findsNothing);
      expect(find.byIcon(Icons.bed_outlined), findsNothing);
      expect(find.byIcon(Icons.shower_outlined), findsNothing);
      expect(find.byType(Icon), findsNWidgets(3));''')
p.write_text(s)
