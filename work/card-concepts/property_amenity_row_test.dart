import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_search_results/amenity_row.dart';

void main() {
  for (final direction in TextDirection.values) {
    testWidgets('amenities wrap at narrow widths in $direction', (tester) async {
      tester.view.physicalSize = const Size(320, 800);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(ScreenUtilInit(
        designSize: const Size(390, 844),
        builder: (context, child) => MaterialApp(
          home: Scaffold(body: Directionality(
            textDirection: direction,
            child: MediaQuery(
              data: const MediaQueryData(textScaler: TextScaler.linear(1.5)),
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: AmenityRow(item: const PropertyDetailsModel.initial().copyWith(
                  amenities: ['wifi', 'wifi', 'air_conditioning', 'elevator'],
                  area: 180,
                  bedrooms: 2,
                  bathrooms: 1,
                )),
              ),
            ),
          )),
        ),
      ));
      expect(find.byIcon(Icons.wifi_outlined), findsOneWidget);
      expect(find.byIcon(Icons.ac_unit_outlined), findsOneWidget);
      expect(find.byIcon(Icons.elevator_outlined), findsOneWidget);
      expect(find.byIcon(Icons.local_parking_outlined), findsNothing);
      expect(find.byIcon(Icons.square_foot_outlined), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }
}
