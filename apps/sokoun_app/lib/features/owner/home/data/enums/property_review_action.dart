enum PropertyReviewAction {
  basics(0),
  photos(1),
  video(2),
  pricing(3),
  details(4),
  submit(null);

  const PropertyReviewAction(this.page);
  final int? page;
}
