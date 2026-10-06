import 'package:melos_core/config/language/languages.dart';
import 'package:sokoun_app/features/shared/premium/presentation/cubits/feature_configuration_cubit.dart';
import 'package:flutter/material.dart';
import 'package:pagify/pagify.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/feature_configuration_view.dart';
import '../../data/promotions_data.dart';
import '../../data/models/promotion_campaign.dart';
import 'promotions_empty_state.dart';
import 'promotion_campaign_card.dart';
import 'promotion_composer.dart';

class PromotionsContent extends StatefulWidget {
  const PromotionsContent({super.key, this.initialProperty});
  final OwnerPropertyContent? initialProperty;
  @override
  State<PromotionsContent> createState() => _PromotionsContentState();
}

class _PromotionsContentState extends State<PromotionsContent> {
  late final FeatureConfigurationCubit _configuration;
  late final Future<void> _configurationRequest;
  Future<void> _loadConfiguration() => _configuration.load(
    AppWorkspace.owner,
    language: Languages.currentLanguage.languageCode,
  );
  final PagifyController<PromotionCampaign> _controller = PagifyController();

  @override
  void initState() {
    super.initState();
    _configuration = FeatureConfigurationCubit();
    _configurationRequest = _loadConfiguration();
  }

  @override
  void dispose() {
    _configuration.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AppPagify<PromotionCampaign>(
    pagifyController: _controller,
    header: FeatureConfigurationView(
      cubit: _configuration,
      request: _configurationRequest,
      onRetry: _loadConfiguration,
      builder: (configuration, isFresh) => PromotionComposer(
        configuration: configuration,
        isFresh: isFresh,
        initialProperty: widget.initialProperty,
        onSaved: () async {
          await _controller.refresh();
        },
      ),
    ),
    enablePullRefresh: true,
    cacheKey: PromotionsData.cacheKey,
    cacheToJson: (item) => item.toJson(),
    cacheFromJson: PromotionCampaign.fromJson,
    asyncCall: (_, page) => PromotionsData.getPage(page: page),
    emptyListView: const PromotionsEmptyState(),
    itemBuilder: (_, __, ___, campaign) =>
        PromotionCampaignCard(key: ValueKey(campaign.id), campaign: campaign),
  );
}
