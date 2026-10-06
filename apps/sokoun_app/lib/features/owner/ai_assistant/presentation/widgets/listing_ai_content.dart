import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:uuid/uuid.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_property_selector.dart';
import '../../data/models/listing_ai_facts.dart';
import '../../data/models/listing_ai_body.dart';
import '../../data/models/listing_suggestion.dart';
import '../cubits/listing_ai_cubit.dart';
import 'listing_ai_facts_view.dart';
import 'listing_ai_review.dart';

class ListingAiContent extends StatefulWidget {
  const ListingAiContent({
    super.key,
    this.facts,
    required this.propertyId,
    required this.canApply,
  });
  final ListingAiFacts? facts;
  final String propertyId;
  final bool canApply;
  @override
  State<ListingAiContent> createState() => _ListingAiContentState();
}

class _ListingAiContentState extends State<ListingAiContent> {
  late final ListingAiCubit _cubit;
  late final ValueNotifier<
    ({
      ListingAiFacts? facts,
      OwnerPropertyContent? property,
      String propertyId,
      bool consent,
    })
  >
  _input;
  String? _requestKey;
  @override
  void initState() {
    super.initState();
    _cubit = ListingAiCubit();
    _input = ValueNotifier((
      facts: widget.facts,
      property: null,
      propertyId: widget.propertyId,
      consent: false,
    ));
  }

  @override
  void dispose() {
    _input.dispose();
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    padding: const EdgeInsets.all(20),
    child: BlocBuilder<ListingAiCubit, AsyncState<ListingSuggestion>>(
      bloc: _cubit,
      builder: (context, state) =>
          ValueListenableBuilder<
            ({
              ListingAiFacts? facts,
              OwnerPropertyContent? property,
              String propertyId,
              bool consent,
            })
          >(
            valueListenable: _input,
            builder: (context, input, _) => Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                AppText(LocaleKeys.paidAiExplanation),
                16.szH,
                if (widget.facts == null)
                  PremiumPropertySelector(
                    property: input.property,
                    enabled: !state.isLoading,
                    onSelected: (property) {
                      _requestKey = null;
                      _cubit.reset();
                      _input.value = (
                        facts: ListingAiFacts.fromProperty(property),
                        property: property,
                        propertyId: property.id,
                        consent: false,
                      );
                    },
                  ),
                if (input.facts != null) ...[
                  ListingAiFactsView(facts: input.facts!),
                  CheckboxListTile(
                    contentPadding: EdgeInsets.zero,
                    title: AppText(LocaleKeys.paidAiConsent),
                    value: input.consent,
                    onChanged: state.isLoading
                        ? null
                        : (value) => _input.value = (
                            facts: input.facts,
                            property: input.property,
                            propertyId: input.propertyId,
                            consent: value ?? false,
                          ),
                  ),
                  FilledButton(
                    onPressed: !input.consent || state.isLoading
                        ? null
                        : () async {
                            _requestKey ??= const Uuid().v4();
                            final result = await _cubit.generate(
                              ListingAiBody(
                                propertyId: input.propertyId,
                                facts: input.facts!,
                                language: context.locale.languageCode,
                                requestKey: _requestKey!,
                              ),
                            );
                            if (result != null) _requestKey = null;
                          },
                    child: state.isLoading
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : AppText(LocaleKeys.paidAiGenerate),
                  ),
                ],
                if (state.isError && state.msg?.isNotEmpty == true)
                  AppText(state.msg!),
                if (state.isSuccess && state.data.id.isNotEmpty) ...[
                  24.szH,
                  ListingAiReview(
                    suggestion: state.data,
                    canApply: widget.canApply,
                  ),
                ],
              ],
            ),
          ),
    ),
  );
}
