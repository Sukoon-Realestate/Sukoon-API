import 'package:flutter/material.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';

import 'kyc_flow_screen.dart';
import 'kyc_upload_documents_screen.dart';
import 'register_screen.dart';

class RegisterFlowScreen extends StatefulWidget {
  const RegisterFlowScreen({super.key});

  @override
  State<RegisterFlowScreen> createState() => _RegisterFlowScreenState();
}

class _RegisterFlowScreenState extends State<RegisterFlowScreen> {
  static const int _registerPage = 0;
  static const int _kycIntroPage = 1;
  static const int _uploadDocumentsPage = 2;

  final PageController _pageController = PageController();
  int _kycStep = 0;

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _goToPage(int page) {
    if (!_pageController.hasClients) {
      return;
    }

    _pageController.animateToPage(
      page,
      duration: const Duration(milliseconds: 280),
      curve: Curves.easeOutCubic,
    );
  }

  void _showRegister() {
    _goToPage(_registerPage);
  }

  void _showKycIntro() {
    setState(() {
      _kycStep = 0;
    });
    _goToPage(_kycIntroPage);
  }

  void _showUploadDocuments() {
    _goToPage(_uploadDocumentsPage);
  }

  void _showPendingReview(KycDocumentUploadData data) {
    setState(() {
      _kycStep = 2;
    });
    _goToPage(_kycIntroPage);
  }

  void _handleCreateAccount({
    required String fullName,
    required String phone,
    required String email,
    required String password,
  }) {
    _showKycIntro();
  }

  @override
  Widget build(BuildContext context) {
    final currentUserType = UserTypeHelper.instance.currentUserType;

    return PageView(
      controller: _pageController,
      physics: const NeverScrollableScrollPhysics(),
      children: [
        RegisterScreen(onCreateAccount: _handleCreateAccount),
        KycFlowScreen(
          role: currentUserType,
          initialStep: _kycStep,
          onBack: _showRegister,
          onUploadDocuments: _showUploadDocuments,
        ),
        KycUploadDocumentsScreen(
          onBack: _showKycIntro,
          onSubmit: _showPendingReview,
        ),
      ],
    );
  }
}
