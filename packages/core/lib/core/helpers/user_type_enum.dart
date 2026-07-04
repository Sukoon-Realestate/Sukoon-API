enum UserGender{male, female, unknown}

extension Check on UserGender{
  bool get isMale => this == UserGender.male;
  bool get isFemale => this == UserGender.female;
  bool get isUnknown => this == UserGender.unknown;
}

enum UserType{individual, parent, child, unknown}

extension CheckType on UserType{
  bool get isIndividual => this == UserType.individual;
  bool get isChild => this == UserType.child;
  bool get isParent => this == UserType.parent;
  bool get isUnknown => this == UserType.unknown;
}