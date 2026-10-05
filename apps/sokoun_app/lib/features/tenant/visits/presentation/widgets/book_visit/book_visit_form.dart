part of '../../../imports.dart';

class BookVisitForm extends StatefulWidget {
  const BookVisitForm({
    super.key,
    required this.property,
    required this.days,
    required this.selectedDayIndex,
    required this.selectedTime,
    required this.noteController,
    required this.onDaySelected,
    required this.onTimeSelected,
    required this.onConfirmPressed,
  });

  final VisitPropertyContent property;
  final List<VisitDayContent> days;
  final int selectedDayIndex;
  final TimeOfDay? selectedTime;
  final TextEditingController noteController;
  final ValueChanged<int> onDaySelected;
  final ValueChanged<TimeOfDay> onTimeSelected;
  final Future<void> Function(BuildContext context) onConfirmPressed;

  @override
  State<BookVisitForm> createState() => _BookVisitFormState();
}

class _BookVisitFormState extends State<BookVisitForm> {
  final GlobalKey _dayFieldKey = GlobalKey();
  final GlobalKey _timeFieldKey = GlobalKey();

  String? _validateDay(String? value) =>
      widget.selectedDayIndex >= 0 &&
          widget.selectedDayIndex < widget.days.length
      ? null
      : LocaleKeys.fillField;

  String? _validateTime(String? value) =>
      widget.selectedTime != null ? null : LocaleKeys.fillField;

  List<FirstValidationErrorField> _validationFields() => [
    FirstValidationErrorField(
      fieldKey: _dayFieldKey,
      title: LocaleKeys.tenantVisitChooseDay,
      value: '${widget.selectedDayIndex}',
      validator: _validateDay,
    ),
    FirstValidationErrorField(
      fieldKey: _timeFieldKey,
      title: LocaleKeys.tenantVisitChooseTime,
      value: widget.selectedTime?.toString(),
      validator: _validateTime,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return FirstValidationErrorForm(
      validationFields: _validationFields,
      onValid: () => widget.onConfirmPressed(context),
      builder: (context, submit) => SingleChildScrollView(
        padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 24.h),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            VisitPropertySummaryCard(property: widget.property),
            18.szH,
            _BookVisitSectionTitle(LocaleKeys.tenantVisitChooseDay),
            10.szH,
            SokounValidationField(
              key: _dayFieldKey,
              value: '${widget.selectedDayIndex}',
              validator: _validateDay,
              child: widget.days.isEmpty
                  ? AppText(
                      LocaleKeys.tenantVisitNoAvailableDays,
                      style: AppTextStyles.regular12.copyWith(
                        color: AppColors.sokoonMuted,
                        fontSize: 12.sp,
                        height: 1.45,
                      ),
                    )
                  : SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        spacing: 8.w,
                        children: [
                          for (
                            int index = 0;
                            index < widget.days.length;
                            index++
                          )
                            VisitDayChip(
                              day: widget.days[index],
                              isSelected: widget.selectedDayIndex == index,
                              onPressed: () => widget.onDaySelected(index),
                            ),
                        ],
                      ),
                    ),
            ),
            20.szH,
            _BookVisitSectionTitle(LocaleKeys.tenantVisitChooseTime),
            10.szH,
            SokounValidationField(
              key: _timeFieldKey,
              value: widget.selectedTime?.toString(),
              validator: _validateTime,
              child: VisitTimePickerField(
                selectedTime: widget.selectedTime,
                onTimeSelected: widget.days.isEmpty
                    ? null
                    : widget.onTimeSelected,
              ),
            ),
            22.szH,
            _BookVisitSectionTitle(LocaleKeys.tenantVisitNoteLabel),
            10.szH,
            Container(
              constraints: BoxConstraints(minHeight: 80.h),
              padding: EdgeInsets.symmetric(horizontal: 14.w),
              decoration: BoxDecoration(
                color: AppColors.white,
                borderRadius: BorderRadius.circular(16.r),
                border: Border.all(color: AppColors.sokoonBorder),
              ),
              child: TextField(
                controller: widget.noteController,
                maxLines: 3,
                textAlign: TextAlign.start,
                style: AppTextStyles.medium13.copyWith(
                  color: AppColors.sokoonNavy,
                  fontSize: 13.sp,
                  height: 1.45,
                ),
                decoration: InputDecoration(
                  hintText: LocaleKeys.tenantVisitNoteHint,
                  hintStyle: AppTextStyles.base.copyWith(
                    color: AppColors.navyAlpha50,
                    fontSize: 13.sp,
                  ),
                  border: InputBorder.none,
                ),
              ),
            ),
            16.szH,
            const VisitPrivacyBanner(),
            16.szH,
            IgnorePointer(
              ignoring: widget.days.isEmpty,
              child: AnimatedOpacity(
                duration: SokounMotion.duration(context, milliseconds: 180),
                curve: SokounMotion.curve,
                opacity: widget.days.isEmpty ? .45 : 1,
                child: AppLoadingButton(
                  asyncCall: (_) => submit(),
                  title: LocaleKeys.tenantVisitConfirmRequest,
                  buttonColor: AppColors.sokoonTeal,
                  textColor: AppColors.white,
                  borderRadius: 14.r,
                  height: 50.h,
                  textStyle: AppTextStyles.bold15.copyWith(
                    fontSize: 15.sp,
                    height: 1.45,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _BookVisitSectionTitle extends StatelessWidget {
  const _BookVisitSectionTitle(this.title);

  final String title;

  @override
  Widget build(BuildContext context) {
    return AppText(
      title,
      style: AppTextStyles.bold14.copyWith(
        color: AppColors.sokoonNavy,
        fontSize: 14.sp,
        height: 1.45,
      ),
      maxLines: 1,
    );
  }
}
