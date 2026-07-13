import 'package:flutter/material.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:sokoun_app/features/auth/presentation/screens/kyc_approved_screen.dart';
import 'package:sokoun_app/features/auth/presentation/screens/kyc_intro_screen.dart';
import 'package:sokoun_app/features/auth/presentation/screens/kyc_pending_screen.dart';
import 'package:sokoun_app/features/auth/presentation/screens/kyc_upload_documents_screen.dart';

class KycFlowScreen extends StatefulWidget {
  const KycFlowScreen({
    super.key,
    this.role = UserType.tenant,
    this.initialStep = 0,
    this.onBack,
    this.onUploadDocuments,
    this.onStartSearch,
  });

  final UserType role;
  final int initialStep;
  final VoidCallback? onBack;
  final VoidCallback? onUploadDocuments;
  final VoidCallback? onStartSearch;

  @override
  State<KycFlowScreen> createState() => _KycFlowScreenState();
}

class _KycFlowScreenState extends State<KycFlowScreen> {
  late int _step;

  @override
  void initState() {
    super.initState();
    _step = widget.initialStep;
  }

  @override
  void didUpdateWidget(covariant KycFlowScreen oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.initialStep != widget.initialStep) {
      _step = widget.initialStep;
    }
  }

  void _goToStep(int step) {
    if (_step == step) {
      return;
    }

    setState(() {
      _step = step;
    });
  }

  @override
  Widget build(BuildContext context) {
    return switch (_step) {
      0 => KycIntroScreen(
        onBack: widget.onBack,
        onUploadDocuments: widget.onUploadDocuments ?? () => _goToStep(1),
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
