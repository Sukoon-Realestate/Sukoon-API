import 'package:easy_localization/easy_localization.dart';

extension EnumExtensions on Enum {
  String get translate{
    return name.tr();
  }
}