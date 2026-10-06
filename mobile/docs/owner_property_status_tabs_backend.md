# Owner property tabs: backend handoff

The mobile listings screen now has three tabs: **Under review**, **Accepted**, and **Rejected**. Each tab requests the existing endpoint with its own `status` query parameter. Backend filtering still needs to be implemented and verified on the server; this repository contains the mobile implementation.

## Endpoint

Keep `GET properties/owned/` and the existing authentication and response envelope. The mobile app sends:

```http
GET properties/owned/?status=under_review&page=1&page_size=10
GET properties/owned/?status=accepted&page=1&page_size=10
GET properties/owned/?status=rejected&page=1&page_size=10
```

| Query parameter | Contract |
| --- | --- |
| `status` | Optional for compatibility; when supplied, accept exactly `under_review`, `accepted`, or `rejected`. Filter by that property's review status. |
| `page` | Positive page number, starting at `1`. |
| `page_size` | Requested page size; the mobile app requests `10`. Return the actual size in `per_page` if the server applies a different limit. |

When `status` is omitted, preserve the existing unfiltered owner-list behavior. Return HTTP 400 with a readable validation message for an unsupported status or invalid pagination parameter.

## Filtering and pagination

1. Restrict the queryset to properties belonging to the authenticated owner.
2. Apply `status` filtering **before** counting and paginating.
3. Apply stable ordering, for example creation date descending with ID as a tie-breaker. Keep the same ordering across page requests for a tab.
4. Return `count` and `total_pages` for the **filtered** queryset, not the owner's entire collection.

`status` describes the review decision. Keep it independent of `is_verified`: a property can be accepted without being verified. If the database uses different status names, map them to the API values above consistently on input and output.

## Response

Preserve existing top-level fields and return the pagination object in `data`. The mobile data helper receives this object after the envelope is unwrapped:

```json
{
  "data": {
    "per_page": 10,
    "total_pages": 1,
    "results": [
      {
        "id": "13954644-cc37-49d9-a772-f1a88be81401",
        "title": "saudi arabia",
        "main_image": "https://res.cloudinary.com/uciefwmu/image/upload/v1791224878/properties/main_images/o9jb3ebqh90vdzdsvjyr.jpg",
        "price": "60000000.00",
        "price_period": "weekly",
        "status": "under_review",
        "is_verified": false,
        "views_count": 2,
        "visits_count": 0
      }
    ],
    "count": 1
  }
}
```

Every result must match the requested status. Keep numeric counts as integers, price as a decimal string, and IDs and media URLs stable. Preserve any existing extra listing fields; do not remove them to add filtering.

Return an empty tab as a successful response:

```json
{
  "data": {
    "per_page": 10,
    "total_pages": 1,
    "results": [],
    "count": 0
  }
}
```

The mobile app uses server-provided `per_page` and `total_pages`, starts each selected tab at page 1, and isolates cached lists by status. Do not mix statuses within a page or reuse another status's count.

## Review changes and verification

Keep review transitions consistent with the existing property-edit contract: an edit or resubmission sent for review must return `status: "under_review"` in its property response. Subsequent filtered reads must show it under review and exclude it from its previous tab. Deleted properties must be excluded from every tab and its pagination totals.

Verify all three status queries, multiple pages, empty tabs, omission of `status`, invalid parameters, owner isolation, accepted properties with `is_verified: false`, and properties moving between tabs after a review decision or resubmission. Update the shared API collection with these query parameters and real response examples once the endpoint is deployed.
