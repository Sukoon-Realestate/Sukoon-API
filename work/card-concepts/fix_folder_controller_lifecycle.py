from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/screens/saved_folders_screen.dart')
s=p.read_text()
a=s.index('  Future<String?> _name(')
b=s.index('\n  @override', a)
s=s[:a]+'''  Future<String?> _name(BuildContext context, [String initial = '']) =>
      showDefaultBottomSheet<String>(
        context: context,
        isScrollControlled: true,
        builder: (_) => _FolderNameSheet(initialName: initial),
      );
''' +s[b:]
s+='''
/// The sheet retains its controller until the reverse transition unmounts it.
class _FolderNameSheet extends StatefulWidget {
  const _FolderNameSheet({required this.initialName});
  final String initialName;

  @override
  State<_FolderNameSheet> createState() => _FolderNameSheetState();
}

class _FolderNameSheetState extends State<_FolderNameSheet> {
  late final TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.initialName);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    padding: const EdgeInsets.all(20),
    child: Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          controller: _controller,
          autofocus: true,
          maxLength: 60,
          decoration: InputDecoration(labelText: LocaleKeys.personalFolderName),
        ),
        FilledButton(
          onPressed: () {
            final name = _controller.text.trim();
            if (name.isNotEmpty) Go.back(name);
          },
          child: Text(LocaleKeys.personalSave),
        ),
      ],
    ),
  );
}
'''
p.write_text(s)
