import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_feature.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/feature_workspace_guard.dart';
import '../../data/models/listing_ai_facts.dart';
import '../widgets/listing_ai_content.dart';

class ListingAiScreen extends StatelessWidget {
  const ListingAiScreen({
    super.key,
    this.facts,
    this.propertyId = '',
    this.canApply = false,
  });
  final ListingAiFacts? facts;
  final String propertyId;
  final bool canApply;
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.paidAiAssistant,
    showBackButton: true,
    body: FeatureWorkspaceGuard(
      feature: PremiumFeature.aiAssistant,
      workspace: AppWorkspace.owner,
      child: ListingAiContent(
        facts: facts,
        propertyId: propertyId,
        canApply: canApply,
      ),
    ),
  );
}
