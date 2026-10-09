part of '../../../imports.dart';

class ProfileContractsList extends StatefulWidget {
  const ProfileContractsList({super.key, this.workspace = AppWorkspace.tenant});
  final AppWorkspace workspace;
  @override
  State<ProfileContractsList> createState() => _ProfileContractsListState();
}

class _ProfileContractsListState extends State<ProfileContractsList> {
  final PagifyController<ProfileContractContent> _controller =
      PagifyController<ProfileContractContent>();
  @override
  Widget build(BuildContext context) => AppPagify<ProfileContractContent>(
    pagifyController: _controller,
    enablePullRefresh: true,
    shrinkWrap: false,
    contentPadding: EdgeInsets.all(20.r),
    header: ContractsJourneyActions(workspace: widget.workspace),
    asyncCall: (_, page) => ProfileContractsData.getPage(page),
    cacheKey: ProfileContractsData.cacheKey,
    cachePolicy: ReadCachePolicy.privateMemory,
    cacheToJson: (contract) => contract.toJson(),
    cacheFromJson: ProfileContractContent.fromJson,
    emptyListView: const ProfileContractsEmptyState(),
    itemBuilder: (_, __, ___, contract) => ProfileContractCard(
      key: ValueKey(contract.id),
      contract: contract,
      workspace: widget.workspace,
    ),
  );
}
