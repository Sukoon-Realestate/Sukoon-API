part of '../../../imports.dart';

class ProfileContractsList extends StatefulWidget {
  const ProfileContractsList({super.key});
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
    asyncCall: (_, page) => ProfileContractsData.getPage(page),
    cacheKey: ProfileContractsData.cacheKey,
    cacheToJson: (contract) => contract.toJson(),
    cacheFromJson: ProfileContractContent.fromJson,
    emptyListView: const ProfileContractsEmptyState(),
    itemBuilder: (_, __, ___, contract) =>
        ProfileContractCard(key: ValueKey(contract.id), contract: contract),
  );
}
