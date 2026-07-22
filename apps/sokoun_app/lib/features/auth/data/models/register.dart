import 'dart:io';

class KycDocumentUploadData {
  const KycDocumentUploadData({
    required this.nationalId,
    required this.frontIdImage,
    required this.backIdImage,
    required this.selfieImage,
  });

  final String nationalId;
  final File? frontIdImage;
  final File? backIdImage;
  final File? selfieImage;
}

class RegisterBody {
  final String firstName;
  final String lastName;
  final String phone;
  final String email;
  final String password;
  final String rePassword;
  final String? userType;
  final String? nationalId;
  final File? frontIdImage;
  final File? backIdImage;
  final File? selfieImage;

  const RegisterBody({
    required this.firstName,
    required this.lastName,
    required this.phone,
    required this.email,
    required this.password,
    required this.rePassword,
    this.userType,
    this.nationalId,
    this.frontIdImage,
    this.backIdImage,
    this.selfieImage,
  });

  factory RegisterBody.initial() => const RegisterBody(
    firstName: '',
    lastName: '',
    phone: '',
    email: '',
    password: '',
    rePassword: '',
  );

  factory RegisterBody.fromJson(Map<String, dynamic> json) => RegisterBody(
    firstName: json['first_name'] ?? '',
    lastName: json['last_name'] ?? '',
    phone: json['phone'] ?? '',
    email: json['email'] ?? '',
    password: json['password'] ?? '',
    rePassword: json['re_password'] ?? '',
    userType: json['type'],
    nationalId: json['national_id'],
  );

  bool get hasFiles =>
      frontIdImage != null || backIdImage != null || selfieImage != null;

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> body = {
      'first_name': firstName,
      'last_name': lastName,
      'phone': phone,
      'email': email,
      'password': password,
      're_password': rePassword,
    };

    if (userType != null && userType!.isNotEmpty) {
      body['type'] = userType;
    }
    if (nationalId != null && nationalId!.isNotEmpty) {
      body['national_id'] = nationalId;
    }
    if (frontIdImage != null) {
      body['front_id_image'] = frontIdImage;
    }
    if (backIdImage != null) {
      body['back_id_image'] = backIdImage;
    }
    if (selfieImage != null) {
      body['selfie_image'] = selfieImage;
    }

    return body;
  }

  RegisterBody copyWith({
    String? firstName,
    String? lastName,
    String? phone,
    String? email,
    String? password,
    String? rePassword,
    String? userType,
    String? nationalId,
    File? frontIdImage,
    File? backIdImage,
    File? selfieImage,
  }) => RegisterBody(
    firstName: firstName ?? this.firstName,
    lastName: lastName ?? this.lastName,
    phone: phone ?? this.phone,
    email: email ?? this.email,
    password: password ?? this.password,
    rePassword: rePassword ?? this.rePassword,
    userType: userType ?? this.userType,
    nationalId: nationalId ?? this.nationalId,
    frontIdImage: frontIdImage ?? this.frontIdImage,
    backIdImage: backIdImage ?? this.backIdImage,
    selfieImage: selfieImage ?? this.selfieImage,
  );
}
