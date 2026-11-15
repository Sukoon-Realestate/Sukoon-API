from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib')
p=root/'features/tenant/decision_tools/presentation/widgets/property_memory_badge.dart'
s=p.read_text().replace("    this.current,", "    this.current,\n    this.contentPadding = EdgeInsets.zero,")
s=s.replace('  final FavoriteSnapshot? current;', '  final FavoriteSnapshot? current;\n  final EdgeInsetsGeometry contentPadding;')
s=s.replace('      return Wrap(\n        spacing: 8,\n        children: [','      final children = <Widget>[')
s=s.replace('''        ],
      );''','''      ];
      if (children.isEmpty) return const SizedBox.shrink();
      return Padding(
        padding: contentPadding,
        child: Wrap(spacing: 8, runSpacing: 8, children: children),
      );''')
p.write_text(s)
p=root/'features/tenant/home/presentation/widgets/tenant_widgets/tenant_property_card.dart'
s=p.read_text().replace('PropertyMemoryBadge(propertyId: propertyId)', '''PropertyMemoryBadge(
              propertyId: propertyId,
              contentPadding: EdgeInsetsDirectional.fromSTEB(12.r, 12.h, 12.r, 0),
            )''')
p.write_text(s)
p=root/'features/tenant/home/presentation/widgets/tenant_search_results/search_result_card.dart'
s=p.read_text().replace('PropertyMemoryBadge(propertyId: item.id)', '''PropertyMemoryBadge(
                propertyId: item.id,
                contentPadding: EdgeInsetsDirectional.fromSTEB(14.w, 12.h, 14.w, 0),
              )''')
p.write_text(s)
