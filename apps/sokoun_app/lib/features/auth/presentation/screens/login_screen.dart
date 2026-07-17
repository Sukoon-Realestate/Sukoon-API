import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';
import 'package:sokoun_app/features/auth/presentation/cubits/login.dart';
import 'package:sokoun_app/shared_widgets/shared_widgets.dart';
import '../widgets/login/login_divider.dart';
import '../widgets/login/login_footer.dart';
import '../widgets/login/login_header.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

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

  Future<void> _submit(BuildContext ctx) async{
    if (_formKey.currentState?.validate() != true) {
      return;
    }

    await ctx.read<LoginCubit>().login(
        email: _emailController.text,
        password: _passwordController.text
    );
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => LoginCubit(),
      child: Scaffold(
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
                          ),
                          16.szH,
                          SokoonPasswordField(controller: _passwordController),
                          10.szH,
                          Align(
                            alignment: AlignmentDirectional.centerStart,
                            child: TextButton(
                              onPressed: (){},
                              style: TextButton.styleFrom(
                                minimumSize: Size.zero,
                                padding: EdgeInsets.zero,
                                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                              ),
                              child: AppText(
                                LocaleKeys.forgotPassword,
                                color: AppColors.tealOrGoldBasedRole,
                                fontSize: 12.sp,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                          14.szH,
                          AppLoadingButton(
                            asyncCall: (ctx)async => await _submit(ctx),
                            title: LocaleKeys.login,
                            buttonColor: AppColors.tealOrGoldBasedRole,
                            textColor: AppColors.white,
                            borderRadius: 14.r,
                            fontSize: 16.sp,
                            fontWeight: FontWeight.w700,
                          ),
                          20.szH,
                          const LoginDivider(),
                          18.szH,
                          SokoonGoogleSignInButton(),
                          12.szH,
                          SokoonFacebookSignInButton(),
                          12.szH,
                          SokoonAppleSignInButton(),
                          16.szH,
                          Center(
                            child: TextButton(
                              onPressed: (){},
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
                          18.szH,
                          LoginFooter(),
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
      ),
    );
  }
}
