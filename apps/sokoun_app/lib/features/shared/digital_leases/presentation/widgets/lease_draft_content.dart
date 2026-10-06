import 'package:melos_core/config/language/languages.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_remote_view.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_empty_state.dart';
import '../../data/models/lease_configuration.dart';
import '../cubits/lease_configuration_cubit.dart';
import 'lease_draft_form.dart';

class LeaseDraftContent extends StatefulWidget {
  const LeaseDraftContent({super.key});
  @override
  State<LeaseDraftContent> createState() => _LeaseDraftContentState();
}

class _LeaseDraftContentState extends State<LeaseDraftContent> {
  late final LeaseConfigurationCubit _cubit;
  late final Future<void> _request;
  @override
  void initState() {
    super.initState();
    _cubit = LeaseConfigurationCubit();
    _request = _load();
  }

  Future<void> _load() =>
      _cubit.load(language: Languages.currentLanguage.languageCode);

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) =>
      PremiumRemoteView<LeaseConfigurationCubit, LeaseConfiguration>(
        cubit: _cubit,
        request: _request,
        initialData: const LeaseConfiguration.initial(),
        onRetry: _load,
        builder: (configuration) =>
            !configuration.canCreate || configuration.templates.isEmpty
            ? SingleChildScrollView(
                child: PremiumEmptyState(
                  title: LocaleKeys.paidUnavailable,
                  description: LocaleKeys.paidUnavailableBody,
                ),
              )
            : LeaseDraftForm(
                templates: configuration.templates,
                isFresh: !_cubit.isCached,
              ),
      );
}
