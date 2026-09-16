import 'package:melos_core/core/shared/models/user_models/user_model.dart';

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
      name: json['name'] ?? '',
      phone: json['phone'] ?? '',
      email: json['email'] ?? '',
      type: json['type'] ?? '',
    );
  }
}
