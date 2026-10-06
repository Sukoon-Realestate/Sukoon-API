import 'package:melos_core/config/language/locale_keys.g.dart';

enum PropertyTenantType {
  all('all'),
  families('families'),
  singles('singles'),
  students('students'),
  femaleStudents('female_students');

  const PropertyTenantType(this.value);
  final String value;

  String get label => switch (this) {
    PropertyTenantType.all => LocaleKeys.ownerAddPropertyEveryone,
    PropertyTenantType.families => LocaleKeys.ownerAddPropertyFamilies,
    PropertyTenantType.singles => LocaleKeys.ownerAddPropertyIndividuals,
    PropertyTenantType.students => LocaleKeys.ownerAddPropertyStudents,
    PropertyTenantType.femaleStudents =>
      LocaleKeys.ownerAddPropertyFemaleStudents,
  };

  static PropertyTenantType? fromValue(String value) =>
      values.where((type) => type.value == value).firstOrNull;
}
