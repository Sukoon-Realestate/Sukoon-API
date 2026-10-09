enum PropertyUploadStatus { queued, sending, confirmed, failed, unknown }

class PropertyUploadProgress {
  const PropertyUploadProgress({
    required this.reference,
    this.status = PropertyUploadStatus.queued,
    this.sent = 0,
    this.total = 0,
    this.imageId = '',
  });
  final String reference;
  final PropertyUploadStatus status;
  final int sent;
  final int total;
  final String imageId;
  double? get fraction => total > 0 ? (sent / total).clamp(0, 1) : null;
  Map<String, dynamic> toJson() => {
    'reference': reference,
    'status': status.name,
    'sent': sent,
    'total': total,
    'image_id': imageId,
  };
  factory PropertyUploadProgress.fromJson(Map<String, dynamic> json) {
    PropertyUploadStatus status = PropertyUploadStatus.values.firstWhere(
      (value) => value.name == json['status'],
      orElse: () => PropertyUploadStatus.unknown,
    );
    if (status == PropertyUploadStatus.sending) {
      status = PropertyUploadStatus.unknown;
    }
    return PropertyUploadProgress(
      reference: json['reference'] as String? ?? '',
      status: status,
      sent: (json['sent'] as num?)?.toInt() ?? 0,
      total: (json['total'] as num?)?.toInt() ?? 0,
      imageId: json['image_id'] as String? ?? '',
    );
  }
}
