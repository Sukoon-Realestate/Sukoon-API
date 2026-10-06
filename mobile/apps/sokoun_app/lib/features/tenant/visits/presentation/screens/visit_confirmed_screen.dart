part of '../../imports.dart';

class VisitConfirmedScreen extends StatelessWidget {
  const VisitConfirmedScreen({
    super.key,
    this.message = '',
    required this.property,
    required this.selectedDay,
    required this.selectedTime,
  });

  final String message;
  final VisitPropertyContent property;
  final VisitDayContent selectedDay;
  final VisitTimeSlotContent selectedTime;

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      showBackButton: false,
      backgroundColor: context.appColor(
        AppColors.scaffoldBackground,
        surface: true,
      ),
      body: SafeArea(
        child: VisitConfirmationContent(
          message: message,
          property: property,
          selectedDay: selectedDay,
          selectedTime: selectedTime,
        ),
      ),
    );
  }
}
