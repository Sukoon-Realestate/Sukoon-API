from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/ux60_identity_correction_test.dart')
s=p.read_text().replace('''                child: AppScaffold(
                  title: LocaleKeys.uploadDocumentsTitle,
                  body: IdentityCorrectionForm(data: cubit.data),
                ),''', '''                child: Builder(
                  builder: (_) => AppScaffold(
                    title: LocaleKeys.uploadDocumentsTitle,
                    body: IdentityCorrectionForm(data: cubit.data),
                  ),
                ),''')
p.write_text(s)
