enum UserType { tenant, owner, unknown }

extension Check on UserType {
  bool get isOwner => this == UserType.owner;
  bool get isTenant => this == UserType.tenant;
}

extension UserTypeExtension on String? {
  UserType get toUserType {
    if (this == UserType.owner.name) {
      return UserType.owner;
    } else if (this == UserType.tenant.name) {
      return UserType.tenant;
    } else {
      return UserType.unknown;
    }
  }
}
