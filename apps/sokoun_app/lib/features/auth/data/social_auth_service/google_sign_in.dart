import 'dart:developer';

import 'package:google_sign_in/google_sign_in.dart';
import 'package:melos_core/core/network/fire_store.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';

class GoogleSignService{

  GoogleSignService._internal();
  static GoogleSignService? _instance;
  static GoogleSignService get instance => _instance ??= GoogleSignService._internal();


  void _handleAuthenticationEvent(GoogleSignInAuthenticationEvent e){}
   void _handleAuthenticationError(Object e) => FireStoreService.instance.storeError(e.toString());

   final GoogleSignIn _signIn = GoogleSignIn.instance;
   Future<void> init()async{
    await _signIn.initialize();
    _signIn.authenticationEvents
        .listen(_handleAuthenticationEvent)
        .onError(_handleAuthenticationError);
  }

   Future<void> authorize()async{
    final GoogleSignInAccount? user;
    const List<String> scopes = <String>[
      'email',
      'profile'
    ];
    if(_signIn.supportsAuthenticate()){
      user = await _signIn.authenticate();
       await user
          .authorizationClient
          .authorizationForScopes(scopes);

      log('the user is ${user.authentication.idToken}');
    }else{
      Messages.showToast(msg: 'can not sign in with google');
    }
  }
}