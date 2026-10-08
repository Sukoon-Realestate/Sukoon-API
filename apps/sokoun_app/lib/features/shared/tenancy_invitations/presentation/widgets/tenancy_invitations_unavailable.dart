import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';

class TenancyInvitationsUnavailable extends StatelessWidget {
  const TenancyInvitationsUnavailable({super.key});
  @override
  Widget build(BuildContext context) => SokounContent(
    child: Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          spacing: 12,
          children: [
            Icon(
              Icons.mark_email_unread_outlined,
              color: Theme.of(context).colorScheme.primary,
              size: 36,
            ),
            AppText(
              LocaleKeys.tenancyInvitationsUnavailable,
              fontWeight: FontWeight.bold,
              textAlign: TextAlign.center,
            ),
            AppText(
              LocaleKeys.tenancyInvitationsUnavailableBody,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    ),
  );
}
