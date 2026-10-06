import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/finance/data/egyptian_pound.dart';
import '../../data/models/property_cost_breakdown.dart';

class PropertyCostCard extends StatelessWidget {
  const PropertyCostCard({
    super.key,
    required this.cost,
    required this.periodLabel,
  });
  final PropertyCostBreakdown cost;
  final String periodLabel;
  String _amount(double? value) => value == null
      ? LocaleKeys.freeAskOwner
      : '${EgyptianPound.formatAmount(value.toString())} ${LocaleKeys.egyptianPoundShort}';
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: context.appColor(AppColors.white, surface: true),
      border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
      borderRadius: BorderRadius.circular(16),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(LocaleKeys.freeKnownCosts, fontWeight: FontWeight.bold),
        const SizedBox(height: 12),
        _CostRow(
          label: '${LocaleKeys.freeRent} $periodLabel',
          value: _amount(cost.rent),
        ),
        _CostRow(label: LocaleKeys.freeDeposit, value: _amount(cost.deposit)),
        if (cost.knownSubtotal != null)
          _CostRow(
            label: LocaleKeys.freeKnownSubtotal,
            value: _amount(cost.knownSubtotal),
          ),
        const Divider(),
        AppText(
          LocaleKeys.freeCostsUnknown,
          color: context.appColor(AppColors.sokoonMuted),
          height: 1.5,
        ),
      ],
    ),
  );
}

class _CostRow extends StatelessWidget {
  const _CostRow({required this.label, required this.value});
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 6),
    child: Wrap(
      alignment: WrapAlignment.spaceBetween,
      spacing: 12,
      runSpacing: 4,
      children: [
        AppText(label),
        AppText(value, fontWeight: FontWeight.w600),
      ],
    ),
  );
}
