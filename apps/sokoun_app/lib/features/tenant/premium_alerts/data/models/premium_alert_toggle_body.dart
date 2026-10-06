class PremiumAlertToggleBody {
  const PremiumAlertToggleBody({
    required this.enabled,
    required this.revision,
    required this.requestKey,
  });
  final bool enabled;
  final int revision;
  final String requestKey;
  Map<String, dynamic> toJson() => {
    'enabled': enabled,
    'revision': revision,
    'request_key': requestKey,
  };
}
