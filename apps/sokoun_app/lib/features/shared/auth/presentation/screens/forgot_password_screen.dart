import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:sokoun_app/features/shared/auth/presentation/cubits/forgot_password.dart';

import '../widgets/auth_scaffold.dart';
import '../widgets/forgot_password/forgot_password_form.dart';
import '../widgets/forgot_password/forgot_password_sent_view.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _emailController = TextEditingController();
  late final ForgotPasswordCubit _cubit;
  final ValueNotifier<({bool submitted, bool emailSent, String email})>
  _uiState = ValueNotifier<({bool submitted, bool emailSent, String email})>((
    submitted: false,
    emailSent: false,
    email: '',
  ));

  @override
  void initState() {
    super.initState();
    _cubit = ForgotPasswordCubit();
  }

  @override
  void dispose() {
    _emailController.dispose();
    _uiState.dispose();
    _cubit.close();
    super.dispose();
  }

  bool get _looksLikeValidEmail =>
      Validators.isValidEmail(_emailController.text);

  String get _maskedEmail {
    final List<String> parts = _emailController.text.trim().split('@');
    if (parts.length != 2 || parts.first.isEmpty) {
      return _emailController.text.trim();
    }

    final String localPart = parts.first;
    final int visibleLength = localPart.length >= 2 ? 2 : 1;
    return '${localPart.substring(0, visibleLength)}****@${parts.last}';
  }

  Future<void> _sendResetLink(BuildContext _) async {
    _uiState.value = (
      submitted: true,
      emailSent: _uiState.value.emailSent,
      email: _emailController.text,
    );
    if (_formKey.currentState?.validate() != true) {
      return;
    }

    await _cubit.sendResetLink(
      email: _emailController.text,
      onSuccess: () {
        if (mounted) {
          _uiState.value = (
            submitted: _uiState.value.submitted,
            emailSent: true,
            email: _emailController.text,
          );
        }
      },
    );
  }

  Future<void> _resend(VoidCallback onSuccess) async {
    await _cubit.sendResetLink(
      email: _emailController.text,
      onSuccess: onSuccess,
    );
  }

  void _showEmailForm() {
    _uiState.value = (
      submitted: false,
      emailSent: false,
      email: _emailController.text,
    );
  }

  void _handleBack() {
    if (_uiState.value.emailSent) {
      _showEmailForm();
    } else {
      Go.back();
    }
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<
      ({bool submitted, bool emailSent, String email})
    >(
      valueListenable: _uiState,
      builder: (context, uiState, _) => PopScope(
        canPop: !uiState.emailSent,
        onPopInvokedWithResult: (didPop, _) {
          if (!didPop) {
            _showEmailForm();
          }
        },
        child: AuthScaffold(
          showBackButton: true,
          isScrollable: false,
          padding: EdgeInsets.zero,
          backgroundColor: AppColors.offWhite,
          onBack: _handleBack,
          title: uiState.emailSent
              ? LocaleKeys.checkYourEmail
              : LocaleKeys.recoverPasswordTitle,
          child: Column(
            children: [
              Expanded(
                child: SingleChildScrollView(
                  keyboardDismissBehavior:
                      ScrollViewKeyboardDismissBehavior.onDrag,
                  padding: EdgeInsets.fromLTRB(24.w, 32.h, 24.w, 28.h),
                  child: uiState.emailSent
                      ? ForgotPasswordSentView(
                          maskedEmail: _maskedEmail,
                          onResend: _resend,
                          onChangeEmail: _showEmailForm,
                        )
                      : ForgotPasswordForm(
                          formKey: _formKey,
                          emailController: _emailController,
                          hasSubmittedInvalidEmail:
                              uiState.submitted && !_looksLikeValidEmail,
                          isEmailValid: _looksLikeValidEmail,
                          onEmailChanged: () {
                            _uiState.value = (
                              submitted: uiState.submitted,
                              emailSent: uiState.emailSent,
                              email: _emailController.text,
                            );
                          },
                          onSubmit: _sendResetLink,
                          onBackToLogin: Go.back,
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
