part of '../../../imports.dart';

class VisitTimePickerField extends StatelessWidget {
  const VisitTimePickerField({
    super.key,
    required this.selectedTime,
    required this.onTimeSelected,
  });

  final TimeOfDay? selectedTime;
  final ValueChanged<TimeOfDay>? onTimeSelected;

  Future<void> _openPicker(BuildContext context) async {
    final TimeOfDay? pickedTime = await showTimePicker(
      context: context,
      initialTime: selectedTime ?? const TimeOfDay(hour: 14, minute: 0),
      builder: (context, child) {
        final ThemeData theme = Theme.of(context);
        return Theme(
          data: theme.copyWith(
            colorScheme: theme.colorScheme.copyWith(
              primary: AppColors.sokoonTeal,
              onPrimary: AppColors.white,
              surface: AppColors.white,
              onSurface: AppColors.sokoonNavy,
            ),
            textButtonTheme: TextButtonThemeData(
              style: TextButton.styleFrom(
                foregroundColor: AppColors.sokoonTeal,
                textStyle: TextStyle(
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w800,
                  fontFamily: ConstantManager.fontFamily,
                ),
              ),
            ),
            timePickerTheme: TimePickerThemeData(
              backgroundColor: AppColors.white,
              hourMinuteColor: AppColors.tealAlpha07,
              hourMinuteTextColor: AppColors.sokoonNavy,
              dayPeriodColor: AppColors.tealAlpha07,
              dayPeriodTextColor: AppColors.sokoonTeal,
              dialBackgroundColor: AppColors.grayOffWhite,
              dialHandColor: AppColors.sokoonTeal,
              dialTextColor: AppColors.sokoonNavy,
              entryModeIconColor: AppColors.sokoonTeal,
              helpTextStyle: TextStyle(
                color: AppColors.sokoonGray,
                fontSize: 12.sp,
                fontWeight: FontWeight.w700,
                fontFamily: ConstantManager.fontFamily,
              ),
              hourMinuteTextStyle: TextStyle(
                fontSize: 40.sp,
                fontWeight: FontWeight.w800,
                fontFamily: ConstantManager.fontFamily,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(24.r),
              ),
            ),
          ),
          child: child!,
        );
      },
    );
    if (pickedTime != null) onTimeSelected?.call(pickedTime);
  }

  @override
  Widget build(BuildContext context) {
    final bool isEnabled = onTimeSelected != null;
    final bool hasValue = selectedTime != null;
    final String value = hasValue
        ? BookVisitBody.formatDisplayTime(
            hour: selectedTime!.hour,
            minute: selectedTime!.minute,
          )
        : LocaleKeys.tenantVisitChooseTime;

    return Semantics(
      button: true,
      enabled: isEnabled,
      child: GestureDetector(
        key: const ValueKey('visit-time-picker'),
        onTap: isEnabled ? () => _openPicker(context) : null,
        behavior: HitTestBehavior.opaque,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          height: 52.h,
          padding: EdgeInsetsDirectional.symmetric(horizontal: 16.w),
          decoration: BoxDecoration(
            color: isEnabled ? AppColors.white : AppColors.grayBackground,
            borderRadius: BorderRadius.circular(12.r),
            border: Border.all(
              color: hasValue ? AppColors.sokoonTeal : AppColors.sokoonBorder,
            ),
          ),
          child: Row(
            children: [
              Container(
                width: 32.r,
                height: 32.r,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: hasValue
                      ? AppColors.mintLight
                      : AppColors.grayBackground,
                  borderRadius: BorderRadius.circular(10.r),
                ),
                child: Icon(
                  Icons.schedule_rounded,
                  color: hasValue
                      ? AppColors.sokoonTeal
                      : AppColors.sokoonMuted,
                  size: 18.r,
                ),
              ),
              12.szW,
              Expanded(
                child: Align(
                  alignment: AlignmentDirectional.centerStart,
                  child: Directionality(
                    textDirection: hasValue
                        ? TextDirection.ltr
                        : Directionality.of(context),
                    child: AppText(
                      value,
                      color: hasValue
                          ? AppColors.sokoonNavy
                          : AppColors.sokoonMuted,
                      fontSize: 15.sp,
                      fontWeight: FontWeight.w600,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ),
              ),
              8.szW,
              Icon(
                Icons.keyboard_arrow_down_rounded,
                color: isEnabled ? AppColors.sokoonTeal : AppColors.sokoonMuted,
                size: 22.r,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
