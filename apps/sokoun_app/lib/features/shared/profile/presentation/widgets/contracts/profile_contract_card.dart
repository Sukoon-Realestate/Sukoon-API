part of '../../../imports.dart';

class ProfileContractCard extends StatelessWidget {
  const ProfileContractCard({
    super.key,
    required this.contract,
    this.workspace = AppWorkspace.tenant,
  });
  final ProfileContractContent contract;
  final AppWorkspace workspace;
  Uri? get _document {
    final Uri? uri = Uri.tryParse(contract.documentUrl);
    return uri != null &&
            ['https', 'http'].contains(uri.scheme) &&
            uri.host.isNotEmpty
        ? uri
        : null;
  }

  Future<void> _openDocument(BuildContext context) async {
    final uri = _document;
    if (uri == null) return;
    bool opened = false;
    try {
      opened = await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (_) {
      // Keep the contracts list available if no document viewer is installed.
    }
    if (!opened && context.mounted) {
      Messages.showToast(
        msg: LocaleKeys.supportLinkUnavailable,
        status: BaseStatus.error,
      );
    }
  }

  @override
  Widget build(BuildContext context) => ProfileSurfaceCard(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 12.h,
      children: [
        AppText(
          contract.propertyTitle,
          style: AppTextStyles.bold16.copyWith(
            color: context.appColor(AppColors.sokoonNavy),
          ),
        ),
        AppText(
          switch (contract.status) {
            'active' => LocaleKeys.profileContractActive,
            'expired' => LocaleKeys.profileContractExpired,
            'cancelled' => LocaleKeys.profileContractCancelled,
            _ => LocaleKeys.profileContractUnknown,
          },
          style: AppTextStyles.regular14.copyWith(
            color: context.appColor(AppColors.sokoonGray),
          ),
        ),
        if (contract.startDate.isNotEmpty)
          AppText(
            '${LocaleKeys.profileContractStart}: ${profileDate(contract.startDate, context)}',
            style: AppTextStyles.regular14,
          ),
        if (contract.endDate.isNotEmpty)
          AppText(
            '${LocaleKeys.profileContractEnd}: ${profileDate(contract.endDate, context)}',
            style: AppTextStyles.regular14,
          ),
        if (_document != null)
          OutlinedButton.icon(
            icon: const Icon(Icons.description_outlined),
            label: AppText(
              LocaleKeys.profileContractDocument,
              style: AppTextStyles.bold14,
            ),
            onPressed: () => _openDocument(context),
          ),
        if (contract.leaseId.isNotEmpty)
          ContractLeaseEntry(leaseId: contract.leaseId, workspace: workspace),
      ],
    ),
  ).paddingOnly(bottom: 12);
}
