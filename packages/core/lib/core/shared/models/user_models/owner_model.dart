import 'package:melos_core/core/shared/models/user_models/user_model.dart';

import '../../../helpers/user_type/user_type_helper.dart';

class OwnerModel extends UserModel {
  const OwnerModel({
    required super.id,
    required super.name,
    required super.phone,
    required super.email,
    required super.type,
  });

  factory OwnerModel.fromJson(Map<String, dynamic> json) {
    return OwnerModel(
      id: json['id']?.toString() ?? '',
      name: json['full_name'] ?? json['name'] ?? '',
      phone: json['phone'] ?? '',
      email: json['email'] ?? '',
      type:
      json['type']?.toString() ??
          UserTypeHelper.instance.currentUserType.name,
    );
  }
}
