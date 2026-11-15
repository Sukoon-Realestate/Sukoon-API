from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/main_view/presentation/widgets/home_screen_content.dart')
s=p.read_text()
old='''                                      WorkspaceTab.housing ||
                                      WorkspaceTab.messages => false,'''
new='''                                      WorkspaceTab.housing ||
                                      WorkspaceTab.visits ||
                                      WorkspaceTab.messages => false,'''
assert old in s
p.write_text(s.replace(old,new,1))
