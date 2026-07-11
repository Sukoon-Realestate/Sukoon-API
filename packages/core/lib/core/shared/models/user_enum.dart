enum UserType{tenant, owner, unknown}

extension Check on UserType{
  bool get isOwner => this == UserType.owner;
  bool get isTenant => this == UserType.tenant;
}

extension UserTypeExtension on String{
  UserType get toUserType{
    switch(this){
      case 'owner':
        return UserType.owner;

      case 'tenant':
        return UserType.tenant;

      default:
        return UserType.unknown;
    }
  }
}