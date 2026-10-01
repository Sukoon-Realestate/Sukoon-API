part of '../../imports.dart';

class ProfileEditBody {
  const ProfileEditBody({
    required this.avatar,
    required this.fullName,
    required this.gender,
    required this.phoneNumber,
  });

  const ProfileEditBody.initial()
    : avatar = null,
      fullName = '',
      gender = '',
      phoneNumber = '';

  final File? avatar;
  final String fullName;
  final String gender;
  final String phoneNumber;

  Map<String, dynamic> toJson() => {
    if (avatar != null) 'avatar': avatar,
    'full_name': fullName,
    'gender': gender,
    'phone_number': phoneNumber,
  };

  Map<String, dynamic> toUserJson() {
    final List<String> names = fullName.trim().split(RegExp(r'\s+'));
    return {
      if (avatar != null) 'avatar': avatar,
      'first_name': names.first,
      'last_name': names.skip(1).join(' '),
      'gender': gender,
      'phone_number': phoneNumber,
    };
  }

  ProfileEditBody copyWith({
    File? avatar,
    bool clearAvatar = false,
    String? fullName,
    String? gender,
    String? phoneNumber,
  }) {
    return ProfileEditBody(
      avatar: clearAvatar ? null : avatar ?? this.avatar,
      fullName: fullName ?? this.fullName,
      gender: gender ?? this.gender,
      phoneNumber: phoneNumber ?? this.phoneNumber,
    );
  }
}
