import 'package:flutter/material.dart';
import 'package:melos_core/core/shared/models/user_enum.dart';
import 'package:sokoun_app/features/auth/presentation/screens/kyc_approved_screen.dart';
import 'package:sokoun_app/features/auth/presentation/screens/kyc_intro_screen.dart';
import 'package:sokoun_app/features/auth/presentation/screens/kyc_pending_screen.dart';
import 'package:sokoun_app/features/auth/presentation/screens/kyc_upload_documents_screen.dart';

class TenantKycFlowScreen extends StatefulWidget {
  const TenantKycFlowScreen({
    super.key,
    this.role = UserType.tenant,
    this.onBack,
    this.onStartSearch,
  });

  final UserType role;
  final VoidCallback? onBack;
  final VoidCallback? onStartSearch;

  @override
  State<TenantKycFlowScreen> createState() => _TenantKycFlowScreenState();
}

class _TenantKycFlowScreenState extends State<TenantKycFlowScreen> {
  int _step = 0;

  void _goToStep(int step) {
    setState(() {
      _step = step;
    });
  }

  @override
  Widget build(BuildContext context) {
    return switch (_step) {
      0 => KycIntroScreen(
        onBack: widget.onBack,
        onUploadDocuments: () => _goToStep(1),
      ),
      1 => KycUploadDocumentsScreen(
        onBack: () => _goToStep(0),
        onSubmit: (_) => _goToStep(2),
      ),
      2 => KycPendingScreen(onBackHome: () => _goToStep(3)),
      _ => KycApprovedScreen(onStartSearch: widget.onStartSearch),
    };
  }
}
