part of '../../../imports.dart';

String profileDate(
  String value,
  BuildContext context, {
  bool showTime = false,
}) {
  final DateTime? date = DateTime.tryParse(value);
  if (date == null) return '';
  final formatter = DateFormat.yMMMd(context.locale.languageCode);
  if (showTime) formatter.add_jm();
  return formatter.format(showTime ? date.toLocal() : date);
}
