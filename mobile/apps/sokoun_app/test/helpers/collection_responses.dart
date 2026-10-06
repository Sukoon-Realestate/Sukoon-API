import 'dart:convert';
import 'dart:io';

/// Reads saved examples only; never sends requests or reads auth headers.
Map<String, dynamic> collectionResponseData(
  String pathPattern, {
  String method = 'GET',
  int responseIndex = 0,
}) {
  final root =
      jsonDecode(File('../../collection.json').readAsStringSync()) as Map;
  final collection = root['collection'] as Map;
  final pattern = RegExp(pathPattern);
  Map? match;
  void visit(List items) {
    for (final item in items.whereType<Map>()) {
      if (item['item'] is List) visit(item['item'] as List);
      final request = item['request'];
      if (request is! Map || request['method'] != method) continue;
      final url = request['url'];
      final raw = url is Map ? url['raw'] : url;
      if (pattern.hasMatch(raw.toString().split('?').first) &&
          item['response'] is List &&
          (item['response'] as List).isNotEmpty) {
        match = item;
      }
    }
  }

  visit(collection['item'] as List);
  if (match == null) throw StateError('No example for $method $pathPattern');
  final response = (match!['response'] as List)[responseIndex] as Map;
  final body = jsonDecode(response['body'] as String) as Map;
  return Map<String, dynamic>.from(body['data'] as Map);
}
