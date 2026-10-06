import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import '../../data/models/comparison_property.dart';
import '../cubits/decision_tools_cubit.dart';
import '../cubits/property_comparison_cubit.dart';
import '../widgets/comparison_table.dart';
import '../widgets/decision_tools_empty.dart';

class PropertyComparisonScreen extends StatefulWidget {
  const PropertyComparisonScreen({super.key, required this.propertyIds});
  final List<String> propertyIds;
  @override
  State<PropertyComparisonScreen> createState() =>
      _PropertyComparisonScreenState();
}

class _PropertyComparisonScreenState extends State<PropertyComparisonScreen> {
  late final PropertyComparisonCubit _cubit;
  late final DecisionToolsCubit _decisions;
  late final ValueNotifier<Future<void>> _request;
  @override
  void initState() {
    super.initState();
    _cubit = PropertyComparisonCubit();
    _decisions = DecisionToolsCubit(accountId: UserModel.currentUser?.id ?? '');
    _request = ValueNotifier(_load());
  }

  Future<void> _load() async {
    await _decisions.load();
    await _cubit.load(
      widget.propertyIds
          .where(_decisions.state.comparisonIds.contains)
          .toList(),
    );
  }

  Future<void> _remove(String propertyId) async {
    try {
      await _decisions.toggleComparison(
        _decisions.state.decisionFor(propertyId, ''),
      );
      if (mounted) _request.value = _cubit.load(_decisions.state.comparisonIds);
    } catch (_) {
      Messages.showToast(msg: LocaleKeys.freeLocalSaveFailed);
    }
  }

  @override
  void dispose() {
    _request.dispose();
    _cubit.close();
    _decisions.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.freeCompare,
    contentWidth: SokounContentWidth.wide,
    showBackButton: true,
    body: BlocProvider.value(
      value: _cubit,
      child: ValueListenableBuilder<Future<void>>(
        valueListenable: _request,
        builder: (context, request, _) => FutureBuilder<void>(
          future: request,
          builder: (context, snapshot) {
            if (snapshot.hasError) {
              return ExceptionView(
                msg: LocaleKeys.freeLocalSaveFailed,
                onRetry: () async {
                  _request.value = _load();
                  await _request.value;
                },
              );
            }
            return StatusBuilder<
              PropertyComparisonCubit,
              List<ComparisonProperty>
            >.withShimmer(
              initialDataForShimmer: const [
                ComparisonProperty.initial(),
                ComparisonProperty.initial(),
              ],
              shimmerBuilder: (_) => const SizedBox(height: 260),
              onRetry: _load,
              emptyView: DecisionToolsEmpty(
                title: LocaleKeys.freeCompare,
                description: LocaleKeys.freeComparisonExplanation,
              ),
              builder: (properties) => SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: ComparisonTable(
                  properties: properties,
                  onRemove: _remove,
                  savedTitles: {
                    for (final decision in _decisions.state.properties)
                      decision.propertyId: decision.title,
                  },
                ),
              ),
            );
          },
        ),
      ),
    ),
  );
}
