import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';

class TenantModel extends UserModel {
  const TenantModel({
    required super.id,
    required super.name,
    required super.phone,
    required super.email,
    required super.type,
  });

  factory TenantModel.fromJson(Map<String, dynamic> json) {
    return TenantModel(
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
