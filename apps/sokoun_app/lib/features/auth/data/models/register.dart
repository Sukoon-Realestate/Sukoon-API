class RegisterBody {
  final String name;
  final String phone;
  final String email;
  final String password;
  final String rePassword;

  const RegisterBody({
    required this.name,
    required this.phone,
    required this.email,
    required this.password,
    required this.rePassword,
  });

  factory RegisterBody.initial() => const RegisterBody(
    name: '',
    phone: '',
    email: '',
    password: '',
    rePassword: '',
  );

  factory RegisterBody.fromJson(Map<String, dynamic> json) => RegisterBody(
    name: json['name'] ?? '',
    phone: json['phone'] ?? '',
    email: json['email'] ?? '',
    password: json['password'] ?? '',
    rePassword: json['re_password'] ?? '',
  );

  Map<String, dynamic> toJson() => {
    'name': name,
    'phone': phone,
    'email': email,
    'password': password,
    're_password': rePassword,
  };

  RegisterBody copyWith({
    String? name,
    String? phone,
    String? email,
    String? password,
    String? rePassword,
  }) => RegisterBody(
    name: name ?? this.name,
    phone: phone ?? this.phone,
    email: email ?? this.email,
    password: password ?? this.password,
    rePassword: rePassword ?? this.rePassword,
  );
}
