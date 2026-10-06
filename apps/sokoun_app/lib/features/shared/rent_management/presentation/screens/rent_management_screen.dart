import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_feature.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/feature_workspace_guard.dart';
import '../widgets/rent_invoices_list.dart';

class RentManagementScreen extends StatelessWidget {
  const RentManagementScreen({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.paidRentManagement,
    showBackButton: true,
    body: FeatureWorkspaceGuard(
      feature: PremiumFeature.rentManagement,
      workspace: workspace,
      child: RentInvoicesList(workspace: workspace),
    ),
  );
}
