import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import '../../../data/enums/premium_feature.dart';
import 'premium_empty_state.dart';

/// Feature access depends on workspace responsibilities, never on payment.
class FeatureWorkspaceGuard extends StatelessWidget {
  const FeatureWorkspaceGuard({
    super.key,
    required this.feature,
    required this.workspace,
    required this.child,
  });
  final PremiumFeature feature;
  final AppWorkspace workspace;
  final Widget child;
  @override
  Widget build(BuildContext context) =>
      (feature.ownerOnly && !workspace.isOwner) ||
          (feature.tenantOnly && !workspace.isTenant)
      ? SingleChildScrollView(
          child: PremiumEmptyState(
            title: LocaleKeys.paidUnavailable,
            description: LocaleKeys.paidUnavailableBody,
          ),
        )
      : child;
}
