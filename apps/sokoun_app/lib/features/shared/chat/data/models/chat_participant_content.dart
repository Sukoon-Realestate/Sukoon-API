import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/contact/data/phone_disclosure.dart';

class ChatParticipantContent extends Equatable {
  const ChatParticipantContent({
    required this.id,
    this.firstName = '',
    this.lastName = '',
    this.fullName = '',
    this.email = '',
    this.avatarUrl = '',
    this.phoneNumber = '',
    this.isPhoneRevealed = false,
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
      phoneNumber = '',
      isPhoneRevealed = false,
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
      phoneNumber: json['phone_number']?.toString() ?? '',
      isPhoneRevealed: json['is_phone_revealed'] == true,
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
  final String phoneNumber;
  final bool isPhoneRevealed;
  String get revealedPhone => PhoneDisclosure.revealedPhone(
    phoneNumber: phoneNumber,
    isPhoneRevealed: isPhoneRevealed,
  );
  final bool isOnline;
  final bool isVerified;

  Map<String, dynamic> toJson() => {
    'id': id,
    'first_name': firstName,
    'last_name': lastName,
    'full_name': fullName,
    'email': email,
    'avatar_url': avatarUrl,
    'phone_number': phoneNumber,
    'is_phone_revealed': isPhoneRevealed,
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
    String? phoneNumber,
    bool? isPhoneRevealed,
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
      phoneNumber: phoneNumber ?? this.phoneNumber,
      isPhoneRevealed: isPhoneRevealed ?? this.isPhoneRevealed,
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
    phoneNumber,
    isPhoneRevealed,
    isOnline,
    isVerified,
  ];
}
