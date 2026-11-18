from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/bottom_navigation_redesign_test.dart')
s=p.read_text().replace('home: RepaintBoundary(\n                      key: boundary,','home: RepaintBoundary(')
s=s.replace('builder: (_, index, _) => HomeBottomNavigation(', 'builder: (_, index, _) => RepaintBoundary(key: boundary, child: HomeBottomNavigation(')
s=s.replace('''                                  selected.value = value;
                                },
                              ),''','''                                  selected.value = value;
                                },
                              )),''')
p.write_text(s)
