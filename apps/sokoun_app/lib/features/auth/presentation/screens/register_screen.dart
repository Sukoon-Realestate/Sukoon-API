import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/shared/base_state.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'package:sokoun_app/features/auth/data/models/register.dart';
import 'package:sokoun_app/features/auth/presentation/cubits/register.dart';
import 'package:sokoun_app/shared_widgets/shared_widgets.dart';

import '../widgets/register/register_footer.dart';
import '../widgets/register/register_header.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({
    super.key,
    this.userType = UserType.tenant,
    this.onSubmit,
  });

  final UserType userType;
  final VoidCallback? onSubmit;

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameFieldKey = GlobalKey();
  final _phoneFieldKey = GlobalKey();
  final _emailFieldKey = GlobalKey();
  final _passwordFieldKey = GlobalKey();
  final _confirmPasswordFieldKey = GlobalKey();
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

  void _submit() {
    final _RegisterValidationError? firstValidationError = _firstValidationError;
    if (_formKey.currentState?.validate() != true) {
      if (firstValidationError != null) {
        _showValidationError(firstValidationError);
      }
      return;
    }

    final RegisterBody body = RegisterBody(
      name: _nameController.text.trim(),
      phone: _phoneController.text.trim(),
      email: _emailController.text.trim(),
      password: _passwordController.text,
      rePassword: _confirmPasswordController.text,
      userType: widget.userType.name,
    );

    context.read<RegisterCubit>().updateRegisterBody(body);
    widget.onSubmit?.call();
  }

  _RegisterValidationError? get _firstValidationError {
    for (final _RegisterFieldValidation field in _validationFields) {
      final String? error = field.validator(field.value);
      if (error != null && error.trim().isNotEmpty) {
        return _RegisterValidationError(field: field, message: error);
      }
    }

    return null;
  }

  List<_RegisterFieldValidation> get _validationFields {
    return [
      _RegisterFieldValidation(
        key: _nameFieldKey,
        title: LocaleKeys.fullName,
        value: _nameController.text,
        validator: Validators.validateName,
      ),
      _RegisterFieldValidation(
        key: _phoneFieldKey,
        title: LocaleKeys.phoneNumber,
        value: _phoneController.text,
        validator: Validators.validateEmpty,
      ),
      _RegisterFieldValidation(
        key: _emailFieldKey,
        title: LocaleKeys.email,
        value: _emailController.text,
        validator: Validators.validateEmail,
      ),
      _RegisterFieldValidation(
        key: _passwordFieldKey,
        title: LocaleKeys.password,
        value: _passwordController.text,
        validator: Validators.validatePassword,
      ),
      _RegisterFieldValidation(
        key: _confirmPasswordFieldKey,
        title: LocaleKeys.confirmPassword,
        value: _confirmPasswordController.text,
        validator: (value) => Validators.validatePasswordConfirmation(
          value,
          password: _passwordController.text,
        ),
      ),
    ];
  }

  void _showValidationError(_RegisterValidationError error) {
    Messages.showToast(
      title: error.field.title,
      msg: error.message,
      status: BaseStatus.error,
    );

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }

      final BuildContext? fieldContext = error.field.key.currentContext;
      if (fieldContext == null) {
        return;
      }

      Scrollable.ensureVisible(
        fieldContext,
        duration: const Duration(milliseconds: 350),
        curve: Curves.easeOutCubic,
        alignment: 0.12,
      );
    });
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
                        20.szH,
                        const RegisterHeader(),
                        26.szH,
                        SokoonNameField(
                          key: _nameFieldKey,
                          controller: _nameController,
                          validator: Validators.validateName,
                        ),
                        14.szH,
                        SokoonPhoneField(
                          key: _phoneFieldKey,
                          controller: _phoneController,
                          validator: Validators.validateEmpty,
                        ),
                        14.szH,
                        SokoonEmailField(
                          key: _emailFieldKey,
                          controller: _emailController,
                          validator: Validators.validateEmail,
                        ),
                        14.szH,
                        SokoonPasswordField(
                          key: _passwordFieldKey,
                          controller: _passwordController,
                          action: TextInputAction.next,
                          validator: Validators.validatePassword,
                        ),
                        14.szH,
                        SokoonPasswordConfirmationField(
                          key: _confirmPasswordFieldKey,
                          controller: _confirmPasswordController,
                          passwordController: _passwordController,
                          validator: (value) =>
                              Validators.validatePasswordConfirmation(
                                value,
                                password: _passwordController.text,
                              ),
                        ),
                        24.szH,
                        DefaultButton(
                          onTap: _submit,
                          title: LocaleKeys.createAccount,
                          color: AppColors.tealOrGoldBasedRole,
                          textColor: AppColors.white,
                          borderRadius: BorderRadius.circular(14.r),
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
    );
  }
}

class _RegisterFieldValidation {
  const _RegisterFieldValidation({
    required this.key,
    required this.title,
    required this.value,
    required this.validator,
  });

  final GlobalKey key;
  final String title;
  final String value;
  final FormFieldValidator<String?> validator;
}

class _RegisterValidationError {
  const _RegisterValidationError({required this.field, required this.message});

  final _RegisterFieldValidation field;
  final String message;
}
