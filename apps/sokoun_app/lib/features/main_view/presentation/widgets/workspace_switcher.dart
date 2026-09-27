import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../../data/enums/app_workspace.dart';
import '../workspace_navigation.dart';

class WorkspaceSwitcher extends StatelessWidget {
  const WorkspaceSwitcher({
    super.key,
    required this.workspace,
    this.asAction = false,
  });

  final AppWorkspace workspace;
  final bool asAction;

  void _switch(AppWorkspace target) =>
      WorkspaceNavigation.open(workspace: target, showLoginSheet: true);

  @override
  Widget build(BuildContext context) {
    if (asAction) {
      return TextButton.icon(
        onPressed: () => _switch(
          workspace.isOwner ? AppWorkspace.tenant : AppWorkspace.owner,
        ),
        icon: const Icon(Icons.swap_horiz_rounded),
        label: AppText(
          workspace.isOwner
              ? LocaleKeys.workspaceSwitchToTenant
              : LocaleKeys.workspaceSwitchToOwner,
        ),
      );
    }
    return Semantics(
      label: LocaleKeys.workspaceSwitch,
      child: Wrap(
        spacing: 8.w,
        children: AppWorkspace.values
            .map(
              (item) => ChoiceChip(
                selected: workspace == item,
                onSelected: workspace == item ? null : (_) => _switch(item),
                selectedColor: item.isOwner
                    ? AppColors.goldPale
                    : AppColors.mintLight,
                label: AppText(
                  item.isOwner
                      ? LocaleKeys.workspaceOwner
                      : LocaleKeys.workspaceTenant,
                  fontSize: 12.sp,
                  color: AppColors.sokoonNavy,
                ),
              ),
            )
            .toList(growable: false),
      ),
    );
  }
}
