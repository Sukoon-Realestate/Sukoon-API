import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import '../../data/models/decision_notebook.dart';
import '../../data/models/property_cost_breakdown.dart';
import '../cubits/decision_tools_cubit.dart';
import '../screens/decision_tools_screen.dart';
import 'decision_editor.dart';
import 'property_cost_card.dart';
import 'availability_confirmation_label.dart';
import 'property_match_explanation.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

class PropertyDecisionTools extends StatefulWidget {
  const PropertyDecisionTools({
    super.key,
    required this.property,
    this.searchPreferences,
  });
  final PropertyDetailsModel property;
  final PropertySearchFilters? searchPreferences;
  @override
  State<PropertyDecisionTools> createState() => _PropertyDecisionToolsState();
}

class _PropertyDecisionToolsState extends State<PropertyDecisionTools> {
  late final DecisionToolsCubit _cubit;
  late final Future<void> _request;
  @override
  void initState() {
    super.initState();
    _cubit = DecisionToolsCubit(accountId: UserModel.currentUser?.id ?? '');
    _request = _cubit.load();
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      if (widget.searchPreferences != null)
        PropertyMatchExplanation(
          property: widget.property,
          preferences: widget.searchPreferences!,
        ),
      AvailabilityConfirmationLabel(
        confirmedAt: widget.property.availabilityConfirmedAt,
      ),
      const SizedBox(height: 12),
      PropertyCostCard(
        cost: PropertyCostBreakdown.fromProperty(widget.property),
        periodLabel: widget.property.pricePeriodLabel,
      ),
      const SizedBox(height: 12),
      FutureBuilder<void>(
        future: _request,
        builder: (context, snapshot) =>
            BlocBuilder<DecisionToolsCubit, DecisionNotebook>(
              bloc: _cubit,
              builder: (context, notebook) => Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  FilterChip(
                    label: AppText(LocaleKeys.freeCompare),
                    avatar: const Icon(Icons.compare_arrows, size: 18),
                    selected: notebook.comparisonIds.contains(
                      widget.property.id,
                    ),
                    onSelected:
                        snapshot.connectionState != ConnectionState.done ||
                            snapshot.hasError ||
                            widget.property.id.isEmpty
                        ? null
                        : (_) async {
                            try {
                              if (!await _cubit.toggleComparison(
                                notebook.decisionFor(
                                  widget.property.id,
                                  widget.property.title,
                                ),
                              )) {
                                Messages.showToast(
                                  msg: LocaleKeys.freeCompareLimit,
                                );
                              }
                            } catch (_) {
                              Messages.showToast(
                                msg: LocaleKeys.freeLocalSaveFailed,
                              );
                            }
                          },
                  ),
                  OutlinedButton.icon(
                    onPressed:
                        snapshot.connectionState != ConnectionState.done ||
                            snapshot.hasError ||
                            widget.property.id.isEmpty
                        ? null
                        : () => showModalBottomSheet<bool>(
                            context: context,
                            useSafeArea: true,
                            isScrollControlled: true,
                            showDragHandle: true,
                            builder: (_) => DecisionEditor(
                              cubit: _cubit,
                              decision: notebook.decisionFor(
                                widget.property.id,
                                widget.property.title,
                              ),
                            ),
                          ),
                    icon: const Icon(Icons.checklist, size: 18),
                    label: AppText(LocaleKeys.freePrivateNotes),
                  ),
                  TextButton(
                    onPressed: () async {
                      await Go.to(const DecisionToolsScreen());
                      if (mounted) await _cubit.load();
                    },
                    child: AppText(LocaleKeys.freeDecisionTools),
                  ),
                ],
              ),
            ),
      ),
    ],
  );
}
