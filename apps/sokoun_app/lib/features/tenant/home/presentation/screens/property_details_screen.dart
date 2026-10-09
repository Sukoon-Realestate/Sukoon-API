import 'dart:async';
import 'package:sokoun_app/features/shared/destinations/data/models/app_destination.dart';
import 'package:sokoun_app/features/shared/destinations/presentation/visible_destination_registry.dart';
import '../cubits/favorite_coordinator.dart';
import '../../data/models/favorite_target.dart';
import 'package:sokoun_app/features/shared/contact/presentation/widgets/visit_contact_refresh.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/models/property_cost_breakdown.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/widgets/property_cost_card.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_picker.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'package:melos_core/core/extensions/widget_extension.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_details_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_save_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/imports.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';
import 'package:sokoun_app/features/shared/chat/presentation/cubits/create_conversation_cubit.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_screen.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/widgets/property_decision_tools.dart';
import '../../data/models/property_search_model.dart';

class PropertyDetailsScreen extends StatefulWidget {
  const PropertyDetailsScreen({
    super.key,
    required this.propertyId,
    this.searchPreferences,
    this.offerId,
    this.confirmedSelection,
  });

  final String propertyId;
  final String? offerId;

  /// Passed only when returning from a user's explicit confirmation/sign-in.
  final RentalSelection? confirmedSelection;

  final PropertySearchFilters? searchPreferences;

  @override
  State<PropertyDetailsScreen> createState() => _PropertyDetailsScreenState();
}

class _PropertyDetailsScreenState extends State<PropertyDetailsScreen> {
  ModalRoute<dynamic>? _route;
  VoidCallback? _unbindDestination;
  StreamSubscription<Map<FavoriteTarget, FavoriteState>>? _favorites;
  late final PropertyDetailsCubit _detailsCubit;
  late final PropertySaveCubit _saveCubit;
  late final CreateConversationCubit _conversationCubit;
  late final Future<void> _detailsRequest;
  late final ValueNotifier<({String? id, RentalSelection? confirmed})>
  _selectedOffer = ValueNotifier((
    id: widget.offerId,
    confirmed: widget.confirmedSelection,
  ));
  final ValueNotifier<({bool? savedOverride, bool isUpdating})> _savedState =
      ValueNotifier<({bool? savedOverride, bool isUpdating})>((
        savedOverride: null,
        isUpdating: false,
      ));

  @override
  void initState() {
    super.initState();
    _detailsCubit = PropertyDetailsCubit();
    _saveCubit = PropertySaveCubit();
    _conversationCubit = CreateConversationCubit();
    _favorites = FavoriteCoordinator.instance.stream.listen((_) {
      if (!mounted) return;
      final state = FavoriteCoordinator.instance.value(
        FavoriteTarget(widget.propertyId, _selectedOffer.value.id),
      );
      _savedState.value = (savedOverride: state?.desired, isUpdating: false);
    });
    _detailsRequest = _detailsCubit.getPropertyDetails(widget.propertyId);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final route = ModalRoute.of(context);
    if (route == _route) return;
    _unbindDestination?.call();
    _route = route;
    if (route != null) {
      _unbindDestination = VisibleDestinationRegistry.bind(
        route,
        () => AppDestination(
          kind: DestinationKind.property,
          id: widget.propertyId,
          offerId: _selectedOffer.value.id,
          workspace: AppWorkspace.tenant,
        ),
      );
    }
  }

  @override
  void dispose() {
    _unbindDestination?.call();
    _favorites?.cancel();
    _detailsCubit.close();
    _saveCubit.close();
    _conversationCubit.close();
    _savedState.dispose();
    _selectedOffer.dispose();
    super.dispose();
  }

