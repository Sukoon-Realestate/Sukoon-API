from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app')
p=root/'lib/features/tenant/home/presentation/widgets/tenant_property_details/amenity_wrap.dart'
s=p.read_text().replace("import 'package:flutter/material.dart';", "import 'package:flutter/material.dart';\nimport 'package:melos_core/config/language/locale_keys.g.dart';")
s=s.replace('    final uniqueAmenities = amenities.toSet().toList();', '''    final uniqueAmenities = amenities.toSet().toList();
    final icons = <String, IconData>{
      LocaleKeys.tenantFilterWifi: Icons.wifi_outlined,
      LocaleKeys.tenantFilterAirConditioning: Icons.ac_unit_outlined,
      LocaleKeys.tenantFilterElevator: Icons.elevator_outlined,
      LocaleKeys.tenantFilterGarage: Icons.local_parking_outlined,
      LocaleKeys.tenantFilterSecurity: Icons.shield_outlined,
      LocaleKeys.tenantFilterBalcony: Icons.balcony_outlined,
      LocaleKeys.tenantFilterNearMetro: Icons.subway_outlined,
      LocaleKeys.tenantFilterNaturalGas: Icons.local_fire_department_outlined,
      LocaleKeys.tenantFilterElectricityMeter: Icons.electric_meter_outlined,
      LocaleKeys.tenantFilterWaterMeter: Icons.water_drop_outlined,
    };''')
a=s.index('            child: AppText(')
b=s.index('          ),\n      ],',a)
s=s[:a]+'''            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  icons[amenity] ?? Icons.check_circle_outline,
                  size: 16.r,
                  color: context.appColor(AppColors.sokoonTeal),
                ),
                SizedBox(width: 6.w),
                Flexible(
                  child: AppText(
                    amenity,
                    style: AppTextStyles.bold12.copyWith(
                      color: context.appColor(AppColors.sokoonTeal),
                      fontSize: 12.sp,
                      height: 1.45,
                    ),
                  ),
                ),
              ],
            ),
'''+s[b:]
p.write_text(s)
# Reuse the locale and narrow-screen harness to verify detail chips separately.
s=(root/'test/property_amenity_row_test.dart').read_text()
s=s.replace("import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';\n",'')
s=s.replace("import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_search_results/amenity_row.dart';", "import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/amenity_wrap.dart';")
s=s.replace('short area label and three features fit narrow widths','detail amenity icons fit narrow widths')
a=s.index('                      child: AmenityRow(')
b=s.index('                    ),\n                  ),',a)
s=s[:a]+'''                      child: TenantPropertyAmenityWrap(
                        amenities: [
                          LocaleKeys.tenantFilterWifi,
                          LocaleKeys.tenantFilterWifi,
                          LocaleKeys.tenantFilterAirConditioning,
                          LocaleKeys.tenantFilterElevator,
                          LocaleKeys.tenantFilterSecurity,
                          LocaleKeys.tenantFilterBalcony,
                          LocaleKeys.tenantFilterNaturalGas,
                          LocaleKeys.tenantFilterElectricityMeter,
                          LocaleKeys.tenantFilterWaterMeter,
                        ],
                      ),
'''+s[b:]
a=s.index('      expect(find.byIcon(Icons.bed_outlined)')
b=s.index('      expect(tester.takeException()',a)
s=s[:a]+'''      expect(find.byIcon(Icons.shield_outlined), findsOneWidget);
      expect(find.byIcon(Icons.balcony_outlined), findsOneWidget);
      expect(find.byIcon(Icons.local_fire_department_outlined), findsOneWidget);
      expect(find.byIcon(Icons.electric_meter_outlined), findsOneWidget);
      expect(find.byIcon(Icons.water_drop_outlined), findsOneWidget);
      expect(find.byType(Icon), findsNWidgets(8));
'''+s[b:]
(root/'test/property_detail_amenity_icons_test.dart').write_text(s)
