part of '../../../imports.dart';

class OwnerPropertyAvailabilityAction extends StatelessWidget {
  const OwnerPropertyAvailabilityAction({super.key, required this.propertyId});

  final String propertyId;

  @override
  Widget build(BuildContext context) => _OwnerPropertyCardAction(
    label: LocaleKeys.ownerCalendarManageAvailability,
    foregroundColor: context.appColor(AppColors.sokoonTeal),
    backgroundColor: context.appColor(AppColors.mintLight, surface: true),
    onPressed: () => Go.to(
      OwnerAvailabilityScreen(
        ownerPropertyId: propertyId,
        availabilityStartDate: DateUtils.dateOnly(DateTime.now()),
      ),
    ),
  );
}
