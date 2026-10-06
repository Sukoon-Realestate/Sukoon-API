import 'dart:convert';
import 'dart:developer';
import 'dart:io';

/// Run with: dart run tool/generate_models.dart
/// Reads postman_collection.json -> extracts example responses ->
/// generates Freezed models in lib/models/

void main() async {
  final file = File('postman_collection.json');
  if (!await file.exists()) {
    log('❌ postman_collection.json not found!');
    return;
  }

  final data = jsonDecode(await file.readAsString());
  final items = data['item'] as List;

  for (final item in items) {
    final name = _normalizeName(item['name']);
    final responses = item['response'] as List?;
    if (responses == null || responses.isEmpty) continue;

    final body = responses.first['body'];
    if (body == null || body.toString().isEmpty) continue;

    try {
      final jsonBody = jsonDecode(body);

      final modelCode = _generateFreezedModel(name, jsonBody);

      final outFile = File('lib/models/${name.toLowerCase()}_model.dart');
      await outFile.create(recursive: true);
      await outFile.writeAsString(modelCode);

      log('✅ Generated Freezed model: ${outFile.path}');
    } catch (e) {
      log('⚠️ Skipped ${item['name']} (invalid JSON example)');
    }
  }
}

String _normalizeName(String name) {
  // Remove spaces/special chars, make PascalCase
  final clean = name.replaceAll(RegExp(r'[^a-zA-Z0-9]'), '');
  return clean[0].toUpperCase() + clean.substring(1);
}

/// Generate a Freezed + json_serializable model
String _generateFreezedModel(String className, dynamic json) {
  final buffer = StringBuffer();

  final fileName = className.toLowerCase();

  buffer
      .writeln("import 'package:freezed_annotation/freezed_annotation.dart';");
  buffer.writeln();
  buffer.writeln("part '${fileName}_model.freezed.dart';");
  buffer.writeln("part '${fileName}_model.g.dart';");
  buffer.writeln();
  buffer.writeln('@freezed');
  buffer.writeln('class ${className}Model with _\$${className}Model {');
  buffer.writeln('  const factory ${className}Model({');

  if (json is Map<String, dynamic>) {
    json.forEach((key, value) {
      buffer.writeln('    required ${_mapType(value)} $key,');
    });
  }

  buffer.writeln('  }) = _${className}Model;');
  buffer.writeln();
  buffer.writeln(
      '  factory ${className}Model.fromJson(Map<String, dynamic> json) => _\$${className}ModelFromJson(json);');
  buffer.writeln('}');

  return buffer.toString();
}

String _mapType(dynamic value) {
  if (value is int) return 'int';
  if (value is double) return 'double';
  if (value is bool) return 'bool';
  if (value is List) return 'List<dynamic>';
  if (value is Map) return 'Map<String, dynamic>';
  return 'String';
}
