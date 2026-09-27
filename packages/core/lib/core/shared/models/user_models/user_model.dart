import 'package:melos_core/core/extensions/object.dart';
import 'package:melos_core/core/helpers/cache_service.dart';

class UserModel {
  final String id;
  final String name;
  final String phone;
  final String email;

  /// Legacy server metadata, never an authorization or workspace selection.
  final String type;

  const UserModel({
    required this.id,
    required this.name,
    required this.phone,
    required this.email,
    this.type = '',
  });

  factory UserModel.initial() =>
      const UserModel(id: '0', name: '', phone: '', email: '', type: '');

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id']?.toString() ?? '',
      name: json['full_name']?.toString() ?? json['name']?.toString() ?? '',
      phone:
          json['phone']?.toString() ?? json['phone_number']?.toString() ?? '',
      email: json['email']?.toString() ?? '',
      type: json['type']?.toString() ?? '',
    );
  }

  UserModel copyWith({String? name, String? phone, String? email}) => UserModel(
    id: id,
    name: name ?? this.name,
    phone: phone ?? this.phone,
    email: email ?? this.email,
    type: type,
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'phone': phone,
    'email': email,
    'type': type,
  };

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
