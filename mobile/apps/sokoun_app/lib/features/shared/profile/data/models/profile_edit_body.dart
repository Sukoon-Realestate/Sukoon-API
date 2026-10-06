import 'dart:io';
import 'package:melos_core/core/helpers/validators.dart';

class ProfileEditBody {
  const ProfileEditBody({
    required this.avatar,
    required this.fullName,
    required this.gender,
    required this.phoneNumber,
    this.cityId,
    this.updateCity = false,
    this.updateGender = true,
  });

  const ProfileEditBody.initial()
    : avatar = null,
      fullName = '',
      gender = '',
      phoneNumber = '',
      cityId = null,
      updateCity = false,
      updateGender = true;

  final File? avatar;
  final String fullName;
  final String gender;
  final String phoneNumber;
  final String? cityId;
  final bool updateCity;
  final bool updateGender;

  Map<String, dynamic> toJson() => {
    if (avatar != null) 'avatar': avatar,
    'full_name': fullName.trim(),
    if (updateGender) 'gender': gender,
    'phone_number': Validators.normalizeEgyptianMobile(phoneNumber),
    if (updateCity) 'city_id': cityId ?? '',
  };

  Map<String, dynamic> toUserJson() {
    final List<String> names = fullName.trim().split(RegExp(r'\s+'));
    return {
      'first_name': names.first,
      'last_name': names.skip(1).join(' '),
      if (updateGender) 'gender': gender,
      'phone_number': Validators.normalizeEgyptianMobile(phoneNumber),
      if (updateCity) 'city_id': cityId ?? '',
    };
  }

  ProfileEditBody copyWith({
    File? avatar,
    bool clearAvatar = false,
    String? fullName,
    String? gender,
    String? phoneNumber,
    String? cityId,
    bool clearCity = false,
    bool? updateCity,
    bool? updateGender,
  }) {
    return ProfileEditBody(
      avatar: clearAvatar ? null : avatar ?? this.avatar,
      fullName: fullName ?? this.fullName,
      gender: gender ?? this.gender,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      cityId: clearCity ? null : cityId ?? this.cityId,
      updateCity: updateCity ?? this.updateCity,
      updateGender: updateGender ?? this.updateGender,
    );
  }
}
