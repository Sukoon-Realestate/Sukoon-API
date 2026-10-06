class PremiumRevisionBody {
  const PremiumRevisionBody({required this.revision, required this.requestKey});
  final int revision;
  final String requestKey;
  Map<String, dynamic> toJson() => {
    'revision': revision,
    'request_key': requestKey,
  };
}
