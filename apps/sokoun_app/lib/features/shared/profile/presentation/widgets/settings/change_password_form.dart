part of '../../../imports.dart';

class ChangePasswordForm extends StatefulWidget {
  const ChangePasswordForm({super.key});
  @override
  State<ChangePasswordForm> createState() => _ChangePasswordFormState();
}

class _ChangePasswordFormState extends State<ChangePasswordForm> {
  final GlobalKey _currentFieldKey = GlobalKey();
  final GlobalKey _passwordFieldKey = GlobalKey();
  final GlobalKey _confirmationFieldKey = GlobalKey();
  final TextEditingController _current = TextEditingController();
  final TextEditingController _password = TextEditingController();
  final TextEditingController _confirmation = TextEditingController();
  late final ChangePasswordCubit _cubit;
  ChangePasswordBody _body = const ChangePasswordBody.initial();
  bool _saved = false;
  @override
  void initState() {
    super.initState();
    _cubit = ChangePasswordCubit();
  }

  @override
  void dispose() {
    _current.dispose();
    _password.dispose();
    _confirmation.dispose();
    _cubit.close();
    super.dispose();
  }

  Future<void> _save(BuildContext context) async {
    if (_cubit.isLoading) {
      return;
    }
    if (!await _cubit.save(_body) || !context.mounted) return;
    _saved = true;
    Go.back();
  }

  List<FirstValidationErrorField> _validationFields() => [
    FirstValidationErrorField(
      fieldKey: _currentFieldKey,
      title: LocaleKeys.settingsCurrentPassword,
      value: _current.text,
      validator: Validators.validateLoginPassword,
    ),
    FirstValidationErrorField(
      fieldKey: _passwordFieldKey,
      title: LocaleKeys.createNewPassword,
      value: _password.text,
      validator: Validators.validatePassword,
    ),
    FirstValidationErrorField(
      fieldKey: _confirmationFieldKey,
      title: LocaleKeys.confirmPassword,
      value: _confirmation.text,
      validator: (value) => Validators.validatePasswordConfirmation(
        value,
        password: _password.text,
      ),
    ),
  ];

  @override
  Widget build(BuildContext context) => UnsavedChangesGuard(
    hasChanges: () =>
        !_saved &&
        (_current.text.isNotEmpty ||
            _password.text.isNotEmpty ||
            _confirmation.text.isNotEmpty),
    isSaving: () => _cubit.isLoading,
    child: FirstValidationErrorForm(
      validationFields: _validationFields,
      onValid: () => _save(context),
      builder: (context, submit) => Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              padding: EdgeInsets.all(20.r),
              child: BlocBuilder<ChangePasswordCubit, AsyncState<bool>>(
                bloc: _cubit,
                builder: (context, state) => AbsorbPointer(
                  absorbing: state.isLoading,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    spacing: 20.h,
                    children: [
                      AppText(
                        LocaleKeys.settingsPasswordIntro,
                        style: AppTextStyles.regular14.copyWith(
                          color: context.appColor(AppColors.sokoonGray),
                          height: 1.5,
                        ),
                      ),
                      SokoonPasswordField(
                        key: _currentFieldKey,
                        controller: _current,
                        label: LocaleKeys.settingsCurrentPassword,
                        action: TextInputAction.next,
                        validator: Validators.validateLoginPassword,
                        onChanged: (value) => _body = _body.copyWith(
                          currentPassword: value ?? '',
                        ),
                      ),
                      SokoonPasswordField(
                        key: _passwordFieldKey,
                        controller: _password,
                        label: LocaleKeys.createNewPassword,
                        action: TextInputAction.next,
                        onChanged: (value) =>
                            _body = _body.copyWith(newPassword: value ?? ''),
                      ),
                      SokoonPasswordConfirmationField(
                        key: _confirmationFieldKey,
                        controller: _confirmation,
                        passwordController: _password,
                        onChanged: (value) =>
                            _body = _body.copyWith(confirmation: value ?? ''),
                      ),
                      ProfileVerificationBanner(
                        title: LocaleKeys.settingsPasswordPolicyTitle,
                        description:
                            LocaleKeys.settingsPasswordPolicyDescription,
                        isPrivacy: true,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          SokounActionFooter(
            width: SokounContentWidth.form,
            child: AppLoadingButton(
              asyncCall: (_) => submit(),
              title: LocaleKeys.settingsSavePassword,
            ),
          ),
        ],
      ),
    ),
  );
}
