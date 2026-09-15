import 'package:equatable/equatable.dart';

class ChatReadContent extends Equatable {
  const ChatReadContent({required this.status});

  const ChatReadContent.initial() : status = '';

  factory ChatReadContent.fromJson(Map<String, dynamic> json) {
    return ChatReadContent(status: json['status']?.toString() ?? '');
  }

  final String status;

  Map<String, dynamic> toJson() => {'status': status};

  ChatReadContent copyWith({String? status}) {
    return ChatReadContent(status: status ?? this.status);
  }

  @override
  List<Object?> get props => [status];
}
