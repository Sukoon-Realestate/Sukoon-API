import 'dart:convert';
import 'dart:developer';
import 'dart:io';
import 'package:watcher/watcher.dart';
import '../utils/exceptions.dart';
import '../utils/generate_constants.dart';
import 'models/names.dart';

/// TO run this file, write this command in terminal:
/// "dart generate/strings/main.dart"
Future<void> main(List<String> args) async {
  final bool watch = args.contains('--watch');
  await generateTranslations();

  if (!watch) {
    return;
  }

  const String filePath = GenerateConstants.langJsonAssetFilePath;
  final File file = File(filePath);
  final FileWatcher watcher = FileWatcher(filePath);
  String previousContent = file.readAsStringSync();

  watcher.events.listen((WatchEvent event) {
    if (event.type == ChangeType.MODIFY) {
      log('File changed: ${watcher.path}');
      handleFileChange(file, previousContent);
      previousContent = file.readAsStringSync();
    }
  });
  log('Watching for changes in: ${watcher.path}');
}

Future<void> generateTranslations() async {
  const String filePath = GenerateConstants.langJsonAssetFilePath;
  final File file = File(filePath);
  final Map<String, dynamic> jsonMap = json.decode(file.readAsStringSync());
  final Map<String, dynamic> jsonEnMap = await generateJsonTranslate(
    lang: 'en',
    jsonMap: jsonMap,
  );
  await generateJsonTranslate(lang: 'ar', jsonMap: jsonMap);
  await generateAppStrings(jsonEnMap);
}

void handleFileChange(File file, String previousContent) async {
  try {
    final String currentContent = file.readAsStringSync();
    final List<String> currentLines = currentContent.split('\n');
    final List<String> previousLines = previousContent.split('\n');

    for (int i = 0; i < currentLines.length; i++) {
      if (i >= previousLines.length || currentLines[i] != previousLines[i]) {
        log('Line ${i + 1} changed');
        log(
          'Previous: ${(i) >= previousLines.length ? 'null' : previousLines[i]}',
        );
        log('Current: ${currentLines[i]}');
        log('------------------------------------------------------');
      }
    }
    previousContent = currentContent;
    final Map<String, dynamic> jsonMap = json.decode(currentContent);
    final Map<String, dynamic> jsonEnMap = await generateJsonTranslate(
      lang: 'en',
      jsonMap: jsonMap,
    );
    await generateJsonTranslate(lang: 'ar', jsonMap: jsonMap);
    await generateAppStrings(jsonEnMap);
  } catch (e) {
    log('Uknown Key');
  }
}

Future<Map<String, dynamic>> generateJsonTranslate({
  required String lang,
  required Map<String, dynamic> jsonMap,
}) async {
  final StringBuffer buffer = StringBuffer();
  final String filePath = lang == 'en'
      ? GenerateConstants.langEnJsonAssetFilePath
      : lang == 'ar'
      ? GenerateConstants.langArJsonAssetFilePath
      : '';
  final File file = File(filePath);
  buffer.writeln('{');
  // String content = file.readAsStringSync().trim();
  // final Map<String, dynamic> fileMap = json.decode(content);
  // List<String> lines = content.split('\n');
  // List<String> linesWithoutLastCurlBrace = lines.sublist(0, lines.length - 1);
  // buffer.writeAll(linesWithoutLastCurlBrace, '\n');
  // String bufferStringTrim = buffer.toString().trim();
  // bufferStringTrim = '$bufferStringTrim,';
  // buffer.clear();
  // buffer.writeln(bufferStringTrim);
  int counter = 0;
  //print('fileMap ${fileMap.toString()}');
  jsonMap.forEach((String key, value) {
    //print('$lang($counter)  "$key": "$value"');
    try {
      final Names keyNames = Names.fromString(key);
      // if (!fileMap.containsKey(keyNames.snakeCase)) {
      //print('$lang($counter)  !containsKey "${keyNames.snakeCase}" ');
      lang == 'en'
          ? buffer.write('  "${keyNames.snakeCase}": "${keyNames.original}"')
          : buffer.write('  "${keyNames.snakeCase}": "$value"');
      if (counter < jsonMap.length - 1) {
        buffer.write(',');
        // }
        buffer.writeln();
      }
    } on NamesException {
      final String keyStr = '[$key]';
      const String errorMessage = 'is not valid!';
      log(
        '${GenerateConstants.blueColorCode} $keyStr ${GenerateConstants.redColorCode}$errorMessage',
      );
    }
    counter++;
  });
  final List<String> linesAfterWrite = buffer.toString().trim().split('\n');
  String lastLineOfLinesAfterWrite = linesAfterWrite.last.trimRight();
  //print('lastLineOfLinesAfterWrite $lastLineOfLinesAfterWrite');
  if (lastLineOfLinesAfterWrite[lastLineOfLinesAfterWrite.length - 1] == ',') {
    lastLineOfLinesAfterWrite = lastLineOfLinesAfterWrite.substring(
      0,
      lastLineOfLinesAfterWrite.length - 1,
    );
    linesAfterWrite[linesAfterWrite.length - 1] = lastLineOfLinesAfterWrite;
    buffer.clear();
    buffer.writeAll(linesAfterWrite, '\n');
  }
  buffer.writeln('');
  buffer.writeln('}');
  await file.writeAsString(buffer.toString());
  log(
    '${GenerateConstants.greenColorCode} Lang Json File Updated successfully at $filePath ${GenerateConstants.resetColorCode}',
  );
  return json.decode(buffer.toString());
}

Future<void> generateAppStrings(Map<String, dynamic> jsonMap) async {
  final StringBuffer buffer = StringBuffer();
  // String content = file.readAsStringSync();
  // List<String> lines = content.split('\n');
  // List<String> linesWithoutLastCurlBrace = lines.sublist(0, lines.length - 1);
  // buffer.writeln();
  // buffer.writeAll(linesWithoutLastCurlBrace, '\n');
  // buffer.writeln();
  buffer.writeln(
    'import \'package:easy_localization/easy_localization.dart\';',
  );
  buffer.writeln();
  buffer.writeln('abstract class LocaleKeys {');
  jsonMap.forEach((String key, _) {
    try {
      final Names keyNames = Names.fromString(key);
      buffer.writeln(
        "  static const String _${keyNames.camelCase} = '${keyNames.original}';",
      );
      buffer.writeln(
        '  static String get ${keyNames.camelCase} => _${keyNames.camelCase}.tr();',
      );
      buffer.writeln();
    } on NamesException {
      final String keyStr = '[$key]';
      const String errorMessage = 'is not valid!';
      log(
        '${GenerateConstants.blueColorCode} $keyStr ${GenerateConstants.redColorCode}$errorMessage',
      );
    }
  });
  buffer.writeln('}');
  final File file = File(GenerateConstants.outputStringsFilePath);
  await file.writeAsString(buffer.toString());
  log(
    '${GenerateConstants.greenColorCode} class AppStrings Generated successfully at ${GenerateConstants.outputStringsFilePath} ${GenerateConstants.resetColorCode}',
  );
}
