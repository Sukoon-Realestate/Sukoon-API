part of '../../imports.dart';

class UserProfileContent extends Equatable {
  const UserProfileContent({
    required this.id,
    required this.name,
    required this.phone,
    required this.gender,
    required this.birthDate,
    required this.avatar,
    this.city,
    this.email = '',
  });
  const UserProfileContent.initial()
    : id = '',
      name = '',
      phone = '',
      gender = '',
      birthDate = '',
      avatar = '',
      email = '',
      city = null;
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
        email: _profileString(json['email']),
        city: json['city'] is Map
            ? ProfileCity.fromJson(_profileJsonMap(json['city']))
            : null,
      );
  final String id, name, phone, gender, birthDate, avatar;
  final String email;
  final ProfileCity? city;
  UserModel toUser(UserModel fallback) =>
      fallback.copyWith(name: name, phone: phone);
  Map<String, dynamic> toJson() => {
    'id': id,
    'full_name': name,
    'phone_number': phone,
    'gender': gender,
    'birth_date': birthDate,
    'avatar': avatar,
    'email': email,
    'city': city?.toJson(),
  };
  UserProfileContent copyWith({
    String? id,
    String? name,
    String? phone,
    String? gender,
    String? birthDate,
    String? avatar,
    String? email,
    ProfileCity? city,
    bool clearCity = false,
  }) => UserProfileContent(
    id: id ?? this.id,
    name: name ?? this.name,
    phone: phone ?? this.phone,
    gender: gender ?? this.gender,
    birthDate: birthDate ?? this.birthDate,
    avatar: avatar ?? this.avatar,
    email: email ?? this.email,
    city: clearCity ? null : city ?? this.city,
  );
  @override
  List<Object?> get props => [
    id,
    name,
    phone,
    gender,
    birthDate,
    avatar,
    city,
    email,
  ];
}
