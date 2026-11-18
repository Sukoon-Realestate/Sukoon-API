from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/widgets/housing_budget_form.dart')
s=p.read_text().replace("import 'package:sokoun_app/shared_widgets/sokoun_settings_section.dart';\n", '')
s=s.replace('''                padding: const EdgeInsets.only(bottom: 12),
                child: SokounSettingsSection(
                  title: _label(key),
                  child: Column(''', '''                padding: const EdgeInsets.only(bottom: 20),
                child: Column(''')
s=s.replace('''                    children: [
                      TextFormField(''', '''                    children: [
                      Text(_label(key), style: Theme.of(context).textTheme.titleSmall),
                      TextFormField(''',1)
s=s.replace('''                    ],
                  ),
                ),
              ),
            const SizedBox(height: 8),''','''                    ],
                ),
              ),
            const SizedBox(height: 8),''',1)
p.write_text(s)
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/housing_budget_clean_layout_test.dart')
s=p.read_text().replace('child: RepaintBoundary(key: boundary, child: HousingBudgetForm(', 'child: RepaintBoundary(key: boundary, child: ColoredBox(color: Theme.of(tester.element(find.byType(Scaffold))).scaffoldBackgroundColor, child: HousingBudgetForm(') if False else p.read_text()
# Capture the canvas in the preview, without changing the actual sheet widget.
s=s.replace('child: RepaintBoundary(key: boundary, child: HousingBudgetForm(', 'child: RepaintBoundary(key: boundary, child: Material(child: HousingBudgetForm(')
s=s.replace('''              )),
            )),''','''              ))),
            )),''')
p.write_text(s)
