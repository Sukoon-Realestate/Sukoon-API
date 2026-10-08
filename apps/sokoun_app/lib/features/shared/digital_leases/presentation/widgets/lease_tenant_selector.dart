import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import '../../data/models/lease_tenant.dart';
import '../screens/lease_tenant_picker_screen.dart';

class LeaseTenantSelector extends StatelessWidget {
  const LeaseTenantSelector({
    super.key,
    required this.propertyId,
    required this.tenant,
    required this.enabled,
    required this.onSelected,
    this.offerId = '',
  });
  final String propertyId;
  final String offerId;
  final LeaseTenant? tenant;
  final bool enabled;
  final ValueChanged<LeaseTenant> onSelected;
  @override
  Widget build(BuildContext context) => OutlinedButton.icon(
    onPressed: !enabled || propertyId.isEmpty
        ? null
        : () async {
            final selected = await Go.to<LeaseTenant>(
              LeaseTenantPickerScreen(propertyId: propertyId, offerId: offerId),
            );
            if (selected != null && context.mounted) onSelected(selected);
          },
    icon: const Icon(Icons.person_outline),
    label: AppText(tenant?.displayName ?? LocaleKeys.paidLeaseTenant),
  );
}
