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
  });
  final List<LeaseTemplate> templates;
  final bool isFresh;
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
      String templateId,
      String? error,
    })
  >
  _selection = ValueNotifier((
    property: null,
    tenant: null,
    templateId: '',
    error: null,
  ));
  String? _requestKey;
  @override
  void initState() {
    super.initState();
    _cubit = LeaseDraftCubit();
  }

  @override
  void dispose() {
    _start.dispose();
    _end.dispose();
    _rent.dispose();
    _selection.dispose();
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
                      enabled: canChange,
                      onSelected: (property) {
                        _changed();
                        _selection.value = (
                          property: property,
                          tenant: null,
                          templateId: selection.templateId,
                          error: null,
                        );
                      },
                    ),
                    16.szH,
                    LeaseTenantSelector(
                      propertyId: selection.property?.id ?? '',
                      tenant: selection.tenant,
                      enabled: canChange,
                      onSelected: (tenant) {
                        _changed();
                        _selection.value = (
                          property: selection.property,
                          tenant: tenant,
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
                                templateId: id ?? '',
                                error: null,
                              );
                            },
                    ),
                    16.szH,
                    if (template != null)
                      AppText('${template.title} ${template.version}'),
                    8.szH,
                    TextFormField(
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
                    TextFormField(
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
                    TextFormField(
                      controller: _rent,
                      enabled: canChange,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      inputFormatters: [LocalizedDigitsFormatter()],
                      decoration: InputDecoration(
                        labelText: LocaleKeys.paidMonthlyRent,
                      ),
                      onChanged: (_) => _changed(),
                    ),
                    16.szH,
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
                              if (lease != null && mounted) Go.back(lease);
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
