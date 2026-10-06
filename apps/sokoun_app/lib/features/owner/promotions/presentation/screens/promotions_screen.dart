import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_feature.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/feature_workspace_guard.dart';
import '../widgets/promotions_content.dart';

class PromotionsScreen extends StatelessWidget {
  const PromotionsScreen({super.key, this.property});
  final OwnerPropertyContent? property;
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.paidListingBoost,
    showBackButton: true,
    body: FeatureWorkspaceGuard(
      feature: PremiumFeature.listingBoost,
      workspace: AppWorkspace.owner,
      child: PromotionsContent(initialProperty: property),
    ),
  );
}
