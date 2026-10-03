part of '../../../imports.dart';

class SupportMessageBubble extends StatelessWidget {
  const SupportMessageBubble({super.key, required this.message});
  final SupportMessage message;

  Uri? _attachmentUri(SupportAttachment attachment) {
    final uri = Uri.tryParse(attachment.url);
    return uri != null &&
            ['https', 'http'].contains(uri.scheme) &&
            uri.host.isNotEmpty
        ? uri
        : null;
  }

  Future<void> _openAttachment(BuildContext context, Uri uri) async {
    bool opened = false;
    try {
      opened = await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (_) {
      // Preserve the conversation when an external viewer is unavailable.
    }
    if (!opened && context.mounted) {
      MessageUtils.showSnackBar(
        LocaleKeys.supportLinkUnavailable,
        context: context,
      );
    }
  }

  @override
  Widget build(BuildContext context) => Align(
    alignment: message.isFromUser
        ? AlignmentDirectional.centerEnd
        : AlignmentDirectional.centerStart,
    child: ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 520),
      child: Container(
        margin: EdgeInsets.only(bottom: 14.h),
        padding: EdgeInsets.all(16.r),
        decoration: BoxDecoration(
          color: message.isFromUser ? AppColors.mintLight : AppColors.white,
          borderRadius: BorderRadius.circular(16.r),
          border: Border.all(color: AppColors.sokoonBorder),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          spacing: 8.h,
          children: [
            AppText(
              message.isFromUser
                  ? LocaleKeys.supportYou
                  : LocaleKeys.supportTeam,
              style: AppTextStyles.bold12.copyWith(color: AppColors.sokoonTeal),
            ),
            SelectableText(
              message.body,
              style: AppTextStyles.regular14.copyWith(
                color: AppColors.sokoonNavy,
                height: 1.6,
              ),
            ),
            for (final attachment in message.attachments)
              if (_attachmentUri(attachment) case final Uri uri)
                TextButton.icon(
                  onPressed: () => _openAttachment(context, uri),
                  icon: const Icon(Icons.attach_file_rounded),
                  label: AppText(
                    attachment.name.isEmpty
                        ? LocaleKeys.supportAttachment
                        : attachment.name,
                    style: AppTextStyles.regular14,
                  ),
                ),
            AppText(
              supportDate(message.createdAt, context),
              style: AppTextStyles.regular12.copyWith(
                color: AppColors.sokoonGray,
              ),
            ),
          ],
        ),
      ),
    ),
  );
}
