import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import '../../../data/models/premium_action_receipt.dart';

abstract final class PremiumFeedback {
  static void saved(PremiumActionReceipt receipt) => Messages.showToast(
    msg: receipt.message.isNotEmpty
        ? receipt.message
        : LocaleKeys.paidActionSaved,
  );
  static void invalid() =>
      Messages.showToast(msg: LocaleKeys.paidInvalidResponse);
  static void linkFailed() =>
      Messages.showToast(msg: LocaleKeys.paidOpenFailed);
}