  Future<void> _toggleSaved(TenantPropertyDetailsContent property) async {
    if (property.hasRentalOffers &&
        (!property.selectionConfirmed ||
            property.selection == null ||
            !RentalOfferCapabilities.configured.canFavorite)) {
      Messages.showToast(
        msg: !property.selectionConfirmed || property.selection == null
            ? LocaleKeys.rentalConfirmAccommodation
            : LocaleKeys.rentalUnavailableCapability,
      );
      return;
    }
    if (!WorkspaceNavigation.isAuthenticated) {
      final choice = _selectedOffer.value;
      await WorkspaceNavigation.open(
        workspace: AppWorkspace.tenant,
        showLoginSheet: true,
        detail: () => Go.to(
          PropertyDetailsScreen(
            propertyId: widget.propertyId,
            offerId: choice.id,
            confirmedSelection: choice.confirmed,
            searchPreferences: widget.searchPreferences,
          ),
        ),
      );
      return;
    }

    final target = FavoriteTarget(
      property.id.isEmpty ? widget.propertyId : property.id,
      property.selection?.offerId,
    );
    FavoriteCoordinator.instance.seed(target, property.isSaved);
    final bool currentValue =
        FavoriteCoordinator.instance.value(target)?.desired ?? property.isSaved;
    final bool nextValue = !currentValue;
    final String propertyId = property.id.isEmpty
        ? widget.propertyId
        : property.id;

    _savedState.value = (savedOverride: nextValue, isUpdating: false);

    void rollbackSavedState(String _) {
      if (!mounted) return;
      _savedState.value = (
        savedOverride:
            FavoriteCoordinator.instance.value(target)?.desired ?? currentValue,
        isUpdating: _savedState.value.isUpdating,
      );
    }

    if (nextValue) {
      await _saveCubit.saveProperty(
        propertyId: propertyId,
        selection: property.selection,
        hasRentalOffers: property.hasRentalOffers,
        onError: rollbackSavedState,
      );
    } else {
      await _saveCubit.unsaveProperty(
        propertyId: propertyId,
        selection: property.selection,
        hasRentalOffers: property.hasRentalOffers,
        onError: rollbackSavedState,
      );
    }
    if (!mounted) return;
    if (_saveCubit.state.isSuccess && property.selection != null) {
      final current = _detailsCubit.data;
      final inventory = current.rentalInventory;
      if (inventory != null) {
        _detailsCubit.updateData(
          current.copyWith(
            rentalInventory: inventory.copyWith(
              offers: [
                for (final offer in inventory.offers)
                  offer.id == property.selection!.offerId
                      ? offer.copyWith(
                          isSaved:
                              FavoriteCoordinator.instance
                                  .value(target)
                                  ?.desired ??
                              nextValue,
                        )
                      : offer,
              ],
            ),
          ),
        );
      }
    }
    _savedState.value = (
      savedOverride: _savedState.value.savedOverride,
      isUpdating: false,
    );
  }

  Widget _buildDetails(PropertyDetailsModel data) =>
      ValueListenableBuilder<({String? id, RentalSelection? confirmed})>(
        valueListenable: _selectedOffer,
        builder: (_, choice, _) => Column(
          children: [
            if (_detailsCubit.state.fromCache)
              Padding(
                padding: const EdgeInsets.all(8),
                child: Semantics(
                  liveRegion: true,
                  child: AppText(LocaleKeys.professionalSavedData),
                ),
              ),
            Expanded(child: _buildSelectedDetails(data, choice)),
          ],
        ),
      );

