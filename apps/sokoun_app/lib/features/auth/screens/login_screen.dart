import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/auth/screens/widgets/login/login_divider.dart';
import 'package:sokoun_app/features/auth/screens/widgets/login/login_header.dart';
import 'package:sokoun_app/shared_widgets/shared_widgets.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({
    super.key,
    this.onLogin,
    this.onForgotPassword,
    this.onGoogleSignIn,
    this.onFacebookSignIn,
    this.onAppleSignIn,
    this.onVisitorSignIn,
  });

  final void Function(String email, String password)? onLogin;
  final VoidCallback? onForgotPassword;
  final VoidCallback? onGoogleSignIn;
  final VoidCallback? onFacebookSignIn;
  final VoidCallback? onAppleSignIn;
  final VoidCallback? onVisitorSignIn;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_formKey.currentState?.validate() != true) {
      return;
    }

    widget.onLogin?.call(
      _emailController.text.trim(),
      _passwordController.text,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: true,
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight),
                child: Padding(
                  padding: EdgeInsets.symmetric(horizontal: 24.w),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        34.szH,
                        const LoginHeader(),
                        24.szH,
                        SokoonEmailField(
                          controller: _emailController,
                          hintText: 'ahmed@gmail.com',
                          textAlign: TextAlign.right,
                        ),
                        16.szH,
                        SokoonPasswordField(controller: _passwordController),
                        10.szH,
                        Align(
                          alignment: AlignmentDirectional.centerStart,
                          child: TextButton(
                            onPressed: widget.onForgotPassword,
                            style: TextButton.styleFrom(
                              minimumSize: Size.zero,
                              padding: EdgeInsets.zero,
                              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                            ),
                            child: AppText(
                              LocaleKeys.forgotPassword,
                              color: AppColors.sokoonTeal,
                              fontSize: 12.sp,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                        14.szH,
                        DefaultButton(
                          onTap: _submit,
                          title: LocaleKeys.login,
                          color: AppColors.sokoonTeal,
                          textColor: AppColors.white,
                          borderRadius: BorderRadius.circular(14.r),
                          height: 52.h,
                          width: double.infinity,
                          fontSize: 16.sp,
                          fontWeight: FontWeight.w700,
                        ),
                        20.szH,
                        const LoginDivider(),
                        18.szH,
                        SokoonGoogleSignInButton(onTap: widget.onGoogleSignIn),
                        12.szH,
                        SokoonFacebookSignInButton(
                          onTap: widget.onFacebookSignIn,
                        ),
                        12.szH,
                        SokoonAppleSignInButton(onTap: widget.onAppleSignIn),
                        16.szH,
                        Center(
                          child: TextButton(
                            onPressed: widget.onVisitorSignIn,
                            style: TextButton.styleFrom(
                              minimumSize: Size.zero,
                              padding: EdgeInsets.symmetric(
                                horizontal: 8.w,
                                vertical: 4.h,
                              ),
                              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                            ),
                            child: AppText(
                              LocaleKeys.signInAsVisitor,
                              color: AppColors.sokoonGray,
                              fontSize: 13.sp,
                              fontWeight: FontWeight.w700,
                              decoration: TextDecoration.underline,
                            ),
                          ),
                        ),
                        24.szH,
                      ],
                    ),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
