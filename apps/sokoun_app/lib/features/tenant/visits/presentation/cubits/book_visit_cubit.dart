part of '../../imports.dart';

class BookVisitCubit extends VerifiedActionCubit<Map<String, dynamic>> {
  BookVisitCubit({this.capabilities = RentalOfferCapabilities.configured})
    : super(const {});
  final RentalOfferCapabilities capabilities;
  bool _validating = false;

  Future<void> bookVisit({
    required String propertyId,
    String ownerId = '',
    RentalSelection? selection,
    bool hasRentalOffers = false,
    required String visitDate,
    required int visitHour,
    required int visitMinute,
    required String note,
    required void Function() onSuccess,
    void Function(String message)? onError,
  }) async {
    if (isLoading || isClosed || _validating) return;
    if (!checkVerification(onError: onError)) return;
    if ((hasRentalOffers || selection != null) &&
        (!capabilities.canRequestViewing ||
            selection?.canIdentify != true ||
            selection?.propertyId != propertyId)) {
      setError(errorMessage: LocaleKeys.rentalUnavailableCapability);
      onError?.call(LocaleKeys.rentalUnavailableCapability);
      return;
    }
    if (selection != null) {
      _validating = true;
      try {
        final fresh = await RentalOfferReadData(
          baseCrudUseCase,
        ).freshSelection(selection);
        if (!selection.sameTermsAs(fresh)) {
          throw StateError(LocaleKeys.rentalTermsChanged);
        }
      } catch (error) {
        if (!isClosed) {
          final message = error is StateError
              ? error.message
              : error.toString();
          setError(errorMessage: message);
          onError?.call(message);
        }
        return;
      } finally {
        _validating = false;
      }
      if (isClosed || !checkVerification(onError: onError)) return;
    }
    if (ownerId.isNotEmpty && ownerId == UserModel.currentUser?.id) {
      setError(errorMessage: LocaleKeys.workspaceSelfActionBlocked);
      onError?.call(LocaleKeys.workspaceSelfActionBlocked);
      return;
    }
    if (!VisitScheduleRules.isFuture(
      visitDate,
      BookVisitBody.formatApiTime(hour: visitHour, minute: visitMinute),
    )) {
      setError(errorMessage: LocaleKeys.freeVisitPastTime);
      onError?.call(LocaleKeys.freeVisitPastTime);
      return;
    }
    final BookVisitBody body = BookVisitBody.fromTime(
      selection: selection,
      visitDate: visitDate,
      hour: visitHour,
      minute: visitMinute,
      note: note,
    );
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<Map<String, dynamic>>(
          api: ApiConstants.propertyVisits(propertyId),
          httpRequestType: HttpRequestType.post,
          body: body.toJson(capabilities: capabilities),
          mapper: (json) {
            if (selection != null &&
                (json is! Map ||
                    json['offer_id']?.toString() != selection.offerId)) {
              throw FormatException(LocaleKeys.rentalIncompatibleResponse);
            }
            return json is Map<String, dynamic> ? json : <String, dynamic>{};
          },
        ),
      ),
      onSuccess: (_) {
        WorkspaceCountsRefreshBus.refresh();
        onSuccess();
      },
      onError: onError,
    );
  }

  static bool isUnavailableSlotError(String message) {
    final String normalized = message.toLowerCase();
    return normalized.contains('already booked') ||
        normalized.contains('not available');
  }
}
