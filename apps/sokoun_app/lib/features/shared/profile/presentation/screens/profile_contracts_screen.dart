part of '../../imports.dart';

class ProfileContractsScreen extends StatelessWidget {
  const ProfileContractsScreen({
    super.key,
    this.workspace = AppWorkspace.tenant,
  });
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.profileContracts,
    body: SafeArea(child: ProfileContractsList(workspace: workspace)),
  );
}
