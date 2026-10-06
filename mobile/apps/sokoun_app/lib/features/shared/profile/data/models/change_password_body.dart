class ChangePasswordBody {
  const ChangePasswordBody({
    required this.currentPassword,
    required this.newPassword,
    required this.confirmation,
  });
  const ChangePasswordBody.initial()
    : currentPassword = '',
      newPassword = '',
      confirmation = '';
  final String currentPassword;
  final String newPassword;
  final String confirmation;
  Map<String, dynamic> toJson() => {
    'current_password': currentPassword,
    'new_password': newPassword,
    're_new_password': confirmation,
  };
  ChangePasswordBody copyWith({
    String? currentPassword,
    String? newPassword,
    String? confirmation,
  }) => ChangePasswordBody(
    currentPassword: currentPassword ?? this.currentPassword,
    newPassword: newPassword ?? this.newPassword,
    confirmation: confirmation ?? this.confirmation,
  );
}
