import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';

class LoginFooter extends StatefulWidget {
  const LoginFooter({super.key, this.onSignUp});

  final VoidCallback? onSignUp;

  @override
  State<LoginFooter> createState() => _LoginFooterState();
}

class _LoginFooterState extends State<LoginFooter> {
  late final TapGestureRecognizer _signUpRecognizer;

  @override
  void initState() {
    super.initState();
    _signUpRecognizer = TapGestureRecognizer();
  }

  @override
  void dispose() {
    _signUpRecognizer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    _signUpRecognizer.onTap = widget.onSignUp;

    return Text.rich(
      TextSpan(
        text: '${LocaleKeys.doNotHaveAnAccount}؟ ',
        style: TextStyle(
          color: AppColors.sokoonGray,
          fontFamily: ConstantManager.fontFamily,
          fontSize: 13.sp,
          fontWeight: FontWeight.w500,
        ),
        children: [
          TextSpan(
            text: LocaleKeys.signUp,
            recognizer: _signUpRecognizer,
            style: const TextStyle(
              color: AppColors.sokoonTeal,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
      textAlign: TextAlign.center,
    );
  }
}
