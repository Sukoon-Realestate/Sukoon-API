part of '../../imports.dart';

class ProfileAccountDetailsContent extends Equatable {
  const ProfileAccountDetailsContent({
    required this.name,
    required this.email,
    required this.phoneNumber,
    required this.maskedPhoneNumber,
  });

  const ProfileAccountDetailsContent.initial()
    : name = '',
      email = '',
      phoneNumber = '',
      maskedPhoneNumber = '';

  factory ProfileAccountDetailsContent.fromJson(Map<String, dynamic> json) {
    return ProfileAccountDetailsContent(
      name: _profileString(json['name'] ?? json['full_name']),
      email: _profileString(json['email']),
      phoneNumber: _profileString(json['phone_number'] ?? json['phone']),
      maskedPhoneNumber: _profileString(json['masked_phone_number']),
    );
  }

  final String name;
  final String email;
  final String phoneNumber;
  final String maskedPhoneNumber;

  String get displayPhone {
    if (maskedPhoneNumber.isNotEmpty) return maskedPhoneNumber;
    return maskPhone(phoneNumber);
  }

  static String maskPhone(String value) {
    final String phone = value.trim();
    if (phone.length < 7) return phone;
    return '${phone.substring(0, 3)}****${phone.substring(phone.length - 3)}';
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'email': email,
    'phone_number': phoneNumber,
    'masked_phone_number': maskedPhoneNumber,
  };

  ProfileAccountDetailsContent copyWith({
    String? name,
    String? email,
    String? phoneNumber,
    String? maskedPhoneNumber,
  }) {
    return ProfileAccountDetailsContent(
      name: name ?? this.name,
      email: email ?? this.email,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      maskedPhoneNumber: maskedPhoneNumber ?? this.maskedPhoneNumber,
    );
  }

  @override
  List<Object?> get props => [name, email, phoneNumber, maskedPhoneNumber];
}

Map<String, dynamic> _profileJsonMap(Object? value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  return const {};
}

String _profileString(Object? value) => value?.toString().trim() ?? '';

String? _profileNullableString(Object? value) {
  final String normalized = _profileString(value);
  return normalized.isEmpty ? null : normalized;
}

int _profileInt(Object? value) {
  if (value is num) return value.toInt();
  return int.tryParse(_profileString(value)) ?? 0;
}

double _profileDouble(Object? value) {
  if (value is num) return value.toDouble();
  return double.tryParse(_profileString(value)) ?? 0;
}
