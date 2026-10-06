part of '../../imports.dart';

class ProfileContractsScreen extends StatelessWidget {
  const ProfileContractsScreen({super.key});
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.profileContracts,
    body: const SafeArea(child: ProfileContractsList()),
  );
}
