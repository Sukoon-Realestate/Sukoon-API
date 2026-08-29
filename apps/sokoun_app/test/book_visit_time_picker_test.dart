import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';

void main() {
  testWidgets('picks and displays visit time in 12-hour format', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(360, 690);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      ScreenUtilInit(
        designSize: const Size(360, 690),
        builder: (context, child) =>
            const MaterialApp(home: Scaffold(body: _TimePickerHost())),
      ),
    );

    await tester.tap(find.byKey(const ValueKey('visit-time-picker')));
    await tester.pumpAndSettle();

    expect(find.byType(TimePickerDialog), findsOneWidget);
    final BuildContext pickerContext = tester.element(
      find.byType(TimePickerDialog),
    );
    final String okLabel = MaterialLocalizations.of(
      pickerContext,
    ).okButtonLabel;
    await tester.tap(find.widgetWithText(TextButton, okLabel).last);
    await tester.pumpAndSettle();

    expect(find.byType(TimePickerDialog), findsNothing);
    expect(find.text('2:00 PM'), findsOneWidget);
    expect(
      tester
          .widget<VisitTimePickerField>(find.byType(VisitTimePickerField))
          .selectedTime,
      const TimeOfDay(hour: 14, minute: 0),
    );
  });
}

class _TimePickerHost extends StatefulWidget {
  const _TimePickerHost();

  @override
  State<_TimePickerHost> createState() => _TimePickerHostState();
}

class _TimePickerHostState extends State<_TimePickerHost> {
  TimeOfDay? _selectedTime;

  @override
  Widget build(BuildContext context) {
    return VisitTimePickerField(
      selectedTime: _selectedTime,
      onTimeSelected: (time) => setState(() => _selectedTime = time),
    );
  }
}
