import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_feedback.dart';
import '../../data/models/premium_alert_body.dart';
import '../cubits/premium_alert_submit_cubit.dart';

class PremiumAlertComposer extends StatefulWidget {
  const PremiumAlertComposer({
    super.key,
    required this.filters,
    required this.name,
    required this.cadences,
    required this.cubit,
    required this.canChange,
    required this.onSaved,
  });
  final PropertySearchFilters filters;
  final String name;
  final List<String> cadences;
  final PremiumAlertSubmitCubit cubit;
  final bool canChange;
  final VoidCallback onSaved;
  @override
  State<PremiumAlertComposer> createState() => _PremiumAlertComposerState();
}

class _PremiumAlertComposerState extends State<PremiumAlertComposer> {
  final GlobalKey<FormState> _form = GlobalKey<FormState>();
  late final TextEditingController _name;
  final ValueNotifier<String?> _cadence = ValueNotifier(null);
  String? _requestKey;
  @override
  void initState() {
    super.initState();
    _name = TextEditingController(text: widget.name);
  }

  @override
  void dispose() {
    _name.dispose();
    _cadence.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Form(
    key: _form,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(widget.filters.combinedSearch),
        16.szH,
        TextFormField(
          controller: _name,
          enabled: widget.canChange,
          maxLength: 80,
          decoration: InputDecoration(labelText: LocaleKeys.paidAlertName),
          onChanged: (_) => _requestKey = null,
          validator: (text) =>
              text?.trim().isNotEmpty == true ? null : LocaleKeys.fillField,
        ),
        16.szH,
        ValueListenableBuilder<String?>(
          valueListenable: _cadence,
          builder: (context, cadence, _) {
            final available = widget.cadences
                .where((value) => const ['instant', 'daily'].contains(value))
                .toList();
            return DropdownButtonFormField<String>(
              isExpanded: true,
              initialValue: available.contains(cadence) ? cadence : null,
              decoration: InputDecoration(
                labelText: LocaleKeys.paidAlertCadence,
              ),
              items: [
                for (final value in available)
                  DropdownMenuItem(
                    value: value,
                    child: AppText(
                      value == 'instant'
                          ? LocaleKeys.paidAlertInstant
                          : LocaleKeys.paidAlertDaily,
                    ),
                  ),
              ],
              validator: (value) => value != null ? null : LocaleKeys.fillField,
              onChanged: !widget.canChange
                  ? null
                  : (value) {
                      _requestKey = null;
                      _cadence.value = value;
                    },
            );
          },
        ),
        16.szH,
        FilledButton(
          onPressed: !widget.canChange
              ? null
              : () async {
                  if (!_form.currentState!.validate() ||
                      _cadence.value == null) {
                    return;
                  }
                  _requestKey ??= const Uuid().v4();
                  final receipt = await widget.cubit.create(
                    PremiumAlertBody(
                      name: _name.text.trim(),
                      cadence: _cadence.value!,
                      filters: widget.filters,
                      requestKey: _requestKey!,
                    ),
                  );
                  if (receipt != null && mounted) {
                    PremiumFeedback.saved(receipt);
                    _requestKey = null;
                    widget.onSaved();
                  }
                },
          child: AppText(LocaleKeys.paidCreateAlert),
        ),
      ],
    ),
  );
}
