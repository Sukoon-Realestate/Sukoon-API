from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib')
p=root/'features/shared/personal_tools/presentation/widgets/remembered_filters.dart'
s=p.read_text().replace('    required this.reset,','    required this.reset,\n    this.showReset = true,')
s=s.replace('  final String namespace, scope;', '  final String namespace, scope;\n  final bool showReset;')
s=s.replace('''                  TextButton.icon(
                    icon: const Icon(Icons.settings_backup_restore),''','''                  if (widget.showReset) TextButton.icon(
                    icon: const Icon(Icons.settings_backup_restore),''')
p.write_text(s)
p=root/'features/tenant/visits/presentation/screens/tenant_visits_screen.dart'
s=p.read_text().replace('''                RememberedFilters(
                  namespace: 'tenant_visit_filters',''', '''                RememberedFilters(
                  showReset: false,
                  namespace: 'tenant_visit_filters',''')
p.write_text(s)
p=root/'features/tenant/visits/presentation/widgets/tenant_visits/tenant_visits_list.dart'
s=p.read_text().replace('      VisitCollectionCount(initialCount: initialVisits?.length),\n','')
p.write_text(s)
