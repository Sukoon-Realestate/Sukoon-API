import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/register_flow_screen.dart';

class LoginFooter extends StatefulWidget {
  const LoginFooter({super.key});

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
    _signUpRecognizer.onTap = () => Go.to(const RegisterFlowScreen());
    return Text.rich(
      TextSpan(
        text: '${LocaleKeys.doNotHaveAnAccount}؟ ',
        style: AppTextStyles.medium13.copyWith(
          color: AppColors.sokoonGray,
          fontSize: 13.sp,
          height: 1.45,
        ),
        children: [
          TextSpan(
            text: LocaleKeys.signUp,
            recognizer: _signUpRecognizer,
            style: AppTextStyles.extraBold.copyWith(
              color: AppColors.sokoonTeal,
            ),
          ),
        ],
      ),
      textAlign: TextAlign.center,
    );
  }
}
