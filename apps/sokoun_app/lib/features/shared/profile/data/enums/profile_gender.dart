part of '../../imports.dart';

enum ProfileGender { male, female, unspecified }

extension ProfileGenderX on ProfileGender {
  bool get isMale => this == ProfileGender.male;

  bool get isFemale => this == ProfileGender.female;

  bool get isUnspecified => this == ProfileGender.unspecified;

  String get apiValue => isUnspecified ? '' : name;
}
