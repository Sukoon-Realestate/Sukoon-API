from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/tenant/visits/presentation/widgets/tenant_visits/tenant_visits_list.dart')
s=p.read_text()
old='''      if (header != null) header!,
      TenantVisitsFilters('''
new='''      if (header != null) ...[
        header!,
        const SizedBox(height: 16),
      ],
      TenantVisitsFilters('''
assert s.count(old)==1
p.write_text(s.replace(old,new))
