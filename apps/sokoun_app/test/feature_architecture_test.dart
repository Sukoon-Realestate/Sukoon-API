import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  final Directory features = _featuresDirectory();
  final List<File> dartFiles = features
      .listSync(recursive: true)
      .whereType<File>()
      .where((file) => file.path.endsWith('.dart'))
      .toList(growable: false);

  group('Sokoun feature architecture', () {
    test('data code never imports presentation code', () {
      final violations = <String>[];
      for (final File file in dartFiles.where(_isDataFile)) {
        final String source = file.readAsStringSync();
        if (RegExp(r'''import\s+['"][^'"]*/presentation/''').hasMatch(source)) {
          violations.add(_relativePath(file));
        }
      }
      expect(violations, isEmpty, reason: violations.join('\n'));
    });

    test('screens and widgets do not use network primitives directly', () {
      const forbidden = <String>[
        'NetworkRequest(',
        'NetworkService',
        'CrudBaseParmas<',
        'ApiConstants.',
      ];
      final violations = <String>[];
      for (final File file in dartFiles.where(_isVisualPresentationFile)) {
        final String source = file.readAsStringSync();
        for (final String token in forbidden) {
          if (source.contains(token)) {
            violations.add('${_relativePath(file)} uses $token');
          }
        }
      }
      expect(violations, isEmpty, reason: violations.join('\n'));
    });

    test('feature navigation uses Go', () {
      const forbidden = <String>[
        'Navigator.',
        'MaterialPageRoute',
        'CupertinoPageRoute',
      ];
      final violations = <String>[];
      for (final File file in dartFiles) {
        final String source = file.readAsStringSync();
        for (final String token in forbidden) {
          if (source.contains(token)) {
            violations.add('${_relativePath(file)} uses $token');
          }
        }
      }
      expect(violations, isEmpty, reason: violations.join('\n'));
    });

    test('status builders use the shimmer constructor', () {
      final violations = <String>[];
      for (final File file in dartFiles) {
        final String source = file.readAsStringSync();
        int offset = 0;
        while (true) {
          final int index = source.indexOf('StatusBuilder<', offset);
          if (index < 0) break;
          final int end = (index + 300).clamp(0, source.length);
          final String callSite = source.substring(index, end);
          if (!RegExp(r'>\s*\.withShimmer\s*\(').hasMatch(callSite)) {
            violations.add('${_relativePath(file)}:$index');
          }
          offset = index + 1;
        }
      }
      expect(violations, isEmpty, reason: violations.join('\n'));
    });

    test('base CRUD GETs have cache and reconnect contracts', () {
      final violations = <String>[];
      for (final File file in dartFiles) {
        final String source = file.readAsStringSync();
        if (!source.contains('httpRequestType: HttpRequestType.get')) continue;

        const requiredTokens = <String>[
          'cacheKey:',
          'fromCacheJson:',
          'toJson:',
          'withInternetInterceptor:',
        ];
        for (final String token in requiredTokens) {
          if (!source.contains(token)) {
            violations.add('${_relativePath(file)} misses $token');
          }
        }
      }
      expect(violations, isEmpty, reason: violations.join('\n'));
    });

    test('API dropdowns have complete cache contracts', () {
      final violations = <String>[];
      for (final File file in dartFiles.where(_isVisualPresentationFile)) {
        final String source = file.readAsStringSync();
        if (!source.contains('>.withApiRequest(') &&
            !source.contains('>.withApiSearchRequest(')) {
          continue;
        }

        const requiredTokens = <String>[
          'cacheKey:',
          'cacheToJson:',
          'cacheFromJson:',
        ];
        for (final String token in requiredTokens) {
          if (!source.contains(token)) {
            violations.add('${_relativePath(file)} misses $token');
          }
        }
      }
      expect(violations, isEmpty, reason: violations.join('\n'));
    });

    test('presentation uses translations and semantic colors', () {
      final violations = <String>[];
      final RegExp arabicLiteral = RegExp(r'''['"][^'"]*[\u0621-\u064A]''');
      for (final File file in dartFiles.where(_isVisualPresentationFile)) {
        final String source = file.readAsStringSync();
        if (arabicLiteral.hasMatch(source)) {
          violations.add('${_relativePath(file)} has Arabic display literals');
        }
        if (source.contains('Color(0x') ||
            RegExp(r'(^|[^A-Za-z0-9_])Colors\.').hasMatch(source)) {
          violations.add('${_relativePath(file)} has raw colors');
        }
      }
      expect(violations, isEmpty, reason: violations.join('\n'));
    });

    test('assigned widget keys represent real lifecycle identity', () {
      final RegExp valueKey = RegExp(r'ValueKey\(([^\)]*)\)');
      final violations = <String>[];
      for (final File file in dartFiles.where(_isVisualPresentationFile)) {
        final String source = file.readAsStringSync();
        if (source.contains('UniqueKey(') || source.contains('ObjectKey(')) {
          violations.add(
            '${_relativePath(file)} uses unstable or object-based identity',
          );
        }
        if (RegExp(r'key:\s*(?:const\s+)?Key\(').hasMatch(source)) {
          violations.add('${_relativePath(file)} uses a decorative Key');
        }

        for (final RegExpMatch match in valueKey.allMatches(source)) {
          final String identity = match.group(1) ?? '';
          final bool usesDomainId = RegExp(
            r'\.\s*id\b|\b[A-Za-z_][A-Za-z0-9_]*Id\b',
          ).hasMatch(identity);
          final bool resetsOwnedState =
              identity.contains('ResetKey') ||
              identity.contains('dropdownGeneration');
          final bool switchesAnimatedState =
              source.contains('AnimatedSwitcher(') &&
              (identity.contains('update-loading') ||
                  identity.contains('update-idle'));
          if (!usesDomainId && !resetsOwnedState && !switchesAnimatedState) {
            violations.add(
              '${_relativePath(file)} uses ValueKey($identity) without stable identity',
            );
          }
        }
      }
      expect(violations, isEmpty, reason: violations.join('\n'));
    });
  });
}

Directory _featuresDirectory() {
  const candidates = <String>['lib/features', 'apps/sokoun_app/lib/features'];
  for (final String path in candidates) {
    final Directory directory = Directory(path);
    if (directory.existsSync()) return directory;
  }
  throw StateError('Could not locate apps/sokoun_app/lib/features');
}

bool _isDataFile(File file) => file.path.contains('/data/');

bool _isVisualPresentationFile(File file) =>
    file.path.contains('/presentation/screens/') ||
    file.path.contains('/presentation/widgets/');

String _relativePath(File file) => file.path
    .replaceFirst('${Directory.current.path}/', '')
    .replaceAll('\\', '/');
