import 'package:equatable/equatable.dart';

class ChatParticipantContent extends Equatable {
  const ChatParticipantContent({
    required this.id,
    this.firstName = '',
    this.lastName = '',
    this.fullName = '',
    this.email = '',
    this.avatarUrl = '',
    this.isOnline = false,
    this.isVerified = true,
  });

  const ChatParticipantContent.initial()
    : id = '',
      firstName = '',
      lastName = '',
      fullName = '',
      email = '',
      avatarUrl = '',
      isOnline = false,
      isVerified = true;

  factory ChatParticipantContent.fromJson(Map<String, dynamic> json) {
    final String firstName = json['first_name']?.toString() ?? '';
    final String lastName = json['last_name']?.toString() ?? '';
    final String fullName =
        (json['full_name'] ?? json['name'])?.toString().trim() ?? '';
    final String composedName = [
      firstName,
      lastName,
    ].where((part) => part.trim().isNotEmpty).join(' ');

    return ChatParticipantContent(
      id: json['id']?.toString() ?? '',
      firstName: firstName,
      lastName: lastName,
      fullName: fullName.isNotEmpty ? fullName : composedName,
      email: json['email']?.toString() ?? '',
      avatarUrl:
          json['avatar_url']?.toString() ?? json['avatar']?.toString() ?? '',
      isOnline: json['is_online'] as bool? ?? false,
      isVerified: json['is_verified'] as bool? ?? true,
    );
  }

  final String id;
  final String firstName;
  final String lastName;
  final String fullName;
  final String email;
  final String avatarUrl;
  final bool isOnline;
  final bool isVerified;

  Map<String, dynamic> toJson() => {
    'id': id,
    'first_name': firstName,
    'last_name': lastName,
    'full_name': fullName,
    'email': email,
    'avatar_url': avatarUrl,
    'is_online': isOnline,
    'is_verified': isVerified,
  };

  ChatParticipantContent copyWith({
    String? id,
    String? firstName,
    String? lastName,
    String? fullName,
    String? email,
    String? avatarUrl,
    bool? isOnline,
    bool? isVerified,
  }) {
    return ChatParticipantContent(
      id: id ?? this.id,
      firstName: firstName ?? this.firstName,
      lastName: lastName ?? this.lastName,
      fullName: fullName ?? this.fullName,
      email: email ?? this.email,
      avatarUrl: avatarUrl ?? this.avatarUrl,
      isOnline: isOnline ?? this.isOnline,
      isVerified: isVerified ?? this.isVerified,
    );
  }

  @override
  List<Object?> get props => [
    id,
    firstName,
    lastName,
    fullName,
    email,
    avatarUrl,
    isOnline,
    isVerified,
  ];
}
