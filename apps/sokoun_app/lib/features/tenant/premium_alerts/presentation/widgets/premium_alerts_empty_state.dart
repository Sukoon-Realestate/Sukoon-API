import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_empty_state.dart';

class PremiumAlertsEmptyState extends StatelessWidget {
  const PremiumAlertsEmptyState({super.key});
  @override
  Widget build(BuildContext context) => PremiumEmptyState(
    title: LocaleKeys.paidAlertsEmpty,
    description: LocaleKeys.paidAlertsEmptyBody,
  );
}
