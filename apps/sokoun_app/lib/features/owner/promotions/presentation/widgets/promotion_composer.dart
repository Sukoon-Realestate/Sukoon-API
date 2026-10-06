import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:uuid/uuid.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'package:sokoun_app/features/shared/premium/data/models/feature_configuration.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_action_receipt.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_property_selector.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_confirm_sheet.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_feedback.dart';
import '../../data/models/promotion_body.dart';
import '../cubits/promotion_submit_cubit.dart';

class PromotionComposer extends StatefulWidget {
  const PromotionComposer({
    super.key,
    required this.configuration,
    required this.isFresh,
    required this.onSaved,
    this.initialProperty,
  });
  final FeatureConfiguration configuration;
  final bool isFresh;
  final OwnerPropertyContent? initialProperty;
  final Future<void> Function() onSaved;
  @override
  State<PromotionComposer> createState() => _PromotionComposerState();
}

class _PromotionComposerState extends State<PromotionComposer> {
  late final PromotionSubmitCubit _submit;
  late final ValueNotifier<({OwnerPropertyContent? property, String optionId})>
  _selection;
  String? _requestKey;
  @override
  void initState() {
    super.initState();
    _submit = PromotionSubmitCubit();
    _selection = ValueNotifier((
      property: widget.initialProperty,
      optionId: '',
    ));
  }

  @override
  void dispose() {
    _selection.dispose();
    _submit.close();
    super.dispose();
  }

  @override
  Widget build(
    BuildContext context,
  ) => BlocBuilder<PromotionSubmitCubit, AsyncState<PremiumActionReceipt>>(
    bloc: _submit,
    builder: (context, state) =>
        ValueListenableBuilder<
          ({OwnerPropertyContent? property, String optionId})
        >(
          valueListenable: _selection,
          builder: (context, selection, _) {
            final options = widget.configuration.boostOptions
                .where((option) => option.isValid)
                .toList();
            final option = options
                .where((value) => value.id == selection.optionId)
                .firstOrNull;
            final canChange = widget.isFresh && !state.isLoading;
            return Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  AppText(LocaleKeys.paidBoostExplanation),
                  if (!widget.isFresh) AppText(LocaleKeys.paidCachedNotice),
                  16.szH,
                  PremiumPropertySelector(
                    property: selection.property,
                    enabled: canChange,
                    onSelected: (property) {
                      _requestKey = null;
                      _selection.value = (
                        property: property,
                        optionId: selection.optionId,
                      );
                    },
                  ),
                  16.szH,
                  DropdownButtonFormField<String>(
                    isExpanded: true,
                    itemHeight: null,
                    selectedItemBuilder: (_) => [
                      for (final item in options)
                        AppText(
                          item.title,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                    ],
                    initialValue: option?.id,
                    decoration: InputDecoration(
                      labelText: LocaleKeys.paidBoostDuration,
                    ),
                    items: [
                      for (final item in options)
                        DropdownMenuItem(
                          value: item.id,
                          child: AppText(item.title),
                        ),
                    ],
                    onChanged: !canChange
                        ? null
                        : (id) {
                            _requestKey = null;
                            _selection.value = (
                              property: selection.property,
                              optionId: id ?? '',
                            );
                          },
                  ),
                  if (option != null) AppText(option.title),
                  if (option != null)
                    AppText(
                      LocaleKeys.toolsBoostDuration.replaceAll(
                        '{days}',
                        '${option.durationDays}',
                      ),
                    ),
                  16.szH,
                  FilledButton(
                    onPressed:
                        !canChange ||
                            option == null ||
                            selection.property == null
                        ? null
                        : () async {
                            final confirmed = await PremiumConfirmSheet.show(
                              context,
                              title: LocaleKeys.paidConfirmBoost,
                              details: Column(
                                children: [
                                  AppText(selection.property!.title),
                                  AppText(option.title),
                                  AppText(
                                    LocaleKeys.toolsBoostDuration.replaceAll(
                                      '{days}',
                                      '${option.durationDays}',
                                    ),
                                  ),
                                ],
                              ),
                              actionLabel: LocaleKeys.paidStartBoost,
                            );
                            if (!confirmed || !mounted) return;
                            _requestKey ??= const Uuid().v4();
                            final receipt = await _submit.submit(
                              PromotionBody(
                                propertyId: selection.property!.id,
                                optionId: option.id,
                                requestKey: _requestKey!,
                              ),
                            );
                            if (receipt != null && mounted) {
                              PremiumFeedback.saved(receipt);
                              _requestKey = null;
                              await widget.onSaved();
                            }
                          },
                    child: state.isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : AppText(LocaleKeys.paidStartBoost),
                  ),
                  24.szH,
                  AppText(
                    LocaleKeys.paidCampaignsTitle,
                    fontWeight: FontWeight.bold,
                  ),
                ],
              ),
            );
          },
        ),
  );
}
