import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import '../../../data/enums/premium_feature.dart';
import 'premium_feature_tile.dart';

class PremiumDashboard extends StatelessWidget {
  const PremiumDashboard({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    padding: const EdgeInsets.all(20),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(LocaleKeys.toolsSubtitle),
        16.szH,
        for (final feature in PremiumFeature.values.where(
          (feature) =>
              (!feature.ownerOnly || workspace.isOwner) &&
              (!feature.tenantOnly || workspace.isTenant),
        ))
          PremiumFeatureTile(feature: feature, workspace: workspace),
      ],
    ),
  );
}
