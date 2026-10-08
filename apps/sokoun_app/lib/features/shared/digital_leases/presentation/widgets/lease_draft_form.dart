import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_selection_panel.dart';
import 'lease_rental_offer_selector.dart';
import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';
import '../../data/models/lease_tenant.dart';
import 'lease_tenant_selector.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:uuid/uuid.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_property_selector.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_confirm_sheet.dart';
import 'package:sokoun_app/shared_widgets/localized_digits_formatter.dart';
import '../../data/lease_rules.dart';
import '../../data/models/lease_draft_body.dart';
import '../../data/models/lease_template.dart';
import '../../data/models/digital_lease.dart';
import '../cubits/lease_draft_cubit.dart';

class LeaseDraftForm extends StatefulWidget {
  const LeaseDraftForm({
    super.key,
    required this.templates,
    required this.isFresh,
    this.property,
  });
  final List<LeaseTemplate> templates;
  final bool isFresh;
  final OwnerPropertyContent? property;
  @override
  State<LeaseDraftForm> createState() => _LeaseDraftFormState();
}

class _LeaseDraftFormState extends State<LeaseDraftForm> {
  final GlobalKey<FormState> _form = GlobalKey<FormState>();
  final TextEditingController _start = TextEditingController(),
      _end = TextEditingController(),
      _rent = TextEditingController();
  late final LeaseDraftCubit _cubit;
  final ValueNotifier<
    ({
      OwnerPropertyContent? property,
      LeaseTenant? tenant,
      RentalSelection? offer,
      String templateId,
      String? error,
    })
  >
  _selection = ValueNotifier((
    property: null,
    tenant: null,
    offer: null,
    templateId: '',
    error: null,
  ));
  String? _requestKey;
  final ValueNotifier<int> _offerRefresh = ValueNotifier(0);
  @override
  void initState() {
    super.initState();
    _cubit = LeaseDraftCubit();
    _selection.value = (
      property: widget.property,
      tenant: null,
      offer: null,
      templateId: '',
      error: null,
    );
  }

  @override
  void dispose() {
    _start.dispose();
    _end.dispose();
    _rent.dispose();
    _selection.dispose();
    _offerRefresh.dispose();
    _cubit.close();
    super.dispose();
  }

  void _changed() {
    _requestKey = null;
  }

