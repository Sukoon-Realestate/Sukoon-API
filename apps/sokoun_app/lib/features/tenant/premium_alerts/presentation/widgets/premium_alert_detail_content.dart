import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_filter_options_cubit.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'premium_alert_details_view.dart';
import 'package:flutter/material.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_remote_view.dart';
import '../../data/models/premium_search_alert.dart';
import '../cubits/premium_alert_details_cubit.dart';
import 'premium_alerts_empty_state.dart';

class PremiumAlertDetailContent extends StatefulWidget {
  const PremiumAlertDetailContent({super.key, required this.alertId});
  final String alertId;
  @override
  State<PremiumAlertDetailContent> createState() =>
      _PremiumAlertDetailContentState();
}

class _PremiumAlertDetailContentState extends State<PremiumAlertDetailContent> {
  late final PremiumAlertDetailsCubit _cubit;
  late final Future<void> _request;
  late final PropertyFilterOptionsCubit _filterOptions;
  late final Future<void> _optionsRequest;
  @override
  void initState() {
    super.initState();
    _cubit = PremiumAlertDetailsCubit();
    _filterOptions = PropertyFilterOptionsCubit();
    _optionsRequest = _filterOptions.getFilterOptions();
    _request = _cubit.load(widget.alertId);
  }

  @override
  void dispose() {
    _cubit.close();
    _filterOptions.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) =>
      PremiumRemoteView<PremiumAlertDetailsCubit, PremiumSearchAlert>(
        cubit: _cubit,
        request: _request,
        initialData: const PremiumSearchAlert.initial(),
        onRetry: () => _cubit.load(widget.alertId),
        builder: (alert) => alert.id.isEmpty
            ? const PremiumAlertsEmptyState()
            : BlocProvider<PropertyFilterOptionsCubit>.value(
                value: _filterOptions,
                child: FutureBuilder<void>(
                  future: _optionsRequest,
                  builder: (context, snapshot) =>
                      StatusBuilder<
                        PropertyFilterOptionsCubit,
                        PropertyFilterOptionsModel
                      >.withShimmer(
                        initialDataForShimmer:
                            const PropertyFilterOptionsModel.initial(),
                        errorType: ErrorType.withData,
                        onRetry: () => _filterOptions.getFilterOptions(),
                        builder: (options) => PremiumAlertDetailsView(
                          alert: alert,
                          options: options,
                        ),
                      ),
                ),
              ),
      );
}
