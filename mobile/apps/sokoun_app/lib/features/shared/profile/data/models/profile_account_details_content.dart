import 'package:equatable/equatable.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import '../profile_json.dart';

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
      name: profileString(json['name'] ?? json['full_name']),
      email: profileString(json['email']),
      phoneNumber: profileString(json['phone_number'] ?? json['phone']),
      maskedPhoneNumber: profileString(json['masked_phone_number']),
    );
  }

  final String name;
  final String email;
  final String phoneNumber;
  final String maskedPhoneNumber;

  UserModel editableUser({
    required UserModel fallback,
    required String fullName,
  }) => fallback.copyWith(
    name: fullName.isNotEmpty ? fullName : fallback.name,
    phone: phoneNumber.isNotEmpty ? phoneNumber : fallback.phone,
    email: email.isNotEmpty ? email : fallback.email,
  );

  ProfileAccountDetailsContent updateFromUser(UserModel user) => copyWith(
    name: user.name,
    email: user.email,
    phoneNumber: user.phone,
    maskedPhoneNumber: maskPhone(user.phone),
  );

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
