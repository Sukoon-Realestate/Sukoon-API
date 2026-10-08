/// Provider and worker readiness is independent from persistence/API support.
/// Enable each flag only after its staging operation and dependencies pass.
class FeatureServiceCapabilities {
  const FeatureServiceCapabilities({
    this.rentCheckout = false,
    this.leaseSigning = false,
    this.signedDocuments = false,
    this.analyticsExports = false,
    this.alertDelivery = false,
    this.promotionWorker = false,
  });

  static const configured = FeatureServiceCapabilities(
    rentCheckout: bool.fromEnvironment('SOKOUN_RENT_CHECKOUT'),
    leaseSigning: bool.fromEnvironment('SOKOUN_LEASE_SIGNING'),
    signedDocuments: bool.fromEnvironment('SOKOUN_SIGNED_DOCUMENTS'),
    analyticsExports: bool.fromEnvironment('SOKOUN_ANALYTICS_EXPORTS'),
    alertDelivery: bool.fromEnvironment('SOKOUN_ALERT_DELIVERY'),
    promotionWorker: bool.fromEnvironment('SOKOUN_PROMOTION_WORKER'),
  );

  final bool rentCheckout, leaseSigning, signedDocuments, analyticsExports;
  final bool alertDelivery, promotionWorker;
}
