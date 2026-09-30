import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/login_screen.dart';
import 'package:sokoun_app/features/shared/public_pages/presentation/widgets/public_page_menu.dart';

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
    _loginRecognizer.onTap = () => Go.off(const LoginScreen());
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text.rich(
          TextSpan(
            text: '${LocaleKeys.alreadyHaveAnAccount}؟ ',
            style: AppTextStyles.medium13.copyWith(
              color: AppColors.sokoonGray,
              fontSize: 13.sp,
              height: 1.45,
            ),
            children: [
              TextSpan(
                text: LocaleKeys.login,
                recognizer: _loginRecognizer,
                style: AppTextStyles.extraBold.copyWith(
                  color: AppColors.sokoonTeal,
                ),
              ),
            ],
          ),
          textAlign: TextAlign.center,
        ),
        const PublicPageMenu(),
      ],
    );
  }
}
