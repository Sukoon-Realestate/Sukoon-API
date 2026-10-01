part of '../../imports.dart';

class UserProfileContent extends Equatable {
  const UserProfileContent({
    required this.id,
    required this.name,
    required this.phone,
    required this.gender,
    required this.birthDate,
    required this.avatar,
  });
  const UserProfileContent.initial()
    : id = '',
      name = '',
      phone = '',
      gender = '',
      birthDate = '',
      avatar = '';
  factory UserProfileContent.fromJson(Map<String, dynamic> json) =>
      UserProfileContent(
        id: _profileString(json['id']),
        name: _profileString(
          json['full_name'] ??
              [
                json['first_name'],
                json['last_name'],
              ].whereType<String>().join(' '),
        ),
        phone: _profileString(json['phone_number']),
        gender: _profileString(json['gender']),
        birthDate: _profileString(json['birth_date']),
        avatar: _profileString(json['avatar']),
      );
  final String id, name, phone, gender, birthDate, avatar;
  UserModel toUser(UserModel fallback) =>
      fallback.copyWith(name: name, phone: phone);
  Map<String, dynamic> toJson() => {
    'id': id,
    'full_name': name,
    'phone_number': phone,
    'gender': gender,
    'birth_date': birthDate,
    'avatar': avatar,
  };
  UserProfileContent copyWith({
    String? id,
    String? name,
    String? phone,
    String? gender,
    String? birthDate,
    String? avatar,
  }) => UserProfileContent(
    id: id ?? this.id,
    name: name ?? this.name,
    phone: phone ?? this.phone,
    gender: gender ?? this.gender,
    birthDate: birthDate ?? this.birthDate,
    avatar: avatar ?? this.avatar,
  );
  @override
  List<Object?> get props => [id, name, phone, gender, birthDate, avatar];
}
