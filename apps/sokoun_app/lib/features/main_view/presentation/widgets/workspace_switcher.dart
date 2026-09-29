import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
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
          style: AppTextStyles.regular,
        ),
      );
    }
    return Semantics(
      label: LocaleKeys.workspaceSwitch,
      child: Container(
        padding: EdgeInsets.symmetric(horizontal: 4.w),
        decoration: const ShapeDecoration(
          color: AppColors.grayBackground,
          shape: StadiumBorder(side: BorderSide(color: AppColors.sokoonBorder)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          spacing: 4.w,
          children: AppWorkspace.values
              .map((item) {
                final bool isSelected = workspace == item;
                final Color foregroundColor = isSelected
                    ? AppColors.white
                    : AppColors.sokoonGray;

                return Flexible(
                  child: ChoiceChip(
                    selected: isSelected,
                    onSelected: (_) {
                      if (!isSelected) _switch(item);
                    },
                    showCheckmark: false,
                    shape: const StadiumBorder(),
                    side: BorderSide.none,
                    backgroundColor: AppColors.transparent,
                    selectedColor: item.isOwner
                        ? AppColors.sokoonNavy
                        : AppColors.sokoonTeal,
                    padding: EdgeInsets.symmetric(
                      horizontal: 6.w,
                      vertical: 4.h,
                    ),
                    labelPadding: EdgeInsets.symmetric(horizontal: 4.w),
                    materialTapTargetSize: MaterialTapTargetSize.padded,
                    visualDensity: VisualDensity.standard,
                    avatar: Icon(
                      item.isOwner ? Icons.key_rounded : Icons.home_outlined,
                      color: isSelected && item.isOwner
                          ? AppColors.sokoonGold
                          : foregroundColor,
                      size: 16.r,
                    ),
                    label: AppText(
                      item.isOwner
                          ? LocaleKeys.workspaceOwner
                          : LocaleKeys.workspaceTenant,
                      style: AppTextStyles.bold12.copyWith(
                        fontSize: 12.sp,
                        color: foregroundColor,
                        height: 1.45,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                );
              })
              .toList(growable: false),
        ),
      ),
    );
  }
}
