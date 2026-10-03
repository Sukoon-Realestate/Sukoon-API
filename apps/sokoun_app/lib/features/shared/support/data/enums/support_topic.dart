import 'package:melos_core/config/language/locale_keys.g.dart';
import '../../../../main_view/data/enums/app_workspace.dart';

enum SupportTopic {
  visit,
  payment,
  verification,
  reportOwner,
  reportTenant,
  property,
  other;

  String get apiValue => switch (this) {
    reportOwner => 'report_owner',
    reportTenant => 'report_tenant',
    _ => name,
  };

  String get label => switch (this) {
    visit => LocaleKeys.supportTopicVisit,
    payment => LocaleKeys.supportTopicPayment,
    verification => LocaleKeys.identityVerification,
    reportOwner => LocaleKeys.supportTopicReportOwner,
    reportTenant => LocaleKeys.supportTopicReportTenant,
    property => LocaleKeys.supportTopicProperty,
    other => LocaleKeys.supportTopicOther,
  };

  static List<SupportTopic> forWorkspace(AppWorkspace workspace) => [
    visit,
    payment,
    verification,
    if (workspace.isOwner) reportTenant else reportOwner,
    property,
    other,
  ];
}
