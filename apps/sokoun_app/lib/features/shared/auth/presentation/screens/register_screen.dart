import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:melos_core/core/widgets/first_validation_error_form.dart';
import 'package:sokoun_app/features/shared/auth/data/models/register.dart';
import 'package:sokoun_app/features/shared/auth/presentation/cubits/register.dart';
import 'package:sokoun_app/shared_widgets/shared_widgets.dart';

import '../widgets/auth_scaffold.dart';
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
  final _firstNameFieldKey = GlobalKey();
  final _lastNameFieldKey = GlobalKey();
  final _phoneFieldKey = GlobalKey();
  final _emailFieldKey = GlobalKey();
  final _passwordFieldKey = GlobalKey();
  final _confirmPasswordFieldKey = GlobalKey();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  void _submit() {
    final RegisterBody body = RegisterBody(
      firstName: _firstNameController.text.trim(),
      lastName: _lastNameController.text.trim(),
      phone: _phoneController.text.trim(),
      email: _emailController.text.trim(),
      password: _passwordController.text,
      rePassword: _confirmPasswordController.text,
      userType: widget.userType.name,
    );

    context.read<RegisterCubit>().updateRegisterBody(body);
    widget.onSubmit?.call();
  }

  List<FirstValidationErrorField> _validationFields() {
    return [
      FirstValidationErrorField(
        fieldKey: _firstNameFieldKey,
        title: LocaleKeys.firstName,
        value: _firstNameController.text,
        validator: Validators.validateName,
      ),
      FirstValidationErrorField(
        fieldKey: _lastNameFieldKey,
        title: LocaleKeys.lastName,
        value: _lastNameController.text,
        validator: Validators.validateName,
      ),
      FirstValidationErrorField(
        fieldKey: _phoneFieldKey,
        title: LocaleKeys.phoneNumber,
        value: _phoneController.text,
        validator: Validators.validateEmpty,
      ),
      FirstValidationErrorField(
        fieldKey: _emailFieldKey,
        title: LocaleKeys.email,
        value: _emailController.text,
        validator: Validators.validateEmail,
      ),
      FirstValidationErrorField(
        fieldKey: _passwordFieldKey,
        title: LocaleKeys.password,
        value: _passwordController.text,
        validator: Validators.validatePassword,
      ),
      FirstValidationErrorField(
        fieldKey: _confirmPasswordFieldKey,
        title: LocaleKeys.confirmPassword,
        value: _confirmPasswordController.text,
        validator: (value) => Validators.validatePasswordConfirmation(
          value,
          password: _passwordController.text,
        ),
      ),
    ];
  }

  @override
  Widget build(BuildContext context) {
    return AuthScaffold(
      child: FirstValidationErrorForm(
        validationFields: _validationFields,
        onValid: _submit,
        builder: (context, submit) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const RegisterHeader(),
              26.szH,
              SokoonNameField(
                key: _firstNameFieldKey,
                controller: _firstNameController,
                label: LocaleKeys.firstName,
                hintText: LocaleKeys.firstNameHint,
                validator: Validators.validateName,
              ),
              14.szH,
              SokoonNameField(
                key: _lastNameFieldKey,
                controller: _lastNameController,
                label: LocaleKeys.lastName,
                hintText: LocaleKeys.lastNameHint,
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
                validator: (value) => Validators.validatePasswordConfirmation(
                  value,
                  password: _passwordController.text,
                ),
              ),
              24.szH,
              DefaultButton(
                onTap: submit,
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
          );
        },
      ),
    );
  }
}
