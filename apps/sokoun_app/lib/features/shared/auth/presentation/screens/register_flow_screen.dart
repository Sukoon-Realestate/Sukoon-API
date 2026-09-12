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
import 'register_screen.dart';

class RegisterFlowScreen extends StatefulWidget {
  const RegisterFlowScreen({super.key});

  @override
  State<RegisterFlowScreen> createState() => _RegisterFlowScreenState();
}

class _RegisterFlowScreenState extends State<RegisterFlowScreen> {
  _RegisterFlowStep _step = _RegisterFlowStep.basicInfo;

  void _goBack() {
    setState(() {
      _step = switch (_step) {
        _RegisterFlowStep.uploadDocuments => _RegisterFlowStep.kycIntro,
        _ => _RegisterFlowStep.basicInfo,
      };
    });
  }

  void _handleBasicInfoSubmitted() {
    setState(() => _step = _RegisterFlowStep.kycIntro);
  }

  void _handleRegisterSuccess() {
    setState(() => _step = _RegisterFlowStep.pendingReview);
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
        builder: (context) => _buildCurrentStep(context, currentUserType),
      ),
    );
  }

  Widget _buildCurrentStep(BuildContext context, UserType currentUserType) {
    return switch (_step) {
      _RegisterFlowStep.basicInfo => RegisterScreen(
        userType: currentUserType,
        onSubmit: _handleBasicInfoSubmitted,
      ),
      _RegisterFlowStep.kycIntro => KycIntroScreen(
        onBack: _goBack,
        onUploadDocuments: () {
          setState(() => _step = _RegisterFlowStep.uploadDocuments);
        },
        onSkip: () async => context.read<RegisterCubit>().register(
          onSuccess: _handleRegisterSuccess,
        ),
      ),
      _RegisterFlowStep.uploadDocuments => KycUploadDocumentsScreen(
        onBack: _goBack,
        onRegisterSuccess: _handleRegisterSuccess,
      ),
      _RegisterFlowStep.pendingReview => KycPendingScreen(
        fullName: _fullName(context),
        maskedNationalId: _maskedNationalId(
          context.read<RegisterCubit>().registerBody.nationalId,
        ),
        onBackHome: () {
          setState(() => _step = _RegisterFlowStep.approved);
        },
      ),
      _RegisterFlowStep.approved => const KycApprovedScreen(),
    };
  }

  String _fullName(BuildContext context) {
    final RegisterBody body = context.read<RegisterCubit>().registerBody;
    return '${body.firstName} ${body.lastName}'.trim();
  }
}

enum _RegisterFlowStep {
  basicInfo,
  kycIntro,
  uploadDocuments,
  pendingReview,
  approved,
}