  Future<void> _pickDate(TextEditingController controller) async {
    final date = await showDatePicker(
      context: context,
      initialDate: LeaseRules.date(controller.text) ?? DateTime.now(),
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );
    if (date != null && mounted) {
      controller.text = date.toIso8601String().substring(0, 10);
      _changed();
    }
  }

  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    padding: const EdgeInsets.all(20),
    child: BlocBuilder<LeaseDraftCubit, AsyncState<DigitalLease>>(
      bloc: _cubit,
      builder: (context, state) =>
          ValueListenableBuilder<
            ({
              OwnerPropertyContent? property,
              LeaseTenant? tenant,
              RentalSelection? offer,
              String templateId,
              String? error,
            })
          >(
            valueListenable: _selection,
            builder: (context, selection, _) {
              final template = widget.templates
                  .where((value) => value.id == selection.templateId)
                  .firstOrNull;
              final canChange = widget.isFresh && !state.isLoading;
              return Form(
                key: _form,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    AppText(LocaleKeys.paidLeasesExplanation),
                    16.szH,
                    PremiumPropertySelector(
                      property: selection.property,
                      enabled: canChange && widget.property == null,
                      onSelected: (property) {
                        _changed();
                        _selection.value = (
                          property: property,
                          tenant: null,
                          offer: null,
                          templateId: selection.templateId,
                          error: null,
                        );
                      },
                    ),
                    16.szH,
                    if (selection.property != null) ...[
                      ValueListenableBuilder<int>(
                        valueListenable: _offerRefresh,
                        builder: (context, refreshGeneration, _) =>
                            LeaseRentalOfferSelector(
                              key: ValueKey(selection.property!.id),
                              propertyId: selection.property!.id,
                              selection: selection.offer,
                              enabled: canChange,
                              refreshGeneration: refreshGeneration,
                              onSelected: (offer) {
                                _changed();
                                _selection.value = (
                                  property: selection.property,
                                  tenant: null,
                                  offer: offer,
                                  templateId: selection.templateId,
                                  error: null,
                                );
                              },
                            ),
                      ),
                      16.szH,
                    ],
                    LeaseTenantSelector(
                      propertyId: selection.property?.id ?? '',
                      offerId: selection.offer?.offerId ?? '',
                      tenant: selection.tenant,
                      enabled: canChange,
                      onSelected: (tenant) {
                        _changed();
                        _selection.value = (
                          property: selection.property,
                          tenant: tenant,
                          offer: selection.offer,
                          templateId: selection.templateId,
                          error: null,
                        );
                      },
                    ),
                    16.szH,
                    DropdownButtonFormField<String>(
                      initialValue: template?.id,
                      isExpanded: true,
                      itemHeight: null,
                      selectedItemBuilder: (_) => [
                        for (final item in widget.templates)
                          AppText(
                            '${item.title} ${item.version}',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                      ],
                      decoration: InputDecoration(
                        labelText: LocaleKeys.paidLeaseTemplate,
                      ),
                      items: [
                        for (final item in widget.templates)
                          DropdownMenuItem(
                            value: item.id,
                            child: AppText('${item.title} ${item.version}'),
                          ),
                      ],
                      onChanged: !canChange
                          ? null
                          : (id) {
                              _changed();
                              _selection.value = (
                                property: selection.property,
                                tenant: selection.tenant,
                                offer: selection.offer,
                                templateId: id ?? '',
                                error: null,
                              );
                            },
                    ),
                    16.szH,
                    if (template != null)
                      AppText(
                        LocaleKeys.featureLeaseTemplateDetails
                            .replaceAll('{version}', template.version)
                            .replaceAll('{language}', template.language)
                            .replaceAll(
                              '{jurisdiction}',
                              template.jurisdiction,
                            ),
                      ),
                    8.szH,
                    DefaultTextField(
                      controller: _start,
                      readOnly: true,
                      enabled: canChange,
                      decoration: InputDecoration(
                        labelText: LocaleKeys.paidLeaseStart,
                        suffixIcon: const Icon(Icons.calendar_today_outlined),
                      ),
                      onTap: () => _pickDate(_start),
                    ),
                    16.szH,
                    DefaultTextField(
                      controller: _end,
                      readOnly: true,
                      enabled: canChange,
                      decoration: InputDecoration(
                        labelText: LocaleKeys.paidLeaseEnd,
                        suffixIcon: const Icon(Icons.calendar_today_outlined),
                      ),
                      onTap: () => _pickDate(_end),
                    ),
                    16.szH,
                    DefaultTextField(
                      controller: _rent,
                      enabled: canChange,
                      inputType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      inputFormatters: [
                        const LocalizedDigitsFormatter(allowDecimal: true),
                      ],
                      decoration: InputDecoration(
                        labelText: LocaleKeys.paidMonthlyRent,
                      ),
                      onChanged: (_) => _changed(),
                    ),
                    16.szH,
                    if (state.isError && state.msg?.isNotEmpty == true)
                      AppText(
                        state.msg!,
                        color: Theme.of(context).colorScheme.error,
                      ),
                    if (selection.error != null)
                      AppText(
                        selection.error!,
                        color: Theme.of(context).colorScheme.error,
                      ),
                    FilledButton(
                      onPressed: !canChange
                          ? null
                          : () async {
                              if (!_form.currentState!.validate()) return;
                              _requestKey ??= const Uuid().v4();
                              final body = LeaseDraftBody(
                                hasRentalOffers:
                                    selection.property?.hasRentalOffers ==
                                        true ||
                                    selection.offer != null,
                                offerId: selection.offer?.offerId ?? '',
                                rentalSelection: selection.offer,
                                propertyId: selection.property?.id ?? '',
                                tenantId: selection.tenant?.id ?? '',
                                templateId: template?.id ?? '',
                                templateVersion: template?.version ?? '',
                                startDate: _start.text,
                                endDate: _end.text,
                                rent: LeaseRules.money(_rent.text),
                                requestKey: _requestKey!,
                              );
                              if (!LeaseRules.valid(body)) {
                                _selection.value = (
                                  property: selection.property,
                                  tenant: selection.tenant,
                                  offer: selection.offer,
                                  templateId: selection.templateId,
                                  error: LocaleKeys.paidLeaseInvalid,
                                );
                                return;
                              }
                              final confirmed = await PremiumConfirmSheet.show(
                                context,
                                title: LocaleKeys.paidCreateLease,
                                details: Column(
                                  crossAxisAlignment:
                                      CrossAxisAlignment.stretch,
                                  children: [
                                    AppText(selection.property!.title),
                                    if (selection.offer != null)
                                      RentalSelectionPanel(
                                        selection: selection.offer!,
                                      ),
                                    AppText(selection.tenant!.displayName),
                                    AppText(template!.title),
                                    AppText(
                                      '${body.startDate} – ${body.endDate}',
                                    ),
                                    AppText(body.rent.display),
                                    AppText(LocaleKeys.paidLeasesExplanation),
                                  ],
                                ),
                                actionLabel: LocaleKeys.paidCreateLease,
                              );
                              if (!confirmed || !mounted) return;
                              final lease = await _cubit.create(body);
                              if (!mounted) return;
                              if (lease != null) {
                                Go.back(lease);
                              } else {
                                _offerRefresh.value++;
                              }
                            },
                      child: state.isLoading
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : AppText(LocaleKeys.paidCreateLease),
                    ),
                  ],
                ),
              );
            },
          ),
    ),
  );
}
