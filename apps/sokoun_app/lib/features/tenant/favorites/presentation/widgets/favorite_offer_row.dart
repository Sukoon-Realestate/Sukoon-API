import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_save_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';

class FavoriteOfferRow extends StatefulWidget {
  const FavoriteOfferRow({
    super.key,
    required this.propertyId,
    required this.offer,
    this.onRemoved,
  });
  final String propertyId;
  final RentalSelection offer;
  final VoidCallback? onRemoved;
  @override
  State<FavoriteOfferRow> createState() => _FavoriteOfferRowState();
}

class _FavoriteOfferRowState extends State<FavoriteOfferRow> {
  PropertySaveCubit? _cubit;
  @override
  void initState() {
    super.initState();
    if (RentalOfferCapabilities.configured.canFavorite &&
        widget.onRemoved != null) {
      _cubit = PropertySaveCubit();
    }
  }

  @override
  void dispose() {
    _cubit?.close();
    super.dispose();
  }

  Future<void> _remove() async {
    final cubit = _cubit;
    if (cubit == null || cubit.isLoading) return;
    var failed = false;
    await cubit.unsaveProperty(
      propertyId: widget.propertyId,
      hasRentalOffers: true,
      selection: widget.offer,
      onError: (_) => failed = true,
    );
    if (mounted && !failed && cubit.state.isSuccess) widget.onRemoved?.call();
  }

  Widget _row({bool loading = false, String? error}) => Column(
    children: [
      ListTile(
        title: AppText(RentalOfferLabels.accommodation(widget.offer)),
        subtitle: AppText(
          [
            RentalOfferLabels.price(widget.offer),
            ...RentalOfferLabels.snapshotFacts(widget.offer),
            RentalOfferLabels.availability(
              widget.offer.availability,
              archived: widget.offer.archived,
            ),
          ].join('\n'),
        ),
        onTap: widget.offer.offerId.isEmpty
            ? null
            : () => Go.to(
                PropertyDetailsScreen(
                  propertyId: widget.propertyId,
                  offerId: widget.offer.offerId,
                ),
              ),
        trailing: _cubit == null
            ? null
            : IconButton(
                tooltip: LocaleKeys.favoriteRemoveSemanticLabel,
                onPressed: loading ? null : _remove,
                icon: const Icon(Icons.bookmark_remove_outlined),
              ),
      ),
      if (loading) const LinearProgressIndicator(),
      if (error != null) AppText(error),
    ],
  );
  @override
  Widget build(BuildContext context) => _cubit == null
      ? _row()
      : BlocBuilder<PropertySaveCubit, AsyncState<bool>>(
          bloc: _cubit,
          builder: (_, state) => _row(
            loading: state.isLoading,
            error: state.isError ? state.msg : null,
          ),
        );
}
