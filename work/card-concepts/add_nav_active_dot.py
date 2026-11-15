from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app')
p=root/'lib/features/main_view/presentation/widgets/home_navigation_item.dart'
s=p.read_text()
needle='''                  ),
                ],
              ),
            ),'''
assert s.count(needle)==1
s=s.replace(needle,'''                  ),
                  if (!rail)
                    AnimatedOpacity(
                      opacity: selected ? 1 : 0,
                      duration: SokounMotion.duration(context, milliseconds: 180),
                      curve: SokounMotion.curve,
                      child: Container(
                        width: 4,
                        height: 4,
                        decoration: BoxDecoration(
                          color: palette.accent,
                          shape: BoxShape.circle,
                        ),
                      ),
                    ),
                ],
              ),
            ),''',1)
p.write_text(s)
p=root/'test/bottom_navigation_redesign_test.dart'
s=p.read_text()
needle='''              final bounds = tester.getRect(messages);'''
s=s.replace(needle,'''              expect(tester.widgetList<AnimatedOpacity>(find.descendant(
                of: find.byType(HomeBottomNavigation), matching: find.byType(AnimatedOpacity),
              )).where((w) => w.opacity == 1).length, 1);
              final bounds = tester.getRect(messages);''',1)
needle='''              expect(selected.value, 2);'''
s=s.replace(needle,'''              expect(selected.value, 2);
              final dot = tester.widget<AnimatedOpacity>(find.descendant(
                of: messages, matching: find.byType(AnimatedOpacity),
              ));
              expect(dot.opacity, 1);
              expect(dot.duration, reduced ? Duration.zero : const Duration(milliseconds: 180));''',1)
p.write_text(s)
