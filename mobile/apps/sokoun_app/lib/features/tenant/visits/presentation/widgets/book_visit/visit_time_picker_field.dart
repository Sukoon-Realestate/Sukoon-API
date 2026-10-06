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
              primary: context.appColor(AppColors.sokoonTeal),
              onPrimary: theme.brightness == Brightness.dark
                  ? AppColors.sokoonNavy
                  : AppColors.white,
              surface: context.appColor(AppColors.white, surface: true),
              onSurface: context.appColor(AppColors.sokoonNavy),
            ),
            textButtonTheme: TextButtonThemeData(
              style: TextButton.styleFrom(
                foregroundColor: context.appColor(AppColors.sokoonTeal),
                textStyle: AppTextStyles.extraBold.copyWith(fontSize: 14.sp),
              ),
            ),
            timePickerTheme: TimePickerThemeData(
              backgroundColor: context.appColor(AppColors.white, surface: true),
              hourMinuteColor: AppColors.tealAlpha07,
              hourMinuteTextColor: context.appColor(AppColors.sokoonNavy),
              dayPeriodColor: AppColors.tealAlpha07,
              dayPeriodTextColor: context.appColor(AppColors.sokoonTeal),
              dialBackgroundColor: context.appColor(
                AppColors.grayOffWhite,
                surface: true,
              ),
              dialHandColor: context.appColor(AppColors.sokoonTeal),
              dialTextColor: context.appColor(AppColors.sokoonNavy),
              entryModeIconColor: context.appColor(AppColors.sokoonTeal),
              helpTextStyle: AppTextStyles.bold12.copyWith(
                color: context.appColor(AppColors.sokoonGray),
                fontSize: 12.sp,
                height: 1.45,
              ),
              hourMinuteTextStyle: AppTextStyles.extraBold.copyWith(
                fontSize: 40.sp,
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
        onTap: isEnabled ? () => _openPicker(context) : null,
        behavior: HitTestBehavior.opaque,
        child: AnimatedContainer(
          duration: SokounMotion.duration(context, milliseconds: 180),
          height: 52.h,
          padding: EdgeInsetsDirectional.symmetric(horizontal: 16.w),
          decoration: BoxDecoration(
            color: isEnabled
                ? context.appColor(AppColors.white, surface: true)
                : context.appColor(AppColors.grayBackground, surface: true),
            borderRadius: BorderRadius.circular(12.r),
            border: Border.all(
              color: hasValue
                  ? context.appColor(AppColors.sokoonTeal)
                  : context.appColor(AppColors.sokoonBorder),
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
                      ? context.appColor(AppColors.mintLight, surface: true)
                      : context.appColor(
                          AppColors.grayBackground,
                          surface: true,
                        ),
                  borderRadius: BorderRadius.circular(10.r),
                ),
                child: Icon(
                  Icons.schedule_rounded,
                  color: hasValue
                      ? context.appColor(AppColors.sokoonTeal)
                      : context.appColor(AppColors.sokoonMuted),
                  size: 18.r,
                ),
              ),
              12.szW,
              Expanded(
                child: AppText(
                  value,
                  style: AppTextStyles.semiBold.copyWith(
                    color: hasValue
                        ? context.appColor(AppColors.sokoonNavy)
                        : context.appColor(AppColors.sokoonMuted),
                    fontSize: 15.sp,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ).startWidget,
              ),
              8.szW,
              Icon(
                Icons.keyboard_arrow_down_rounded,
                color: isEnabled
                    ? context.appColor(AppColors.sokoonTeal)
                    : context.appColor(AppColors.sokoonMuted),
                size: 22.r,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
