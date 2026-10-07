import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/owner/advanced_analytics/presentation/widgets/owner_analytics_entry.dart';
import 'package:sokoun_app/features/shared/profile/presentation/widgets/contracts/contracts_entry.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/widgets/rent_management_entry.dart';

class OwnerOperationsSection extends StatelessWidget {
  const OwnerOperationsSection({super.key});
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      AppText(LocaleKeys.journeyOwnerOperations, fontWeight: FontWeight.bold),
      8.szH,
      const Card(
        child: Column(
          children: [
            OwnerAnalyticsEntry(),
            Divider(height: 1),
            ContractsEntry(workspace: AppWorkspace.owner),
            Divider(height: 1),
            RentManagementEntry(workspace: AppWorkspace.owner),
          ],
        ),
      ),
    ],
  );
}
