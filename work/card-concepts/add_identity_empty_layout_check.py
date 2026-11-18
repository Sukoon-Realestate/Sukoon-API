from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/ux60_identity_correction_test.dart')
s=p.read_text()
idx=s.rfind('\n}')
s=s[:idx]+'''
  for (final dark in [false, true]) {
    for (final scale in [1.0, 2.0]) {
      testWidgets('initial missing documents dark=$dark scale=$scale', (tester) async {
        tester.view.physicalSize = const Size(390, 900);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        final payload = projection();
        payload['documents'] = [
          for (final doc in payload['documents'] as List)
            {...doc as Map<String, dynamic>, 'status': 'missing', 'present': false,
              'can_replace': true, 'reason': ''},
        ];
        repository.replies[ApiConstants.verificationStatus] = FeatureTestReply(data: payload);
        final cubit = create();
        await cubit.load();
        final boundary = GlobalKey();
        await tester.pumpWidget(featureTestHost(
          BlocProvider.value(value: cubit, child: RepaintBoundary(
            key: boundary,
            child: AppScaffold(title: LocaleKeys.uploadDocumentsTitle,
              body: IdentityCorrectionForm(data: cubit.data)),
          )), dark: dark, scale: scale,
        ));
        await tester.pumpAndSettle();
        expect(find.text(LocaleKeys.idFrontLabel), findsOneWidget);
        expect(find.text(LocaleKeys.nationalId), findsOneWidget);
        expect(tester.takeException(), isNull);
        if (scale == 1) {
          await tester.runAsync(() async {
            final render = boundary.currentContext!.findRenderObject()! as RenderRepaintBoundary;
            final image = await render.toImage(pixelRatio: 2);
            final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
            await File('/tmp/identity-clean-preview/missing-${dark ? 'dark' : 'light'}.png')
              .writeAsBytes(bytes!.buffer.asUint8List());
            image.dispose();
          });
        }
        await tester.pumpWidget(const SizedBox.shrink());
      });
    }
  }
''' +s[idx:]
p.write_text(s)