  Widget _buildSelectedDetails(
    PropertyDetailsModel data,
    ({String? id, RentalSelection? confirmed}) choice,
  ) {
    final selectedId = choice.id;
    final inventory = data.rentalInventory;
    final offer = inventory?.offerById(selectedId ?? '');
    final selection = offer != null && inventory?.isSupported == true
        ? RentalSelection.fromOffer(
            propertyId: data.id,
            inventory: inventory!,
            offer: offer,
          )
        : selectedId == null
        ? null
        : RentalSelection(propertyId: data.id, offerId: selectedId);
    final TenantPropertyDetailsContent property =
        TenantPropertyDetailsContent.fromModel(
          data,
          selection: selection,
          selectionConfirmed:
              choice.confirmed != null &&
              selection != null &&
              selection.sameTermsAs(choice.confirmed!),
        );
    return TenantPropertyDetailsBody.withActions(
      property: property,
      offerPicker: inventory == null
          ? property.hasRentalOffers
                ? AppText(LocaleKeys.rentalIncompatibleResponse)
                : null
          : ValueListenableBuilder<({bool? savedOverride, bool isUpdating})>(
              valueListenable: _savedState,
              builder: (_, state, _) => RentalOfferPicker(
                propertyId: data.id,
                inventory: inventory,
                selectedId: selectedId,
                confirmedSelection: choice.confirmed,
                contextScope: widget.searchPreferences?.rentalScope ?? '',
                contextPricePeriod: widget.searchPreferences?.pricePeriod ?? '',
                enabled: !state.isUpdating,
                onSelected: (id) {
                  _selectedOffer.value = (id: id, confirmed: null);
                  _savedState.value = (savedOverride: null, isUpdating: false);
                },
                onConfirmed: (selected) => _selectedOffer.value = (
                  id: selected.offerId,
                  confirmed: selected,
                ),
              ),
            ),
      decisionTools: property.hasRentalOffers
          ? selection == null || !selection.canIdentify
                ? null
                : PropertyCostCard(
                    cost: PropertyCostBreakdown.fromProperty(
                      data,
                      selection: selection,
                    ),
                    periodLabel: property.pricePeriodLabel,
                  )
          : PropertyDecisionTools(
              key: ValueKey(data.id),
              property: data,
              searchPreferences: widget.searchPreferences,
            ),
      bottomActions:
          BlocSelector<
            CreateConversationCubit,
            AsyncState<ConversationContent>,
            bool
          >(
            selector: (state) => state.isLoading,
            builder: (context, isOpeningChat) =>
                ValueListenableBuilder<
                  ({bool? savedOverride, bool isUpdating})
                >(
                  valueListenable: _savedState,
                  builder: (context, savedState, _) =>
                      TenantPropertyBottomActions(
                        property: property,
                        isSaved:
                            FavoriteCoordinator.instance
                                .value(
                                  FavoriteTarget(
                                    property.id,
                                    property.selection?.offerId,
                                  ),
                                )
                                ?.desired ??
                            property.isSaved,
                        onSavedPressed:
                            property.hasRentalOffers &&
                                (!property.selectionConfirmed ||
                                    selection?.canIdentify != true ||
                                    inventory?.isSupported != true ||
                                    !RentalOfferCapabilities
                                        .configured
                                        .canFavorite)
                            ? null
                            : () => _toggleSaved(property),
                        isOpeningChat: isOpeningChat,
                        onChatPressed:
                            property.ownerId.isEmpty ||
                                property.ownerId == UserModel.currentUser?.id ||
                                (property.hasRentalOffers &&
                                    (!property.selectionConfirmed ||
                                        selection?.isAvailable != true))
                            ? null
                            : () => _openChat(property),
                      ),
                ),
          ),
    );
  }

  Future<void> _openChat(TenantPropertyDetailsContent property) async {
    if (!WorkspaceNavigation.isAuthenticated) {
      final choice = _selectedOffer.value;
      await WorkspaceNavigation.open(
        workspace: AppWorkspace.tenant,
        showLoginSheet: true,
        detail: () => Go.to(
          PropertyDetailsScreen(
            propertyId: widget.propertyId,
            offerId: choice.id,
            confirmedSelection: choice.confirmed,
            searchPreferences: widget.searchPreferences,
          ),
        ),
      );
      return;
    }
    await _conversationCubit.createOrGet(
      userId: property.ownerId,
      onSuccess: (conversation) => Go.to(
        ChatScreen(
          conversation: conversation,
          rentalContext: property.selection,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: LocaleKeys.tenantFilterPropertyDetails,
      showBackButton: true,
      backgroundColor: context.appColor(
        AppColors.scaffoldBackground,
        surface: true,
      ),
      contentWidth: SokounContentWidth.wide,
      body: VisitContactRefresh(
        propertyId: widget.propertyId,
        refreshOnReturn: true,
        onRefresh: () => _detailsCubit.refresh(widget.propertyId),
        child: SafeArea(
          bottom: false,
          child: MultiBlocProvider(
            providers: [
              BlocProvider<PropertyDetailsCubit>.value(value: _detailsCubit),
              BlocProvider<CreateConversationCubit>.value(
                value: _conversationCubit,
              ),
            ],
            child: FutureBuilder<void>(
              future: _detailsRequest,
              builder: (context, snapshot) =>
                  StatusBuilder<
                        PropertyDetailsCubit,
                        PropertyDetailsModel
                      >.withShimmer(
                        initialDataForShimmer:
                            const PropertyDetailsModel.initial(),
                        onRetry: () =>
                            _detailsCubit.getPropertyDetails(widget.propertyId),
                        builder: _buildDetails,
                      )
                      .withPullRefresher(
                        onRefresh: () =>
                            _detailsCubit.getPropertyDetails(widget.propertyId),
                      ),
            ),
          ),
        ),
      ),
    );
  }
}
