import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';
import 'package:sokoun_app/features/main_view/presentation/screens/view.dart';
import 'package:sokoun_app/features/shared/auth/data/models/google_login.dart';
import 'package:sokoun_app/features/shared/auth/presentation/cubits/google_login.dart';
import 'package:sokoun_app/features/shared/auth/presentation/cubits/login.dart';
import 'package:sokoun_app/shared_widgets/shared_widgets.dart';

import '../widgets/auth_scaffold.dart';
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

  Future<void> _submit(BuildContext ctx) async {
    if (_formKey.currentState?.validate() != true) {
      return;
    }

    await ctx.read<LoginCubit>().login(
      email: _emailController.text.trim(),
      password: _passwordController.text,
      onSuccess: () => Go.offAll(const HomeScreen()),
    );
  }

  Future<void> _submitGoogle(BuildContext context, String token) async {
    await context.read<GoogleLoginCubit>().login(
      body: GoogleLoginBody(token: token),
      onSuccess: () => Go.offAll(const HomeScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (context) => LoginCubit()),
        BlocProvider(create: (context) => GoogleLoginCubit()),
      ],
      child: AuthScaffold(
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const LoginHeader(),
              24.szH,
              SokoonEmailField(
                controller: _emailController,
                hintText: 'ahmed@gmail.com',
              ),
              16.szH,
              SokoonPasswordField(controller: _passwordController),
              10.szH,
              TextButton(
                onPressed: () {},
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
              ).startWidget,
              14.szH,
              AppLoadingButton(
                asyncCall: _submit,
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
              // Builder(
              //   builder: (context) => AppGoogleSignInButton(
              //     onSuccess: (token) => _submitGoogle(context, token),
              //   ),
              // ),
              // 12.szH,
              // AppFacebookSignInButton(onSuccess: (token) async {}),
              // 12.szH,
              // SokoonAppleSignInButton(),
              // 16.szH,
              TextButton(
                onPressed: () {},
                style: TextButton.styleFrom(
                  minimumSize: Size.zero,
                  padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                child: AppText(
                  LocaleKeys.signInAsVisitor,
                  color: AppColors.sokoonGray,
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w700,
                  decoration: TextDecoration.underline,
                ),
              ).centerWidget,
              18.szH,
              LoginFooter(),
              24.szH,
            ],
          ),
        ),
      ),
    );
  }
}
