import 'dart:convert';
import '../../../extensions/object.dart';
import '../../../extensions/string_extension.dart';
import '../../../helpers/cache_service.dart';
import '../../../helpers/user_type_enum.dart';
import '../title_value_shape.dart';

class UserModel {
  final bool hasActivePackage;
  final int? id;
  final String? name;
  final int? parentId;
  final TypeValueShape? type;
  final GenderValueShape? gender;
  final dynamic avatar;
  final String? phone;
  final String? countryCode;
  final String? fullPhone;
  final String? identityNumber;
  final int? age;
  final bool? isActive;
  final bool? isBlocked;
  final TitleValueShape? adminApprovalStatus;
  final String? completeRegistration;
  final String? token;
  final bool? isNotify;
  final CanChat? canChat;
  final bool? hasChatWith;
  final bool? isParentMatch;
  final int? views;

  const UserModel({
    this.hasActivePackage = false,
    this.id,
    this.name,
    this.parentId,
    this.type,
    this.gender,
    this.avatar,
    this.phone,
    this.countryCode,
    this.fullPhone,
    this.identityNumber,
    this.age,
    this.isActive,
    this.isBlocked,
    this.adminApprovalStatus,
    this.completeRegistration,
    this.token,
    this.isNotify,
    this.canChat,
    this.hasChatWith,
    this.isParentMatch,
    this.views,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    final bool isParent = json['type']['value'].toString().toUserType().isParent;

    if(isParent){
      return ParentModel.fromJson(json);

    }else {
      return IndividualUserModel.fromJson(json);
    }
  }

  static bool get isMale{
    return currentUser is MaleModel;
  }

  static bool get isFemale{
    return currentUser is FemaleModel;
  }

  static bool get isParent{
    return currentUser is ParentModel;
  }

  static bool get isIndividual{
    return currentUser is! ParentModel;
  }

  static bool get isAuthenticated{
    return currentUser.isNotNull;
  }

  static UserModel? get currentUser {
    final res = (CacheStorage.read('user', isDecoded: true) as Object?).isNotNull;
    if(res){
      return UserModel.fromJson(
          CacheStorage.read('user', isDecoded: true)
      );
    }

    return null;
  }


  factory UserModel.initial() => const UserModel(
    id: 0,
    name: '',
    parentId: null,
    type: null,
    gender: null,
    avatar: null,
    phone: '',
    countryCode: '',
    fullPhone: '',
    identityNumber: '',
    age: 0,
    isActive: false,
    isBlocked: false,
    adminApprovalStatus: null,
    completeRegistration: '',
    token: '',
    isNotify: false,
    hasActivePackage: false
  );

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'parent_id': parentId,
      'type': type,
      'gender': gender?.toJson(),
      'avatar': avatar,
      'phone': phone,
      'country_code': countryCode,
      'full_phone': fullPhone,
      'identity_number': identityNumber,
      'has_active_package' : hasActivePackage,
      'age': age,
      'is_active': isActive,
      'is_blocked': isBlocked,
      'admin_approval_status': adminApprovalStatus,
      'complete_registration': completeRegistration,
      'token': token,
      'is_notify': isNotify,
    };
  }

  UserModel copyWith({
    int? id,
    String? name,
    int? parentId,
    TypeValueShape? type,
    GenderValueShape? gender,
    dynamic avatar,
    String? phone,
    String? countryCode,
    String? fullPhone,
    String? identityNumber,
    int? age,
    bool? isActive,
    bool? isBlocked,
    TitleValueShape? adminApprovalStatus,
    String? completeRegistration,
    String? token,
    bool? isNotify,
    bool? hasActivePackage
  }) {
    return UserModel(
      id: id ?? this.id,
      name: name ?? this.name,
      parentId: parentId ?? this.parentId,
      type: type ?? this.type,
      gender: gender ?? this.gender,
      avatar: avatar ?? this.avatar,
      phone: phone ?? this.phone,
      countryCode: countryCode ?? this.countryCode,
      fullPhone: fullPhone ?? this.fullPhone,
      identityNumber: identityNumber ?? this.identityNumber,
      age: age ?? this.age,
      isActive: isActive ?? this.isActive,
      isBlocked: isBlocked ?? this.isBlocked,
      adminApprovalStatus: adminApprovalStatus ?? this.adminApprovalStatus,
      completeRegistration: completeRegistration ?? this.completeRegistration,
      token: token ?? this.token,
      hasActivePackage: hasActivePackage ?? this.hasActivePackage,
      isNotify: isNotify ?? this.isNotify,
    );
  }

  /// Utility: parse from raw JSON string
  static UserModel fromRawJson(String str) =>
      UserModel.fromJson(json.decode(str));

  /// Utility: convert to raw JSON string
  String toRawJson() => json.encode(toJson());
}


class TypeValueShape {
  UserType? userType;
  TitleValueShape? titleValueShape;

  TypeValueShape({
    this.titleValueShape,
    this.userType,
  });

  TypeValueShape.fromJson(dynamic json) {
    titleValueShape = TitleValueShape.fromJson(json);
    userType = (json['value'] as String).toUserType();
  }

  GenderValueShape copyWith({
    TitleValueShape? titleValueShape,
  }) => GenderValueShape(
      titleValueShape: titleValueShape ?? this.titleValueShape
  );

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{};
    map['value'] = titleValueShape?.value;
    map['title'] = titleValueShape?.title;
    return map;
  }

}


class GenderValueShape {
  UserGender? userGender;
  TitleValueShape? titleValueShape;

  GenderValueShape({
    this.titleValueShape,
    this.userGender,
  });

  GenderValueShape.fromJson(dynamic json) {
    titleValueShape = TitleValueShape.fromJson(json);
    userGender = (json['value'] as String).toUserGender();
  }

  GenderValueShape copyWith({
    TitleValueShape? titleValueShape,
  }) => GenderValueShape(
      titleValueShape: titleValueShape ?? this.titleValueShape
  );

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{};
    map['value'] = titleValueShape?.value;
    map['title'] = titleValueShape?.title;
    return map;
  }

}

class CityModel {
  CityModel({
    this.id,
    this.name,
    this.country,
    this.countryId,
  });

  CityModel.fromJson(dynamic json) {
    id = json['id'];
    name = json['name'];
    country = json['country'];
    countryId = json['country_id'];
  }
  int? id;
  String? name;
  String? country;
  int? countryId;
  CityModel copyWith({  int? id,
    String? name,
    String? country,
    int? countryId,
  }) => CityModel(  id: id ?? this.id,
    name: name ?? this.name,
    country: country ?? this.country,
    countryId: countryId ?? this.countryId,
  );
  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{};
    map['id'] = id;
    map['name'] = name;
    map['country'] = country;
    map['country_id'] = countryId;
    return map;
  }

}
