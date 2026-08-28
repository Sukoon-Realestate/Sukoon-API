import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
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
  static const String _basicInfoRoute = '/basic-info';
  static const String _kycIntroRoute = '/kyc-intro';
  static const String _uploadDocumentsRoute = '/upload-documents';
  static const String _pendingReviewRoute = '/pending-review';
  static const String _approvedRoute = '/approved';

  final GlobalKey<NavigatorState> _navigatorKey = GlobalKey<NavigatorState>();

  void _pushRoute(String route) {
    _navigatorKey.currentState?.pushNamed(route);
  }

  void _replaceRoute(String route) {
    _navigatorKey.currentState?.pushReplacementNamed(route);
  }

  void _goBack() {
    _navigatorKey.currentState?.pop();
  }

  void _handleBasicInfoSubmitted() {
    _pushRoute(_kycIntroRoute);
  }

  void _handleRegisterSuccess() {
    _replaceRoute(_pendingReviewRoute);
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
      child: Navigator(
        key: _navigatorKey,
        initialRoute: _basicInfoRoute,
        onGenerateRoute: (settings) {
          switch (settings.name) {
            case _basicInfoRoute:
              return MaterialPageRoute(
                builder: (_) => RegisterScreen(
                  userType: currentUserType,
                  onSubmit: _handleBasicInfoSubmitted,
                ),
              );
            case _kycIntroRoute:
              return MaterialPageRoute(
                builder: (context) => KycIntroScreen(
                  onBack: _goBack,
                  onUploadDocuments: () => _pushRoute(_uploadDocumentsRoute),
                  onSkip: () async => await context
                      .read<RegisterCubit>()
                      .register(onSuccess: _handleRegisterSuccess),
                ),
              );
            case _uploadDocumentsRoute:
              return MaterialPageRoute(
                builder: (_) => KycUploadDocumentsScreen(
                  onBack: _goBack,
                  onRegisterSuccess: _handleRegisterSuccess,
                ),
              );
            case _pendingReviewRoute:
              return MaterialPageRoute(
                builder: (context) {
                  final RegisterBody body = context
                      .read<RegisterCubit>()
                      .registerBody;

                  return KycPendingScreen(
                    fullName: '${body.firstName} ${body.lastName}'.trim(),
                    maskedNationalId: _maskedNationalId(body.nationalId),
                    onBackHome: () => _replaceRoute(_approvedRoute),
                  );
                },
              );
            case _approvedRoute:
              return MaterialPageRoute(
                builder: (_) => const KycApprovedScreen(),
              );
            default:
              return null;
          }
        },
      ),
    );
  }
}
