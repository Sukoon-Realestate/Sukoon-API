enum PropertyReviewAction {
  basics(0),
  photos(1),
  pricing(2),
  submit(null);

  const PropertyReviewAction(this.page);
  final int? page;
}
