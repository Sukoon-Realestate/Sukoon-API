import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/generated/assets.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'rent_management_entry.dart';

class RentOverviewEmptyState extends StatelessWidget {
  const RentOverviewEmptyState({super.key});
  @override
  Widget build(BuildContext context) => Card(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              ExcludeSemantics(
                child: Assets.lottie.emptyBox.lottie(
                  package: 'melos_core',
                  width: 56,
                  height: 56,
                  animate: !MediaQuery.of(context).disableAnimations,
                  repeat: false,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(child: AppText(LocaleKeys.journeyNoRentDue)),
            ],
          ),
        ),
        const RentManagementEntry(workspace: AppWorkspace.tenant),
      ],
    ),
  );
}
