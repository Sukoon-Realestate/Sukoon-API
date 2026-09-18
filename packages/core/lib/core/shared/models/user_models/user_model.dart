import 'dart:developer';

import 'package:melos_core/core/extensions/object.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/shared/models/user_models/owner_model.dart';
import 'package:melos_core/core/shared/models/user_models/tenent_model.dart';

import '../../../helpers/user_type/user_type_helper.dart';

class UserModel {
  final String id;
  final String name;
  final String phone;
  final String email;
  final String type;

  const UserModel({
    required this.id,
    required this.name,
    required this.phone,
    required this.email,
    required this.type,
  });

  factory UserModel.initial() =>
      const UserModel(id: '0', name: '', phone: '', email: '', type: '');

  factory UserModel.fromJson(Map<String, dynamic> json) {
    log('the user model is $json');
    final UserType type = UserTypeHelper.instance.currentUserType;
    if (type.isTenant) {
      return TenantModel.fromJson(json);
    } else {
      return OwnerModel.fromJson(json);
    }
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'phone': phone,
    'email': email,
    'type': type,
  };

  static bool get isTenant {
    return currentUser is TenantModel;
  }

  static bool get isOwner {
    return currentUser is OwnerModel;
  }

  static bool get isAuthenticated {
    return currentUser.isNotNull;
  }

  static UserModel? get currentUser {
    final res =
        (CacheStorage.read('user', isDecoded: true) as Object?).isNotNull;
    if (res) {
      return UserModel.fromJson(CacheStorage.read('user', isDecoded: true));
    }

    return null;
  }
}
