import 'package:melos_core/core/helpers/cache_service.dart';

class UserModel {
  /// Temporary rollout bypass. Set SOKOUN_BYPASS_VERIFICATION=false to enforce
  /// the account flag without changing the feature guards.
  static const bool bypassVerification = bool.fromEnvironment(
    'SOKOUN_BYPASS_VERIFICATION',
    defaultValue: true,
  );

  final String id;
  final String name;
  final String phone;
  final String email;
  final bool isVerified;

  /// Legacy server metadata, never an authorization or workspace selection.
  final String type;

  const UserModel({
    required this.id,
    required this.name,
    required this.phone,
    required this.email,
    this.isVerified = bypassVerification,
    this.type = '',
  });

  factory UserModel.initial() =>
      const UserModel(id: '0', name: '', phone: '', email: '', type: '');

  factory UserModel.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> user = json['user'] is Map
        ? Map<String, dynamic>.from(json['user'] as Map)
        : json;
    final Map<String, dynamic> details = json['account_details'] is Map
        ? Map<String, dynamic>.from(json['account_details'] as Map)
        : const {};
    return UserModel(
      id: user['id']?.toString() ?? '',
      name:
          user['full_name']?.toString() ??
          user['name']?.toString() ??
          details['name']?.toString() ??
          '',
      phone:
          user['phone']?.toString() ??
          user['phone_number']?.toString() ??
          details['phone_number']?.toString() ??
          details['phone']?.toString() ??
          '',
      email: user['email']?.toString() ?? details['email']?.toString() ?? '',
      isVerified:
          bypassVerification ||
          (json.containsKey('is_verified')
                  ? json['is_verified']
                  : user['is_verified']) ==
              true,
      type: user['type']?.toString() ?? '',
    );
  }

  UserModel copyWith({
    String? name,
    String? phone,
    String? email,
    bool? isVerified,
  }) => UserModel(
    id: id,
    name: name ?? this.name,
    phone: phone ?? this.phone,
    email: email ?? this.email,
    isVerified: isVerified ?? this.isVerified,
    type: type,
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'phone': phone,
    'email': email,
    'is_verified': isVerified,
    'type': type,
  };

  static bool get isAuthenticated => currentUser != null;

  static UserModel? get currentUser {
    final Map<String, dynamic>? json = CacheStorage.read(
      'user',
      isDecoded: true,
    );
    return json == null ? null : UserModel.fromJson(json);
  }
}
