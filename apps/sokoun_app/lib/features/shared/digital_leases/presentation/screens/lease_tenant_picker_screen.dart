import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import '../widgets/lease_tenant_picker_list.dart';

class LeaseTenantPickerScreen extends StatelessWidget {
  const LeaseTenantPickerScreen({
    super.key,
    required this.propertyId,
    this.offerId = '',
  });
  final String propertyId;
  final String offerId;
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.paidLeaseTenant,
    showBackButton: true,
    body: LeaseTenantPickerList(propertyId: propertyId, offerId: offerId),
  );
}
