part of '../../imports.dart';

class OwnerRequestsCalendarScreen extends StatefulWidget {
  const OwnerRequestsCalendarScreen({super.key});

  @override
  State<OwnerRequestsCalendarScreen> createState() =>
      _OwnerRequestsCalendarScreenState();
}

class _OwnerRequestsCalendarScreenState
    extends State<OwnerRequestsCalendarScreen> {
  int _selectedDay = 15;

  void _selectDay(int day) => setState(() => _selectedDay = day);

  Future<void> _openAvailability() async {
    final bool? saved = await Go.to<bool>(const OwnerAvailabilityScreen());
    if (saved == true && mounted) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(content: AppText(LocaleKeys.ownerAvailabilitySaved)),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            children: [
              const _OwnerCalendarHeader(),
              Expanded(
                child: OwnerCalendarContent(
                  selectedDay: _selectedDay,
                  onDaySelected: _selectDay,
                  onAvailabilityPressed: _openAvailability,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _OwnerCalendarHeader extends StatelessWidget {
  const _OwnerCalendarHeader();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 58.h,
      padding: EdgeInsets.symmetric(horizontal: 12.w),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.sokoonBorder)),
      ),
      child: Row(
        children: [
          IconButton(
            key: const ValueKey('owner-calendar-back'),
            onPressed: Go.back,
            visualDensity: VisualDensity.compact,
            icon: Icon(
              Icons.arrow_back_ios_new_rounded,
              color: AppColors.sokoonNavy,
              size: 20.r,
            ),
          ),
          4.szW,
          Expanded(
            child: AppText(
              LocaleKeys.ownerCalendarTitle,
              color: AppColors.sokoonNavy,
              fontSize: 18.sp,
              fontWeight: FontWeight.w900,
            ),
          ),
          AppText(
            LocaleKeys.ownerCalendarMonth,
            color: AppColors.gold,
            fontSize: 13.sp,
            fontWeight: FontWeight.w800,
          ),
        ],
      ),
    );
  }
}
