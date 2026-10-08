import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_empty_state.dart';

class TenancyInvitationsEmptyState extends StatelessWidget {
  const TenancyInvitationsEmptyState({super.key});
  @override
  Widget build(BuildContext context) => PremiumEmptyState(
    title: LocaleKeys.tenancyInvitationsEmpty,
    description: LocaleKeys.tenancyInvitationsEmptyBody,
  );
}
