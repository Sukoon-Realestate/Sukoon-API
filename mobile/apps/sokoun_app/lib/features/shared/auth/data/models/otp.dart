import 'package:melos_core/core/helpers/validators.dart';

class VerifyOtpBody {
  const VerifyOtpBody({required this.email, required this.otp});

  final String email;
  final String otp;

  factory VerifyOtpBody.initial() => const VerifyOtpBody(email: '', otp: '');

  VerifyOtpBody copyWith({String? email, String? otp}) =>
      VerifyOtpBody(email: email ?? this.email, otp: otp ?? this.otp);

  Map<String, dynamic> toJson() => {
    'email': Validators.normalizeEmail(email),
    'otp': Validators.normalizeOtpCode(otp),
  };
}

class ResendOtpBody {
  const ResendOtpBody({required this.email});

  final String email;

  factory ResendOtpBody.initial() => const ResendOtpBody(email: '');

  ResendOtpBody copyWith({String? email}) =>
      ResendOtpBody(email: email ?? this.email);

  Map<String, dynamic> toJson() => {'email': Validators.normalizeEmail(email)};
}
