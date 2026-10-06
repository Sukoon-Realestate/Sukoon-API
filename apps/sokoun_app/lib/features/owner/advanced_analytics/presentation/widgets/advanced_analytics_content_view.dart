import 'package:melos_core/config/language/languages.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_property_selector.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_remote_view.dart';
import '../../data/models/advanced_analytics_content.dart';
import '../cubits/advanced_analytics_cubit.dart';
import 'advanced_analytics_summary.dart';

class AdvancedAnalyticsContentView extends StatefulWidget {
  const AdvancedAnalyticsContentView({super.key, this.initialProperty});
  final OwnerPropertyContent? initialProperty;
  @override
  State<AdvancedAnalyticsContentView> createState() =>
      _AdvancedAnalyticsContentViewState();
}

class _AdvancedAnalyticsContentViewState
    extends State<AdvancedAnalyticsContentView> {
  late final AdvancedAnalyticsCubit _cubit;
  late final ValueNotifier<({OwnerPropertyContent? property, int days})>
  _selection;
  late final ValueNotifier<Future<void>> _request;
  @override
  void initState() {
    super.initState();
    _cubit = AdvancedAnalyticsCubit();
    _selection = ValueNotifier((property: widget.initialProperty, days: 30));
    _request = ValueNotifier(_load());
  }

  Future<void> _load() => _cubit.load(
    propertyId: _selection.value.property?.id ?? '',
    periodDays: _selection.value.days,
    language: Languages.currentLanguage.languageCode,
  );
  void _choose(({OwnerPropertyContent? property, int days}) selection) {
    _selection.value = selection;
    _request.value = _load();
  }

  @override
  void dispose() {
    _selection.dispose();
    _request.dispose();
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    padding: const EdgeInsets.all(20),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(LocaleKeys.paidAnalyticsExplanation),
        16.szH,
        ValueListenableBuilder<({OwnerPropertyContent? property, int days})>(
          valueListenable: _selection,
          builder: (context, selection, _) => Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              PremiumPropertySelector(
                property: selection.property,
                onSelected: (property) =>
                    _choose((property: property, days: selection.days)),
              ),
              16.szH,
              DropdownButtonFormField<int>(
                initialValue: selection.days,
                isExpanded: true,
                decoration: InputDecoration(
                  labelText: LocaleKeys.ownerAnalyticsPeriod,
                ),
                items: [
                  DropdownMenuItem(
                    value: 7,
                    child: AppText(LocaleKeys.ownerAnalyticsSevenDays),
                  ),
                  DropdownMenuItem(
                    value: 30,
                    child: AppText(LocaleKeys.ownerAnalyticsThirtyDays),
                  ),
                  DropdownMenuItem(
                    value: 90,
                    child: AppText(LocaleKeys.ownerAnalyticsNinetyDays),
                  ),
                ],
                onChanged: (days) {
                  if (days != null) {
                    _choose((property: selection.property, days: days));
                  }
                },
              ),
              16.szH,
              if (selection.property != null)
                ValueListenableBuilder<Future<void>>(
                  valueListenable: _request,
                  builder: (_, request, __) =>
                      PremiumRemoteView<
                        AdvancedAnalyticsCubit,
                        AdvancedAnalyticsContent
                      >(
                        cubit: _cubit,
                        request: request,
                        initialData: const AdvancedAnalyticsContent.initial(),
                        onRetry: _load,
                        builder: (content) =>
                            AdvancedAnalyticsSummary(content: content),
                      ),
                ),
            ],
          ),
        ),
      ],
    ),
  );
}
