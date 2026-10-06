class RequestModel {
  const RequestModel({required this.userId});

  const RequestModel.initial() : userId = '';

  final String userId;

  RequestModel copyWith({String? userId}) {
    return RequestModel(userId: userId ?? this.userId);
  }

  Map<String, dynamic> toJson() => {'user_id': userId};
}
