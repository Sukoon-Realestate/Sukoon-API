part of '../../imports.dart';

class VisitConfirmedScreen extends StatelessWidget {
  const VisitConfirmedScreen({
    super.key,
    required this.property,
    required this.selectedDay,
    required this.selectedTime,
  });

  final VisitPropertyContent property;
  final VisitDayContent selectedDay;
  final VisitTimeSlotContent selectedTime;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: VisitConfirmationContent(
          property: property,
          selectedDay: selectedDay,
          selectedTime: selectedTime,
        ),
      ),
    );
  }
}
