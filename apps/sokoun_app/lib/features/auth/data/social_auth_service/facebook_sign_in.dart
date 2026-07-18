import 'package:flutter_facebook_auth/flutter_facebook_auth.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/network/fire_store.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';

class FacebookSignService {
  FacebookSignService._internal();

  static FacebookSignService? _instance;
  static FacebookSignService get instance =>
      _instance ??= FacebookSignService._internal();

  Future<String> authorize() async {
    try {
      final LoginResult result = await FacebookAuth.instance.login(
        permissions: <String>['email', 'public_profile'],
      );

      switch (result.status) {
        case LoginStatus.success:
          final String token = result.accessToken?.tokenString ?? '';
          if (token.isEmpty) {
            Messages.showToast(msg: LocaleKeys.facebookSignInFailed);
          }
          return token;
        case LoginStatus.cancelled:
          Messages.showToast(msg: LocaleKeys.facebookSignInCancelled);
          return '';
        case LoginStatus.failed:
        case LoginStatus.operationInProgress:
          FireStoreService.instance.storeError(
            result.message ?? result.status.name,
          );
          Messages.showToast(msg: LocaleKeys.facebookSignInFailed);
          return '';
      }
    } catch (e) {
      FireStoreService.instance.storeError(e.toString());
      Messages.showToast(msg: LocaleKeys.facebookSignInFailed);
      return '';
    }
  }
}
