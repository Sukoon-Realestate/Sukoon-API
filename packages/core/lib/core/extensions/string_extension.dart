import 'dart:developer';
import 'package:easy_localization/easy_localization.dart' as tr;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../config/language/languages.dart';
import '../../config/language/locale_keys.g.dart';
import '../helpers/user_type_enum.dart';
import '../network/api_endpoints.dart';

extension FormatString on String {
  int calculateRenderedLines({
    required BuildContext context,
    required String text,
    required double maxWidth,
    TextStyle style = const TextStyle(),
  }) {
    final TextPainter textPainter = TextPainter(
      text: TextSpan(text: text, style: style),
      textDirection: TextDirection.ltr,
      textAlign: TextAlign.start,
      maxLines: null,
    );

    // لازم نحط maxWidth
    textPainter.layout(maxWidth: maxWidth);

    return textPainter.computeLineMetrics().length;
  }



  /// 1) عدد السطور المنطقي (count of '\n' + 1)
  int get getLinesCount {
    if (isEmpty) return 0;
    return split('\n').length;
  }

  // /// 2) عدد السطور بعد الرندر (wrap) باستخدام TextPainter
  // ///
  // /// - [style]: مطلوب (حجم/وزن/خط)
  // /// - [maxWidth]: مطلوب — المساحة المتاحة لعرض النص (بالـ pixels)
  // /// - [textDirection]: افتراضي ltr
  // /// - [textAlign]: افتراضي start
  // /// - [maxLines]: اذا عايز تحصر بعدد أقصى من السطور
  // /// - [textScaleFactor]: عادة تأخذ من MediaQuery
  int renderedLineCount({
    TextAlign textAlign = TextAlign.start,
    int? maxLines,
    double textScaleFactor = 1.0,
    StrutStyle? strutStyle,
  }) {
    if (isEmpty) return 0;

    final tp = TextPainter(
      text: TextSpan(text: this),
      textDirection: TextDirection.ltr,
      textAlign: textAlign,
      maxLines: maxLines,
      textScaleFactor: textScaleFactor,
      strutStyle: strutStyle,
    );

    // layout with given maxWidth
    tp.layout();

    // computeLineMetrics gives a LineMetrics per visual line
    final metrics = tp.computeLineMetrics();
    return metrics.length;
  }



  bool get isImage =>
      contains('jpg') ||
          contains('png') ||
          contains('svg') ||
          contains('gif');

  String get pathToRequest{
    if(this == LocaleKeys.moveToNextStage){
      return ApiConstants.matchRequestAnd+ApiConstants.userMoveToNextRequest;

    }else if(this == LocaleKeys.refuseMoveToNextStage){
      return ApiConstants.rejectAll;

    }else if(this == LocaleKeys.requestForExtensionOfPeriod){
      return ApiConstants.matchRequestAnd+ApiConstants.userExtensionRequest;

    }else{
      log('this is $this');
      return '';
    }
  }

  Languages toLang(){
    if(this == Languages.arabic.locale.languageCode || this == Languages.arabic.title){
      return Languages.arabic;
    }

    return Languages.english;
  }


  UserGender toUserGender(){
    if(this == LocaleKeys.male || this == UserGender.male.name){
      return UserGender.male;

    }else if(this == LocaleKeys.female || this == UserGender.female.name){
      return UserGender.female;

    }else{
      return UserGender.unknown;
    }
  }

  UserType toUserType(){
    if(this == UserType.individual.name){
      return UserType.individual;

    }else if(this == UserType.parent.name){
      return UserType.parent;

    }else if(this == UserType.child.name){
      return UserType.child;

    }else{
      return UserType.unknown;
    }
  }

  String capitalize() {
    return '${this[0].toUpperCase()}${substring(1)}';
  }

  String toEnglishNumbers() {
    return replaceAll('٠', '0')
        .replaceAll('١', '1')
        .replaceAll('٢', '2')
        .replaceAll('٣', '3')
        .replaceAll('٤', '4')
        .replaceAll('٥', '5')
        .replaceAll('٦', '6')
        .replaceAll('٧', '7')
        .replaceAll('٨', '8')
        .replaceAll('٩', '9');
  }

  String toCurrency() {
    final formatter = tr.NumberFormat('#,###');
    return formatter.format(double.parse(this));
  }

  void copyToClipboard() {
    Clipboard.setData(ClipboardData(text: this));
  }

  String get locale {
    return this.tr();
  }

  bool isNumeric() {
    return double.tryParse(this) != null;
  }

  String toCamelCase() {
    return this[0].toUpperCase() +
        substring(1).replaceAllMapped(
            RegExp('[_-](.)'), (Match match) => match.group(1)!.toLowerCase());
  }
}

extension FormatDouble on double {
  String toCurrency() {
    final formatter = tr.NumberFormat('#,###');
    return formatter.format(this);
  }
}

extension DateTimeFormatHelper on DateTime {
  String toTime([String? locale]) {
    return tr.DateFormat('hh:mm a', locale).format(this);
  }

  String toTimeWithoutPmAndAm([String? locale]) {
    return tr.DateFormat('hh:mm', locale).format(this);
  }

  String toAmAndPm([String? locale]) {
    return tr.DateFormat('a', locale).format(this);
  }

  String toFullDate({String? locale, String key = '-'}) {
    return tr.DateFormat('yyyy${key}MM${key}dd').format(this);
  }

  String toFullDateTime([String? locale]) {
    return tr.DateFormat('yyyy-MM-dd HH:mm').format(this);
  }

  String toDay([String? locale]) {
    return tr.DateFormat('EEEE').format(this);
  }

  String toMonth([String? locale]) {
    return tr.DateFormat('MMMM').format(this);
  }

  String toMonthShort([String? locale]) {
    return tr.DateFormat('MMM').format(this);
  }

  String toDayMonth([String? locale]) {
    return tr.DateFormat('dd MMMM').format(this);
  }

  String toDayMonthShort([String? locale]) {
    return tr.DateFormat('dd MMM').format(this);
  }

  String toDayMonthYear([String? locale]) {
    return tr.DateFormat('dd MMMM yyyy').format(this);
  }

  String toDayMonthYearShort([String? locale]) {
    return tr.DateFormat('dd MMM yyyy').format(this);
  }

  String toDayMonthYearTime([String? locale]) {
    return tr.DateFormat('dd MMMM yyyy HH:mm').format(this);
  }

  String toDayMonthYearTimeShort([String? locale]) {
    return tr.DateFormat('dd MMM yyyy HH:mm').format(this);
  }

  String toDayMonthYearTimeSeconds([String? locale]) {
    return tr.DateFormat('dd MMMM yyyy HH:mm:ss').format(this);
  }

  String toDayMonthYearTimeSecondsShort([String? locale]) {
    return tr.DateFormat('dd MMM yyyy HH:mm:ss').format(this);
  }
}
