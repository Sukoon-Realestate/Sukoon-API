import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/auth/presentation/screens/login_screen.dart';

class RegisterFooter extends StatefulWidget {
  const RegisterFooter({super.key});

  @override
  State<RegisterFooter> createState() => _RegisterFooterState();
}

class _RegisterFooterState extends State<RegisterFooter> {
  late final TapGestureRecognizer _loginRecognizer;

  @override
  void initState() {
    super.initState();
    _loginRecognizer = TapGestureRecognizer();
  }

  @override
  void dispose() {
    _loginRecognizer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isTenant = UserTypeHelper.instance.currentUserType.isTenant;

    _loginRecognizer.onTap = () => Go.offAll(const LoginScreen());
    return Text.rich(
      TextSpan(
        text: '${LocaleKeys.alreadyHaveAnAccount}؟ ',
        style: TextStyle(
          color: AppColors.sokoonGray,
          fontFamily: ConstantManager.fontFamily,
          fontSize: 13.sp,
          fontWeight: FontWeight.w500,
        ),
        children: [
          TextSpan(
            text: LocaleKeys.login,
            recognizer: _loginRecognizer,
            style: TextStyle(
              color: isTenant ? AppColors.sokoonTeal : AppColors.gold,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
      textAlign: TextAlign.center,
    );
  }
}
