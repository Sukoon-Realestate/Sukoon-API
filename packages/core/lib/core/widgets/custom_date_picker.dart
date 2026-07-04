import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../config/language/languages.dart';
import '../../config/res/config_imports.dart';
import '../navigation/navigator.dart';

Future<DateTime?> showCustomDatePicker({
  required TextEditingController controller,
  String? dateFormat,
}) async {
  final DateTime? pickedDate = await showDatePicker(
    locale: Languages.currentLanguage.locale,
    context: Go.context,
    initialDate: DateTime.now(),
    firstDate: DateTime.now(),
    initialEntryMode: DatePickerEntryMode.calendarOnly,
    lastDate: DateTime.now().add(const Duration(days: 365 * 4)),
    builder: (context, child) {
      return Theme(
        data: Theme.of(context).copyWith(
          colorScheme: const ColorScheme.light(
            primary: AppColors.primary,
            onPrimary: AppColors.white,
            onSurface: AppColors.primary,
          ),
          textButtonTheme: TextButtonThemeData(
            style: TextButton.styleFrom(
              foregroundColor: AppColors.primary,
            ),
          ),
        ),
        child: child!,
      );
    },
  );
  if (pickedDate != null) {
    final String formattedDate = DateFormat(dateFormat ?? 'EEE, M/d/y',
            Languages.currentLanguage.locale.languageCode)
        .format(pickedDate);
    controller.text = formattedDate;
  }
  return pickedDate;
}
