import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:sokoun_app/features/shared/auth/data/models/register.dart';
import 'package:sokoun_app/features/shared/auth/presentation/cubits/register.dart';

import 'kyc_approved_screen.dart';
import 'kyc_intro_screen.dart';
import 'kyc_pending_screen.dart';
import 'kyc_upload_documents_screen.dart';
import 'otp_screen.dart';
import 'register_screen.dart';

class RegisterFlowScreen extends StatefulWidget {
  const RegisterFlowScreen({super.key});

  @override
  State<RegisterFlowScreen> createState() => _RegisterFlowScreenState();
}

class _RegisterFlowScreenState extends State<RegisterFlowScreen> {
  late final PageController _pageController;
  final List<_RegisterFlowStep> _stepHistory = [_RegisterFlowStep.basicInfo];
  _RegisterFlowStep _currentStep = _RegisterFlowStep.basicInfo;
  String _registeredEmail = '';

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _goToStep(_RegisterFlowStep step) {
    if (_stepHistory.last != step) {
      _stepHistory.add(step);
    }
    _animateToStep(step);
  }

  void _goBack() {
    if (_stepHistory.length <= 1) {
      return;
    }

    _stepHistory.removeLast();
    _animateToStep(_stepHistory.last);
  }

  void _animateToStep(_RegisterFlowStep step) {
    if (!mounted || !_pageController.hasClients) {
      return;
    }

    _pageController.animateToPage(
      step.index,
      duration: const Duration(milliseconds: 280),
      curve: Curves.easeOutCubic,
    );
  }

  void _handlePageChanged(int index) {
    final _RegisterFlowStep step = _RegisterFlowStep.values[index];
    if (_currentStep == step) {
      return;
    }

    setState(() => _currentStep = step);
  }

  void _handleBasicInfoSubmitted() {
    _goToStep(_RegisterFlowStep.kycIntro);
  }

  void _handleRegisterSuccess(RegisterBody body) {
    if (!mounted) {
      return;
    }

    setState(() => _registeredEmail = body.email);
    _goToStep(_RegisterFlowStep.verifyEmail);
  }

  void _handleEmailVerified() {
    _goToStep(_RegisterFlowStep.pendingReview);
  }

  String _maskedNationalId(String? value) {
    final String nationalId = value ?? '';
    if (nationalId.length < 4) {
      return nationalId;
    }

    return '${nationalId.substring(0, 2)}*********${nationalId.substring(nationalId.length - 2)}';
  }

  @override
  Widget build(BuildContext context) {
    final currentUserType = UserTypeHelper.instance.currentUserType;
    return BlocProvider(
      create: (_) => RegisterCubit(),
      child: Builder(
        builder: (context) => PopScope(
          canPop: _currentStep == _RegisterFlowStep.basicInfo,
          onPopInvokedWithResult: (didPop, _) {
            if (!didPop) {
              _goBack();
            }
          },
          child: PageView(
            controller: _pageController,
            physics: const NeverScrollableScrollPhysics(),
            onPageChanged: _handlePageChanged,
            children: [
              for (final Widget step in _buildSteps(context, currentUserType))
                _KeepAlivePage(child: step),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _buildSteps(BuildContext context, UserType currentUserType) {
    return [
      RegisterScreen(
        userType: currentUserType,
        onSubmit: _handleBasicInfoSubmitted,
      ),
      KycIntroScreen(
        onBack: _goBack,
        onUploadDocuments: () => _goToStep(_RegisterFlowStep.uploadDocuments),
        onSkip: () async {
          context.read<RegisterCubit>()..removeDocs()..register(
            onSuccess: _handleRegisterSuccess,
          );
        }
      ),
      KycUploadDocumentsScreen(
        onBack: _goBack,
        onRegisterSuccess: _handleRegisterSuccess,
      ),
      OtpScreen(email: _registeredEmail, onVerified: _handleEmailVerified),
      KycPendingScreen(
        fullName: _fullName(context),
      ),

      const KycApprovedScreen(),
    ];
  }

  String _fullName(BuildContext context) {
    final RegisterBody body = context.read<RegisterCubit>().registerBody;
    return '${body.firstName} ${body.lastName}'.trim();
  }
}

class _KeepAlivePage extends StatefulWidget {
  const _KeepAlivePage({required this.child});

  final Widget child;

  @override
  State<_KeepAlivePage> createState() => _KeepAlivePageState();
}

class _KeepAlivePageState extends State<_KeepAlivePage>
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;

  @override
  Widget build(BuildContext context) {
    super.build(context);
    return widget.child;
  }
}

enum _RegisterFlowStep {
  basicInfo,
  kycIntro,
  uploadDocuments,
  verifyEmail,
  pendingReview,
  approved,
}
