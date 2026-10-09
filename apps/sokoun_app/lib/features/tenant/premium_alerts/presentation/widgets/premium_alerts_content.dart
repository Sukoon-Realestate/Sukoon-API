import 'package:melos_core/core/local_db/read_cache_policy.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:sokoun_app/features/shared/premium/presentation/cubits/feature_configuration_cubit.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/feature_configuration_view.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_confirm_sheet.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_revision_body.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_request_keys.dart';
import 'package:sokoun_app/features/shared/premium/data/feature_service_capabilities.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_action_receipt.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_feedback.dart';
import '../../data/premium_alerts_data.dart';
import '../../data/models/premium_search_alert.dart';
import '../../data/models/premium_alert_toggle_body.dart';
import '../cubits/premium_alert_submit_cubit.dart';
import 'premium_alerts_empty_state.dart';
import 'premium_alert_composer.dart';
import 'premium_alert_card.dart';

class PremiumAlertsContent extends StatefulWidget {
  const PremiumAlertsContent({super.key, this.filters, this.name = ''});
  final PropertySearchFilters? filters;
  final String name;
  @override
  State<PremiumAlertsContent> createState() => _PremiumAlertsContentState();
}

class _PremiumAlertsContentState extends State<PremiumAlertsContent> {
  late final FeatureConfigurationCubit _configuration;
  late final Future<void> _configurationRequest;
  Future<void> _loadConfiguration() => _configuration.load(
    AppWorkspace.tenant,
    language: Languages.currentLanguage.languageCode,
  );
  final PagifyController<PremiumSearchAlert> _controller = PagifyController();
  late final PremiumAlertSubmitCubit _submit;
  final PremiumRequestKeys _requestKeys = PremiumRequestKeys();
  @override
  void initState() {
    super.initState();
    _submit = PremiumAlertSubmitCubit();
    _configuration = FeatureConfigurationCubit();
    _configurationRequest = widget.filters == null
        ? Future.value()
        : _loadConfiguration();
  }

  @override
  void dispose() {
    _submit.close();
    _configuration.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) =>
      BlocBuilder<PremiumAlertSubmitCubit, AsyncState<PremiumActionReceipt>>(
        bloc: _submit,
        builder: (context, state) => AppPagify<PremiumSearchAlert>(
          pagifyController: _controller,
          enablePullRefresh: true,
          header: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                AppText(LocaleKeys.paidAlertsExplanation),
                if (!FeatureServiceCapabilities.configured.alertDelivery)
                  AppText(LocaleKeys.featureAlertDeliveryUnavailable),
                if (state.isError && state.msg?.isNotEmpty == true)
                  AppText(
                    state.msg!,
                    color: Theme.of(context).colorScheme.error,
                  ),
                if (widget.filters != null) ...[
                  16.szH,
                  FeatureConfigurationView(
                    cubit: _configuration,
                    request: _configurationRequest,
                    onRetry: _loadConfiguration,
                    builder: (configuration, isFresh) => Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        if (!isFresh) AppText(LocaleKeys.paidCachedNotice),
                        PremiumAlertComposer(
                          filters: widget.filters!,
                          name: widget.name,
                          cadences: configuration.alertCadences,
                          cubit: _submit,
                          canChange: isFresh && !state.isLoading,
                          onSaved: _controller.refresh,
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
          cacheKey: PremiumAlertsData.cacheKey,
          cachePolicy: ReadCachePolicy.privateMemory,
          cacheToJson: (item) => item.toJson(),
          cacheFromJson: PremiumSearchAlert.fromJson,
          asyncCall: (_, page) => PremiumAlertsData.getPage(page: page),
          emptyListView: const PremiumAlertsEmptyState(),
          itemBuilder: (_, __, ___, alert) => PremiumAlertCard(
            key: ValueKey(alert.id),
            alert: alert,
            canChange: !state.isLoading,
            onRemove: () async {
              final confirmed = await PremiumConfirmSheet.show(
                context,
                title: LocaleKeys.paidRemoveAlert,
                details: AppText(alert.name),
                actionLabel: LocaleKeys.freeRemove,
              );
              if (!confirmed || !mounted) return;
              final receipt = await _submit.remove(
                alert.id,
                PremiumRevisionBody(
                  revision: alert.revision,
                  requestKey: _requestKeys.forAction('remove_alert', [
                    alert.id,
                    alert.revision,
                  ]),
                ),
              );
              if (!mounted) return;
              if (receipt != null) PremiumFeedback.saved(receipt);
              _controller.refresh();
            },
            onToggle: () async {
              final receipt = await _submit.toggle(
                alert.id,
                PremiumAlertToggleBody(
                  enabled: !alert.enabled,
                  revision: alert.revision,
                  requestKey: _requestKeys.forAction('toggle_alert', [
                    alert.id,
                    alert.revision,
                    !alert.enabled,
                  ]),
                ),
              );
              if (!mounted) return;
              if (receipt != null) PremiumFeedback.saved(receipt);
              _controller.refresh();
            },
          ),
        ),
      );
}
