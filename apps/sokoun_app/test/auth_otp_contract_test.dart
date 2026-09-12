import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/shared/auth/data/models/otp.dart';

void main() {
  group('auth OTP API contract', () {
    test('uses the verification endpoint and body', () {
      const VerifyOtpBody body = VerifyOtpBody(
        email: 'meshzeyad2@gmail.com',
        otp: '381838',
      );

      expect(ApiConstants.verifyOtp, 'auth/verify/');
      expect(body.toJson(), {'email': 'meshzeyad2@gmail.com', 'otp': '381838'});
    });

    test('uses the resend endpoint and body', () {
      const ResendOtpBody body = ResendOtpBody(email: 'user@example.com');

      expect(ApiConstants.resendOtp, 'auth/resend-otp/');
      expect(body.toJson(), {'email': 'user@example.com'});
    });
  });
}
