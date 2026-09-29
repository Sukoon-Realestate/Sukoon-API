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
      child: ValueListenableBuilder<Future<void>>(
        valueListenable: _calendarRequest,
        builder: (context, calendarRequest, _) =>
            StatusBuilder<
              OwnerCalendarCubit,
              OwnerVisitCalendarContent
            >.withShimmer(
              initialDataForShimmer: OwnerVisitCalendarContent.initial(
                _selectedDate,
              ),
              requestToTryAgainWhenError: calendarRequest,
              onRetry: () => _calendarCubit.getCalendar(date: _selectedDate),
              errorType: ErrorType.defaultView,
              builder: _buildScreen,
            ),
      ),
    );
  }

  Widget _buildScreen(OwnerVisitCalendarContent calendar) {
    final bool canManageAvailability =
        calendar.firstPropertyId.isNotEmpty ||
        widget.ownerPropertyId.trim().isNotEmpty;
    return AppScaffold(
      showBackButton: false,
      contentWidth: SokounContentWidth.wide,
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: Column(
          children: [
            _OwnerCalendarHeader(year: calendar.year, month: calendar.month),
            Expanded(
              child: OwnerCalendarContent(
                calendar: calendar,
                selectedDate: calendar.selectedDateValue,
                onDaySelected: _selectDay,
                onAvailabilityPressed: canManageAvailability
                    ? () => _openAvailability(calendar)
                    : null,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _OwnerCalendarHeader extends StatelessWidget {
  const _OwnerCalendarHeader({required this.year, required this.month});

  final int year;
  final int month;

  @override
  Widget build(BuildContext context) {
    final String monthLabel = MaterialLocalizations.of(
      context,
    ).formatMonthYear(DateTime(year, month));
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
              style: AppTextStyles.bold.copyWith(
                color: AppColors.sokoonNavy,
                fontSize: 18.sp,
              ),
            ),
          ),
          AppText(
            monthLabel,
            style: AppTextStyles.extraBold13.copyWith(
              color: AppColors.gold,
              fontSize: 13.sp,
              height: 1.45,
            ),
          ),
        ],
      ),
    );
  }
}
