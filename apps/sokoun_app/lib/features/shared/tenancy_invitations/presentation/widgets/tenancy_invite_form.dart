import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/feature_detail_field.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_picker.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import '../../data/models/tenancy_invitation.dart';
import '../../data/tenancy_invitation_capabilities.dart';
import '../cubits/tenancy_invitation_create_cubit.dart';
import 'tenancy_invitations_unavailable.dart';

class TenancyInviteForm extends StatefulWidget {
  const TenancyInviteForm({
    super.key,
    required this.propertyId,
    required this.propertyTitle,
    required this.tenantId,
    required this.tenantName,
    required this.property,
    required this.isFresh,
    required this.onRefresh,
  });
  final String propertyId, propertyTitle, tenantId, tenantName;
  final PropertyDetailsModel property;
  final bool isFresh;
  final Future<void> Function() onRefresh;
  @override
  State<TenancyInviteForm> createState() => _TenancyInviteFormState();
}

class _TenancyInviteFormState extends State<TenancyInviteForm> {
  final ValueNotifier<RentalSelection?> _selection = ValueNotifier(null);
  @override
  void dispose() {
    _selection.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final created = await context.read<TenancyInvitationCreateCubit>().create(
      propertyId: widget.propertyId,
      tenantId: widget.tenantId,
      selection: _selection.value,
    );
    if (!mounted) return;
    if (created != null) {
      Go.back(created);
    } else {
      await widget.onRefresh();
    }
  }

  @override
  Widget build(
    BuildContext context,
  ) => BlocBuilder<TenancyInvitationCreateCubit, AsyncState<TenancyInvitation>>(
    builder: (context, state) {
      final enabled = TenancyInvitationCapabilities.current.enabled;
      final inventory = widget.property.rentalInventory;
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 16,
        children: [
          AppText(LocaleKeys.tenancyInviteExplanation),
          Card(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: BorderSide(
                color: Theme.of(context).colorScheme.outlineVariant,
              ),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                spacing: 12,
                children: [
                  FeatureDetailField(
                    label: LocaleKeys.tenancyProperty,
                    value: widget.property.title.isNotEmpty
                        ? widget.property.title
                        : widget.propertyTitle,
                  ),
                  FeatureDetailField(
                    label: LocaleKeys.ownerVisitTenantLabel,
                    value: widget.tenantName,
                  ),
                ],
              ),
            ),
          ),
          if (!enabled) const TenancyInvitationsUnavailable(),
          if (enabled && !widget.isFresh)
            AppText(LocaleKeys.tenancyFreshRequired),
          ValueListenableBuilder<RentalSelection?>(
            valueListenable: _selection,
            builder: (context, selected, _) {
              final canChange = enabled && widget.isFresh && !state.isLoading;
              final offer = inventory?.offerById(selected?.offerId ?? '');
              final freshSelection = inventory == null || offer == null
                  ? null
                  : RentalSelection.fromOffer(
                      propertyId: widget.propertyId,
                      inventory: inventory,
                      offer: offer,
                    );
              final canSend =
                  canChange &&
                  widget.property.id == widget.propertyId &&
                  widget.tenantId.isNotEmpty &&
                  (inventory == null ||
                      (inventory.isSupported &&
                          selected?.canIdentify == true &&
                          freshSelection?.isAvailable == true &&
                          selected!.sameTermsAs(freshSelection!)));
              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                spacing: 16,
                children: [
                  if (enabled && inventory != null)
                    RentalOfferPicker(
                      propertyId: widget.propertyId,
                      inventory: inventory,
                      selectedId: selected?.offerId,
                      confirmedSelection: selected,
                      enabled: canChange,
                      onSelected: (id) {
                        final offer = inventory.offerById(id);
                        _selection.value = offer == null
                            ? null
                            : RentalSelection.fromOffer(
                                propertyId: widget.propertyId,
                                inventory: inventory,
                                offer: offer,
                              );
                      },
                    ),
                  FilledButton.icon(
                    onPressed: canSend ? _send : null,
                    icon: state.isLoading
                        ? const SizedBox.square(
                            dimension: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.send_outlined),
                    label: AppText(LocaleKeys.tenancySendInvitation),
                  ),
                ],
              );
            },
          ),
          if (state.isError && state.msg?.isNotEmpty == true)
            AppText(state.msg!),
        ],
      );
    },
  );
}
