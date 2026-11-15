from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/tenant/favorites/presentation/widgets/favorites_screen_content.dart')
s=p.read_text()
old='''                flatAppBar: true,
'''
new='''                flatAppBar: true,
                // These independently scrolling tabs must not share a
                // collapsible outer header offset when switching tabs.
                scrollAppBar: false,
'''
assert s.count(old)==1
p.write_text(s.replace(old,new))
