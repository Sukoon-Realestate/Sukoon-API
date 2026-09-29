import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';

/// Protects a pushed editor from back navigation and cross-workspace links.
class UnsavedChangesGuard extends StatefulWidget {
  const UnsavedChangesGuard({
    super.key,
    required this.hasChanges,
    required this.isSaving,
    required this.child,
  });

  final bool Function() hasChanges;
  final bool Function() isSaving;
  final Widget child;

  @override
  State<UnsavedChangesGuard> createState() => _UnsavedChangesGuardState();
}

class _UnsavedChangesGuardState extends State<UnsavedChangesGuard> {
  final ValueNotifier<bool> _allowPop = ValueNotifier(false);
  bool _confirming = false;

  @override
  void initState() {
    super.initState();
    WorkspaceNavigation.addLeaveGuard(_confirmLeave);
  }

  @override
  void dispose() {
    WorkspaceNavigation.removeLeaveGuard(_confirmLeave);
    _allowPop.dispose();
    super.dispose();
  }

  Future<bool> _confirmLeave() async {
    if (!mounted || widget.isSaving() || _confirming) return false;
    _confirming = true;
    try {
      final bool leave =
          !widget.hasChanges() ||
          await showDialog<bool>(
                context: context,
                builder: (_) => AlertDialog(
                  title: AppText(
                    LocaleKeys.workspaceDiscardTitle,
                    style: AppTextStyles.regular,
                  ),
                  content: AppText(
                    LocaleKeys.workspaceDiscardMessage,
                    style: AppTextStyles.regular,
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Go.back(false),
                      child: AppText(
                        LocaleKeys.workspaceStay,
                        style: AppTextStyles.regular,
                      ),
                    ),
                    TextButton(
                      onPressed: () => Go.back(true),
                      child: AppText(
                        LocaleKeys.workspaceDiscard,
                        style: AppTextStyles.regular,
                      ),
                    ),
                  ],
                ),
              ) ==
              true;
      if (!mounted || !leave) return false;
      _allowPop.value = true;
      await WidgetsBinding.instance.endOfFrame;
      return mounted;
    } finally {
      _confirming = false;
    }
  }

  @override
  Widget build(BuildContext context) => ValueListenableBuilder<bool>(
    valueListenable: _allowPop,
    builder: (context, allowPop, child) => PopScope(
      canPop: allowPop,
      onPopInvokedWithResult: (didPop, _) async {
        if (!didPop && await _confirmLeave() && mounted) Go.back();
      },
      child: child!,
    ),
    child: widget.child,
  );
}
