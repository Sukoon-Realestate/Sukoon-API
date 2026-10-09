import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';

class RenameSavedSearchDialog extends StatefulWidget {
  const RenameSavedSearchDialog({super.key, required this.name});
  final String name;
  @override
  State<RenameSavedSearchDialog> createState() =>
      _RenameSavedSearchDialogState();
}

class _RenameSavedSearchDialogState extends State<RenameSavedSearchDialog> {
  late final TextEditingController _name = TextEditingController(
    text: widget.name,
  );
  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: AppText(LocaleKeys.professionalRenameSearch),
    content: DefaultTextField(
      controller: _name,
      title: LocaleKeys.freeSavedSearches,
      maxLength: 80,
      action: TextInputAction.done,
    ),
    actions: [
      TextButton(
        onPressed: () => Go.back(),
        child: AppText(LocaleKeys.workspaceStay),
      ),
      TextButton(
        onPressed: () {
          if (_name.text.trim().isNotEmpty) Go.back(_name.text.trim());
        },
        child: AppText(LocaleKeys.professionalRenameSearch),
      ),
    ],
  );
}
