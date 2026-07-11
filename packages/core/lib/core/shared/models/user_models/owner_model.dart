import 'package:melos_core/core/shared/models/user_models/user_model.dart';

class OwnerModel extends UserModel{
  OwnerModel({required super.id, required super.name, required super.email, required super.type});

  factory OwnerModel.fromJson(Map<String, dynamic> json) {
    return OwnerModel(
      id: json['id'],
      name: json['name'],
      email: json['email'],
      type: json['type'],
    );
  }
}