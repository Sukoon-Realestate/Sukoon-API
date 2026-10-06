import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../../../data/models/feature_configuration.dart';
import '../../cubits/feature_configuration_cubit.dart';
import 'premium_remote_view.dart';

/// Configuration stays owned by the content widget when pagination replaces its header.
class FeatureConfigurationView extends StatelessWidget {
  const FeatureConfigurationView({
    super.key,
    required this.cubit,
    required this.request,
    required this.onRetry,
    required this.builder,
  });
  final FeatureConfigurationCubit cubit;
  final Future<void> request;
  final Future<void> Function() onRetry;
  final Widget Function(FeatureConfiguration configuration, bool isFresh)
  builder;
  @override
  Widget build(BuildContext context) =>
      PremiumRemoteView<FeatureConfigurationCubit, FeatureConfiguration>(
        cubit: cubit,
        request: request,
        initialData: const FeatureConfiguration.initial(),
        onRetry: onRetry,
        builder: (configuration) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            builder(configuration, !cubit.isCached),
            if (cubit.isCached)
              TextButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: AppText(LocaleKeys.paidRefresh),
              ),
          ],
        ),
      );
}
