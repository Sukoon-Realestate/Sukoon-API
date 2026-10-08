import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:sokoun_app/features/shared/profile/data/models/account_content.dart';

void main() {
  test(
    'temporary bypass keeps false API accounts verified when enabled',
    () {
      for (final json in <Map<String, dynamic>>[
        {'id': '1', 'is_verified': false},
        {
          'user': {'id': '1', 'is_verified': false},
        },
        {
          'is_verified': false,
          'user': {'id': '1'},
        },
      ]) {
        expect(UserModel.fromJson(json).isVerified, isTrue);
        expect(AccountContent.fromJson(json).identity.isVerified, isTrue);
      }
    },
    skip: !UserModel.bypassVerification,
  );
}
