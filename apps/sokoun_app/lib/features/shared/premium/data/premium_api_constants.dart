/// Implemented contracts in MOBILE_ALL_FEATURES_BACKEND_HANDOFF.md.
abstract final class PremiumApiConstants {
  static const prefix = 'features/v1/';
  static const configuration = '${prefix}configuration/';
  static const campaigns = '${prefix}boost-campaigns/';
  static const alerts = '${prefix}search-alerts/';
  static const leases = '${prefix}leases/';
  static const leaseTenants = '${prefix}lease-tenants/';
  static const leaseConfiguration = '${prefix}lease-configuration/';
  static const invoices = '${prefix}rent-invoices/';
  static String alert(String id) => '$alerts${Uri.encodeComponent(id)}/';
  static String analytics(String propertyId) =>
      '${prefix}owner-analytics/${Uri.encodeComponent(propertyId)}/';
  static const aiSuggestions = '${prefix}listing-suggestions/';
  static String lease(String id) => '$leases${Uri.encodeComponent(id)}/';
  static String signing(String id) => '${lease(id)}signing-session/';
  static String cancelLease(String id) => '${lease(id)}cancel/';
  static String invoice(String id) => '$invoices${Uri.encodeComponent(id)}/';
  static String rentCheckout(String id) => '${invoice(id)}checkout/';
}
