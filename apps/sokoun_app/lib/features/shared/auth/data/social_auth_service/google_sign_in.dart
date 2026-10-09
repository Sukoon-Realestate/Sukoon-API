import 'dart:developer';

import 'package:google_sign_in/google_sign_in.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/network/fire_store.dart';
import 'package:melos_core/core/shared/base_state.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';

class GoogleSignService {
  GoogleSignService._internal();

  static GoogleSignService? _instance;
  static GoogleSignService get instance =>
      _instance ??= GoogleSignService._internal();

  final GoogleSignIn _signIn = GoogleSignIn.instance;

  void _handleAuthenticationEvent(GoogleSignInAuthenticationEvent e) {}
  void _handleAuthenticationError(Object e) =>
      FireStoreService.instance.storeError(e.toString());

  Future<void> init() async {
    await _signIn.initialize();
    _signIn.authenticationEvents
        .listen(_handleAuthenticationEvent)
        .onError(_handleAuthenticationError);
  }

  Future<String> authorize() async {
    final GoogleSignInAccount? user;
    const List<String> scopes = <String>['email', 'profile'];

    if (_signIn.supportsAuthenticate()) {
      try {
        user = await _signIn.authenticate();
        await user.authorizationClient.authorizationForScopes(scopes);
        log('the token is ${user.authentication.idToken}');
        return user.authentication.idToken ?? '';
      } on GoogleSignInException catch (e) {
        if (e.code == GoogleSignInExceptionCode.canceled) {
          Messages.showToast(
            msg: LocaleKeys.googleSignInCancelled,
            status: BaseStatus.error,
          );
          return '';
        }
        log('the google sign in error is ${e.toString()}');
        FireStoreService.instance.storeError(e.toString());
        Messages.showToast(
          msg: LocaleKeys.googleSignInFailed,
          status: BaseStatus.error,
        );
        return '';
      }
    } else {
      Messages.showToast(
        msg: LocaleKeys.googleSignInUnsupportedDevice,
        status: BaseStatus.error,
      );
      return '';
    }
  }
}
