part of '../../imports.dart';

class OwnerRequestsCalendarScreen extends StatefulWidget {
  const OwnerRequestsCalendarScreen({
    super.key,
    this.ownerPropertyId = '',
    this.initialDate,
  });

  final String ownerPropertyId;
  final DateTime? initialDate;

  @override
  State<OwnerRequestsCalendarScreen> createState() =>
      _OwnerRequestsCalendarScreenState();
}

class _OwnerRequestsCalendarScreenState
    extends State<OwnerRequestsCalendarScreen> {
  late final OwnerCalendarCubit _calendarCubit;
  late final ValueNotifier<Future<void>> _calendarRequest;
  late DateTime _selectedDate;

  @override
  void initState() {
    super.initState();
    _selectedDate = DateUtils.dateOnly(widget.initialDate ?? DateTime.now());
    _calendarCubit = OwnerCalendarCubit(initialDate: _selectedDate);
    _calendarRequest = ValueNotifier<Future<void>>(
      _calendarCubit.getCalendar(date: _selectedDate),
    );
  }

  @override
  void dispose() {
    _calendarCubit.close();
    _calendarRequest.dispose();
    super.dispose();
  }

  void _selectDay(DateTime date) {
    if (DateUtils.isSameDay(date, _selectedDate)) {
      return;
    }
    _selectedDate = date;
    _calendarRequest.value = _calendarCubit.getCalendar(date: date);
  }

  Future<void> _openAvailability(OwnerVisitCalendarContent calendar) async {
    final String ownerPropertyId = calendar.firstPropertyId.isNotEmpty
        ? calendar.firstPropertyId
        : widget.ownerPropertyId;
    if (ownerPropertyId.isEmpty) {
      return;
    }

    final bool? saved = await Go.to<bool>(
      OwnerAvailabilityScreen(
        ownerPropertyId: ownerPropertyId,
        availabilityStartDate: calendar.selectedDateValue,
      ),
    );
    if (saved == true && mounted) {
      _calendarRequest.value = _calendarCubit.getCalendar(date: _selectedDate);
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: AppText(
              LocaleKeys.ownerAvailabilitySaved,
              style: AppTextStyles.regular,
            ),
          ),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider<OwnerCalendarCubit>.value(
      value: _calendarCubit,
      child: AppScaffold(
        title: LocaleKeys.ownerCalendarTitle,
        showBackButton: true,
        actions: [
          ValueListenableBuilder<Future<void>>(
            valueListenable: _calendarRequest,
            builder: (context, _, child) => AppText(
              MaterialLocalizations.of(context).formatMonthYear(_selectedDate),
              style: AppTextStyles.extraBold13.copyWith(color: AppColors.gold),
            ).paddingSymmetric(horizontal: 12),
          ),
        ],
        backgroundColor: AppColors.scaffoldBackground,
        contentWidth: SokounContentWidth.wide,
        body: SafeArea(
          child: ValueListenableBuilder<Future<void>>(
            valueListenable: _calendarRequest,
            builder: (context, _, child) =>
                StatusBuilder<
                      OwnerCalendarCubit,
                      OwnerVisitCalendarContent
                    >.withShimmer(
                      initialDataForShimmer: OwnerVisitCalendarContent.initial(
                        _selectedDate,
                      ),
                      onRetry: () =>
                          _calendarCubit.getCalendar(date: _selectedDate),
                      builder: (calendar) => OwnerCalendarContent(
                        calendar: calendar,
                        selectedDate: calendar.selectedDateValue,
                        onDaySelected: _selectDay,
                        onAvailabilityPressed:
                            calendar.firstPropertyId.isNotEmpty ||
                                widget.ownerPropertyId.trim().isNotEmpty
                            ? () => _openAvailability(calendar)
                            : null,
                      ),
                    )
                    .withPullRefresher(
                      onRefresh: () =>
                          _calendarCubit.getCalendar(date: _selectedDate),
                    ),
          ),
        ),
      ),
    );
  }
}
