part of '../../imports.dart';

class TenantEditProfileScreen extends StatelessWidget {
  const TenantEditProfileScreen({super.key, required this.initialValue});

  final UserModel initialValue;

  @override
  Widget build(BuildContext context) {
    return ProfileEditView(
      initialValue: initialValue,
      userType: UserType.tenant,
    );
  }
}
