from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/screens/saved_folders_screen.dart')
s=p.read_text()
s=s.replace('padding: const EdgeInsets.all(16),', 'padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),', 1)
s=s.replace('            Text(LocaleKeys.personalDeviceOnly),\n', '            Text(LocaleKeys.personalDeviceOnly),\n            const SizedBox(height: 16),\n', 1)
s=s.replace('            for (final folder in state.value.folders)\n', '            if (state.value.folders.isNotEmpty) const SizedBox(height: 20),\n            for (final folder in state.value.folders)\n', 1)
p.write_text(s)
