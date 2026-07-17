import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';
import 'package:sokoun_app/features/auth/data/models/register.dart';
import 'package:sokoun_app/features/auth/presentation/cubits/register.dart';
import 'package:sokoun_app/shared_widgets/shared_widgets.dart';

import '../widgets/register/register_footer.dart';
import '../widgets/register/register_header.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key, this.onCreateAccount});

  final void Function({
    required String fullName,
    required String phone,
    required String email,
    required String password,
  })?
  onCreateAccount;

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _submit(BuildContext ctx) async {
    if (_formKey.currentState?.validate() != true) {
      return;
    }

    final RegisterBody body = RegisterBody(
      name: _nameController.text.trim(),
      phone: _phoneController.text.trim(),
      email: _emailController.text.trim(),
      password: _passwordController.text,
      rePassword: _confirmPasswordController.text,
    );

    await ctx.read<RegisterCubit>().register(
      body: body,
      onSuccess: () => widget.onCreateAccount?.call(
        fullName: body.name,
        phone: body.phone,
        email: body.email,
        password: body.password,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => RegisterCubit(),
      child: Scaffold(
        resizeToAvoidBottomInset: true,
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: LayoutBuilder(
            builder: (context, constraints) {
              return SingleChildScrollView(
                keyboardDismissBehavior:
                    ScrollViewKeyboardDismissBehavior.onDrag,
                child: ConstrainedBox(
                  constraints: BoxConstraints(minHeight: constraints.maxHeight),
                  child: Padding(
                    padding: EdgeInsets.symmetric(horizontal: 24.w),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          20.szH,
                          const RegisterHeader(),
                          26.szH,
                          SokoonNameField(
                            controller: _nameController,
                            validator: Validators.validateName,
                          ),
                          14.szH,
                          SokoonPhoneField(
                            controller: _phoneController,
                            validator: Validators.validateEmpty,
                          ),
                          14.szH,
                          SokoonEmailField(controller: _emailController),
                          14.szH,
                          SokoonPasswordField(
                            controller: _passwordController,
                            action: TextInputAction.next,
                          ),
                          14.szH,
                          SokoonPasswordConfirmationField(
                            controller: _confirmPasswordController,
                            passwordController: _passwordController,
                          ),
                          24.szH,
                          AppLoadingButton(
                            asyncCall: (ctx) async => await _submit(ctx),
                            title: LocaleKeys.createAccount,
                            buttonColor: AppColors.tealOrGoldBasedRole,
                            textColor: AppColors.white,
                            borderRadius: 14.r,
                            height: 52.h,
                            width: double.infinity,
                            fontSize: 16.sp,
                            fontWeight: FontWeight.w700,
                          ),
                          18.szH,
                          const RegisterFooter(),
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
