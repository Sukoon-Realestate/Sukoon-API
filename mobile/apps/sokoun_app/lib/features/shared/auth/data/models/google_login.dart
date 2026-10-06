class GoogleLoginBody {
  const GoogleLoginBody({required this.token});

  final String token;

  factory GoogleLoginBody.initial() => const GoogleLoginBody(token: '');

  GoogleLoginBody copyWith({String? token}) =>
      GoogleLoginBody(token: token ?? this.token);

  Map<String, dynamic> toJson() => {'token': token.trim()};
}
