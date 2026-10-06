num ownerPropertyNumber(dynamic value) =>
    value is num ? value : num.tryParse('$value') ?? 0;
Iterable<Map<String, dynamic>> ownerPropertyMaps(dynamic value) =>
    (value is List ? value : const []).whereType<Map>().map(
      (item) => Map<String, dynamic>.from(item),
    );

String ownerFormattedNumber(num value) {
  final text = value.toStringAsFixed(2).replaceFirst(RegExp(r'\.?0+$'), '');
  final parts = text.split('.');
  final whole = parts.first.replaceAllMapped(
    RegExp(r'(\d)(?=(\d{3})+(?!\d))'),
    (match) => '${match[1]},',
  );
  return parts.length > 1 ? '$whole.${parts.last}' : whole;
}
