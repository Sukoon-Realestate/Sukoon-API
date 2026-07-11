import 'package:melos_core/core/shared/models/user_models/user_model.dart';

class TenantModel extends UserModel{
  TenantModel({required super.id, required super.name, required super.email, required super.type});

  factory TenantModel.fromJson(Map<String, dynamic> json) {
    return TenantModel(
      id: json['id'],
      name: json['name'],
      email: json['email'],
      type: json['type'],
    );
  }
}