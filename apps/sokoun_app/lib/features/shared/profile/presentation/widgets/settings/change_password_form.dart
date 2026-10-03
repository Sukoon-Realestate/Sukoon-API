part of '../../../imports.dart';

class ChangePasswordForm extends StatefulWidget {
  const ChangePasswordForm({super.key});
  @override
  State<ChangePasswordForm> createState() => _ChangePasswordFormState();
}

class _ChangePasswordFormState extends State<ChangePasswordForm> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
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
    if (_cubit.isLoading || !(_formKey.currentState?.validate() ?? false)) {
      return;
    }
    FocusScope.of(context).unfocus();
    if (!await _cubit.save(_body) || !context.mounted) return;
    _saved = true;
    MessageUtils.showSnackBar(
      LocaleKeys.settingsPasswordSaved,
      textColor: AppColors.sokoonTeal,
      context: context,
    );
    Go.back();
  }

  @override
  Widget build(BuildContext context) => UnsavedChangesGuard(
    hasChanges: () =>
        !_saved &&
        (_current.text.isNotEmpty ||
            _password.text.isNotEmpty ||
            _confirmation.text.isNotEmpty),
    isSaving: () => _cubit.isLoading,
    child: Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            padding: EdgeInsets.all(20.r),
            child: BlocBuilder<ChangePasswordCubit, AsyncState<bool>>(
              bloc: _cubit,
              builder: (context, state) => AbsorbPointer(
                absorbing: state.isLoading,
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    spacing: 20.h,
                    children: [
                      AppText(
                        LocaleKeys.settingsPasswordIntro,
                        style: AppTextStyles.regular14.copyWith(
                          color: AppColors.sokoonGray,
                          height: 1.5,
                        ),
                      ),
                      SokoonPasswordField(
                        controller: _current,
                        label: LocaleKeys.settingsCurrentPassword,
                        action: TextInputAction.next,
                        validator: Validators.validateLoginPassword,
                        onChanged: (value) => _body = _body.copyWith(
                          currentPassword: value ?? '',
                        ),
                      ),
                      SokoonPasswordField(
                        controller: _password,
                        label: LocaleKeys.createNewPassword,
                        action: TextInputAction.next,
                        onChanged: (value) =>
                            _body = _body.copyWith(newPassword: value ?? ''),
                      ),
                      SokoonPasswordConfirmationField(
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
        ),
        SokounActionFooter(
          width: SokounContentWidth.form,
          child: AppLoadingButton(
            asyncCall: _save,
            title: LocaleKeys.settingsSavePassword,
          ),
        ),
      ],
    ),
  );
}
