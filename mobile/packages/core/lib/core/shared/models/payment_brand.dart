class PaymentBrand {
  final int? id;
  final String? image;
  final String? name;
  final String? type;
  final String? status;
  final String? entityId;

  PaymentBrand({
    this.id,
    this.image,
    this.name,
    this.type,
    this.status,
    this.entityId,
  });

  factory PaymentBrand.fromJson(Map<String, dynamic> json) {
    return PaymentBrand(
      id: json['id'],
      image: json['image'],
      name: json['name'],
      type: json['type'],
      status: json['status'],
      entityId: json['entity_id'],
    );
  }
}