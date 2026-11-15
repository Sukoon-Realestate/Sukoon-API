from pathlib import Path
root = Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app')
p = root/'lib/features/tenant/home/presentation/widgets/tenant_search_results/amenity_row.dart'
s = p.read_text()
s = s.replace('      children: [', '''      children: [
        for (final feature in item.amenities.toSet())
          Amenity(
            icon: _featureIcon(feature),
            label: item.copyWith(amenities: [feature]).amenityLabels.single,
          ),''',1)
s = s.replace('  @override\n', '''  static IconData _featureIcon(String feature) => switch (feature) {
    'wifi' => Icons.wifi_outlined,
    'air_conditioning' => Icons.ac_unit_outlined,
    'elevator' => Icons.elevator_outlined,
    'garage' => Icons.local_parking_outlined,
    'security' => Icons.shield_outlined,
    'balcony' => Icons.balcony_outlined,
    'near_metro' => Icons.subway_outlined,
    'natural_gas' => Icons.local_fire_department_outlined,
    'electricity_meter' => Icons.electric_meter_outlined,
    'water_meter' => Icons.water_drop_outlined,
    _ => Icons.check_circle_outline,
  };

  @override
''',1)
p.write_text(s)
p = root/'lib/features/tenant/home/data/models/home_page_model.dart'
s = p.read_text()
s = s.replace('  final int bedrooms;', '  final List<String> amenities;\n  final int bedrooms;',1)
s = s.replace('    this.bedrooms = 0,','    this.amenities = const [],\n    this.bedrooms = 0,',1)
s = s.replace('    : bedrooms = 0,','    : amenities = const [],\n      bedrooms = 0,',1)
s = s.replace('      HomePropertyModel(','      HomePropertyModel(\n        amenities: (json[\'amenities\'] as List?)?.whereType<String>().toList(growable: false) ?? const [],',1)
s = s.replace("    'bedrooms': bedrooms,", "    'amenities': amenities,\n    'bedrooms': bedrooms,",1)
s = s.replace('    int? bedrooms,','    List<String>? amenities,\n    int? bedrooms,',1)
s = s.replace('    bedrooms: bedrooms ?? this.bedrooms,','    amenities: amenities ?? this.amenities,\n    bedrooms: bedrooms ?? this.bedrooms,',1)
s = s.replace('  List<Object?> get props => [','  List<Object?> get props => [\n    amenities,',1)
p.write_text(s)
p = root/'test/tenant_home_pagination_test.dart'
s = p.read_text().replace("      'id': 'facts',", "      'id': 'facts',\n      'amenities': ['wifi', 'air_conditioning'],",1)
s = s.replace('    expect(restored, property);', "    expect(restored, property);\n    expect(restored.toDetailsPreview().amenities, ['wifi', 'air_conditioning']);\n    expect(property.copyWith(title: 'Updated').amenities, ['wifi', 'air_conditioning']);\n    expect(const HomePropertyModel.initial().amenities, isEmpty);",1)
p.write_text(s)
