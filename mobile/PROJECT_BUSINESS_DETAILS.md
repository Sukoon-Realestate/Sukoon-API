# Sokoun — Project Business Details

**Reviewed:** 6 October 2026

**Scope:** The mobile application, marketing website, shared business rules, API collections and handoffs, and exported design prototype in this repository.

**Purpose:** A business reference for product, operations, design, development, and stakeholder discussions.

## Contents

1. [How to read this document](#1-how-to-read-this-document)
2. [Product and business model](#2-product-and-business-model)
3. [People, accounts, and access](#3-people-accounts-and-access)
4. [Main customer journeys](#4-main-customer-journeys)
5. [Registration, authentication, and identity verification](#5-registration-authentication-and-identity-verification)
6. [Property inventory and listing lifecycle](#6-property-inventory-and-listing-lifecycle)
7. [Tenant discovery, property details, and saved properties](#7-tenant-discovery-property-details-and-saved-properties)
8. [Viewing requests and reviews](#8-viewing-requests-and-reviews)
9. [Owner operations, availability, analytics, and revenue](#9-owner-operations-availability-analytics-and-revenue)
10. [Messaging and communication](#10-messaging-and-communication)
11. [Notifications and engagement](#11-notifications-and-engagement)
12. [Profiles, preferences, legal pages, and account closure](#12-profiles-preferences-legal-pages-and-account-closure)
13. [Contracts and customer support](#13-contracts-and-customer-support)
14. [Administration and operational design](#14-administration-and-operational-design)
15. [Marketing, distribution, and user experience](#15-marketing-distribution-and-user-experience)
16. [Business data and service responsibilities](#16-business-data-and-service-responsibilities)
17. [Service and API inventory](#17-service-and-api-inventory)
18. [Implementation gaps and unresolved business decisions](#18-implementation-gaps-and-unresolved-business-decisions)
19. [Evidence and source index](#19-evidence-and-source-index)

## 1. How to read this document

This document describes the business represented by the checked-out project. It does not establish whether a production backend, store release, or operational team is live.

| Evidence label | Meaning |
| --- | --- |
| **Implemented in the client** | An actual mobile or website flow and its behavior exist in source. A network-dependent feature still requires a compatible service. |
| **Documented backend contract** | A repository handoff specifies server behavior. Deployment and enforcement have not been independently verified. |
| **Proposed service** | Client screens exist, but the accompanying handoff explicitly says the service awaits backend implementation or confirmation. |
| **Design only** | The exported prototype illustrates the idea with sample data or inactive controls. This is design intent, not a live service or an approved delivery commitment. |
| **Unspecified** | The repository does not settle the policy, commercial term, or operational behavior. |

For current behavior, reachable application code is stronger evidence than an unused widget, enum, API constant, or sample screen. For property media and editing, the returned [5 October property handoff](MOBILE_PROPERTY_MEDIA_EDITING_DELETION_HANDOFF.md) supersedes the older proposal retained in [the original backend notes](docs/property_media_edit_delete_backend.md). Conflicting policies are called out rather than silently combined.

The review covers static source, configuration, translations, design exports, existing test definitions, and business-facing handoffs. It did not run production transactions, interview stakeholders, verify deployed APIs, or establish legal or financial terms. No example credentials or personal records from API samples are reproduced here.

## 2. Product and business model

### 2.1 Product identity and repository scope

The product is **Sokoun / سكون**, a rental-property platform connecting people looking for accommodation with people offering properties. Files also use **Sokoon** and **Sukoon**; these are naming variations within the same project. The workspace directory is named `darak-app`.

| Project area | Business purpose | Current evidence |
| --- | --- | --- |
| `apps/sokoun_app` | Customer application for tenant and owner activity | Flutter application with shared account, discovery, listings, viewing requests, chat, and account services |
| `apps/landing_page` | Explain the product and attract prospective tenants and owners | Arabic/English Flutter web marketing page; sample inventory and coming-soon store badges |
| `packages/core` | Shared language, identity, validation, networking, and reusable app services | Shared package; also contains legacy utilities unrelated to the current rental experience |
| `Sokoon Figma Prototype Design` | Visual storyboard for customer flows and an administrative console | React/Vite design export with sample data; not evidence of an operational admin system |
| Root API collection and `docs` | Coordinate mobile/backend business contracts | Request examples, integration notes, proposed services, and explicit unresolved requirements |

Backend implementation source is not included in this repository. The presence of an endpoint in a collection does not prove it is deployed.

### 2.2 Core business proposition

The main product loop is:

**Owner supplies a detailed listing → platform reviews it → tenant discovers and evaluates it → tenant requests a viewing or contacts the owner → owner responds → both manage the viewing → tenant can provide a review.**

| Audience | Problem addressed | Product value represented in the app |
| --- | --- | --- |
| Tenant | Finding relevant rentals and understanding them before visiting | Search and filters, photos and video, rental terms, favorites, owner communication, viewing tracking, reviews |
| Owner | Presenting properties and organizing incoming interest | Structured listing creation, review status, request decisions, calendar and availability, conversations, performance metrics |
| Platform operations | Maintaining trustworthy inventory and handling account or service issues | Identity documents, ownership evidence, moderation contracts, reporting/support concepts, and administrative designs |

The source supports a **rental discovery and viewing marketplace**. A viewing request is an appointment request; it does not itself reserve occupancy, create a lease, or collect rent.

### 2.3 Market, pricing units, and customer segments

- **Market orientation:** Egypt. Current phone and national-ID validation are Egyptian, property creation defaults to Egypt, geography uses governorates and cities, and the active money formatter uses Egyptian pounds.
- **Languages:** Arabic is the initial and fallback language; English is supported. Arabic uses right-to-left layout.
- **Currency:** Current customer-facing property prices and owner revenue amounts are formatted in **EGP**. Older example data or currency fields do not establish multi-currency support.
- **Rental price periods:** Daily, weekly, monthly, and yearly are represented. These describe the quoted rent unit.
- **Minimum rental term:** A separate field stores the minimum rental period in months. This must not be confused with the rent price period or a viewing date.
- **Tenant suitability:** All tenants, families, singles, students, and female students are represented as listing preferences.
- **Property types:** The current model recognizes apartment, room, duplex, villa, floor, roof, and studio labels. Backend-provided types and filter options determine the actual selectable catalog.

Actual launch cities, geographic coverage, property supply, customer acquisition targets, and market size are unspecified. A sample Cairo listing is not evidence of an approved launch boundary.

### 2.4 Monetization and financial scope

The repository does **not** establish an approved platform monetization policy.

| Financial subject | What is represented | What remains unconfirmed |
| --- | --- | --- |
| Rent | Listing price and rent period; owner revenue summaries and transaction rows | Whether rent is collected by Sokoun, imported from another system, or merely reported |
| Security deposit | Informational listing term, including preset periods or a numeric amount | Collection, escrow, release, deductions, or refund workflow |
| Platform commission | Sample admin finance data | Actual rate, payer, charge event, fee basis, tax treatment, and settlement |
| Verification fee | A sample KYC-fee transaction in the prototype | Any real verification charge or payment requirement |
| Refunds | Admin storyboard and sample transaction concepts | Executable refund service, rules, approvals, and funding source |
| Paid promotion | Some notification kinds refer to visibility/bump events | A purchasable promotion product, price, entitlement, or ranking rule |

The admin prototype includes examples such as a **5% platform fee** and a **50 EGP KYC fee**. These are mock values and must not be used as actual commercial terms. The active mobile app has no complete checkout, payment-gateway, rent-collection, owner-payout, subscription-purchase, or refund flow. Legacy wallet/package endpoints in the shared core do not establish such features for Sokoun.

Sources: [Workspace definition](pubspec.yaml), [mobile package](apps/sokoun_app/pubspec.yaml), [EGP formatter](apps/sokoun_app/lib/features/shared/finance/data/egyptian_pound.dart), [landing-page scope](apps/landing_page/README.md), [admin prototype](<Sokoon Figma Prototype Design/src/app/screens-admin.tsx>).

## 3. People, accounts, and access

### 3.1 Business actors

| Actor | Supported responsibilities and access |
| --- | --- |
| Guest | Browse tenant Home and public property discovery/details; authenticate before protected personal actions |
| Signed-in tenant | Maintain a shortlist, request viewings, manage their own requests, communicate, review eligible visits, manage identity and support |
| Signed-in owner | Create/manage their own listings, review incoming requests, maintain availability, inspect analytics/revenue, communicate, manage identity and support |
| Reviewer/administrator | Intended identity review, listing moderation, customer support, enforcement, and operational monitoring; administrative implementation is design only here |
| Backend services | Establish authenticated identity, enforce permissions and state transitions, persist records, protect private files, and provide accurate counts/notifications |

### 3.2 One account, two workspaces

Tenant and owner are **workspaces on the same authenticated account**. A person can switch between them without registering a second identity. Registration does not submit a tenant/owner role as an authorization grant.

| Workspace | Main navigation |
| --- | --- |
| Tenant | Home, Saved, Messages, Visits, Profile |
| Owner | Home, Properties, Messages, Requests, Profile |

Workspace selection is remembered per account and defaults to tenant. The profile identity, identity verification, settings, and chat belong to the shared account; listings, visits, and displayed operational metrics depend on the selected workspace.

Workspace selection changes the interface. It must not allow one user to edit another user's listing or read another user's ticket. A legacy account-type field is retained for compatibility, not used as a complete permission system.

### 3.3 Authentication gates and self-service restrictions

- Guest access is centered on tenant Home. Other main tabs require authentication; switching a guest into owner activity also requires authentication.
- Protected actions open login/create-account access. After successful authentication, the pending workspace, tab, or detail destination can resume. Canceling authentication clears that pending destination.
- Leaving forms with changes uses draft/leave protection where implemented. This is not evidence of a durable draft store across app restarts.
- The app prevents creating a conversation with oneself. Booking one's own property is blocked when the listing's owner ID is available.
- An owner opening their own property sees a management action instead of the ordinary tenant booking/contact action.
- Account changes and session expiry reset account-scoped state to avoid carrying one person's activity into another account.

Sources: [Workspace navigation](apps/sokoun_app/lib/features/main_view/presentation/workspace_navigation.dart), [tab definitions](apps/sokoun_app/lib/features/main_view/presentation/models/home_tab.dart), [workspace preferences](apps/sokoun_app/lib/features/main_view/data/workspace_preferences.dart).

## 4. Main customer journeys

### 4.1 Tenant journey

1. Open the app and browse Home, search, or use an area derived from current location.
2. Narrow results by rent, type, suitability, rooms, furnishing, verification, smoking preference, and amenities.
3. Inspect a property's description, photos/video, location, rental terms, owner information, and reviews.
4. Sign in when saving a property, starting protected communication, or requesting a viewing.
5. Optionally submit identity details/documents; check the actual review status rather than assuming upload means approval.
6. Submit a viewing request with a date, time, and optional note. The request awaits the owner's response.
7. Follow its status in Visits and notifications. Use the actions allowed by the service, including cancellation, contact, or finding an alternative.
8. Submit a visit-linked review when permitted. Use Profile/Support for account, contract, or service questions.

The product copy positions verification as a trust requirement for chat and booking. Enforcement is inconsistent in the current client; [section 5.4](#54-verification-policy-and-current-enforcement) explains the gap.

### 4.2 Owner journey

1. Sign in and switch to owner workspace using the same account.
2. Review the dashboard's listings, pending requests, weekly visits, and rating.
3. Add a property with its location, structural details, media, rental terms, and optional ownership evidence.
4. Submit for review and follow the Under review / Accepted / Rejected tabs.
5. Edit and resubmit when necessary; edits return to review under the documented contract.
6. Inspect incoming viewing requests and tenant information, then accept or reject eligible requests.
7. Use request-linked calendar/availability and conversations to organize viewings.
8. Review property performance, account reviews, and server-provided revenue information.
9. Use shared Profile, Settings, identity verification, and owner-context support.

### 4.3 Operational journey represented by contracts and designs

An operational team would review identity documents and property submissions, make approval/rejection decisions, respond to tickets, investigate complaints, enforce policies, and inspect audit or financial information. The customer app consumes some results of these activities, but the operational console itself is a prototype in this repository.

## 5. Registration, authentication, and identity verification

### 5.1 Account creation and login

| Flow | Business behavior in the client |
| --- | --- |
| Welcome | Entry to login or account creation |
| Registration | First name, last name, email, optional phone, password, and confirmation; no new owner account is required later |
| Email verification | Six-digit numeric OTP sent to the registration email; successful verification returns to Login |
| Password login | Email/password login followed by a current-user lookup to establish the account |
| Google login | Implemented Google authentication handoff to the backend |
| Forgot password | Submit email, show the email-sent result, resend or change the address; the reset-link completion is handled outside the mobile flow |
| Guest browsing | Continue from Login to tenant Home |

Facebook and Apple login buttons/services are not active completed sign-in options in the current screen. Their existence in shared files should not be advertised as supported authentication. A complete two-factor login challenge is also absent.

Current client validation and timers:

| Input or rule | Current rule |
| --- | --- |
| Registration names | Required; up to 50 characters each; Unicode letters/marks, spaces, apostrophes, and hyphens supported |
| Email | Trimmed/lowercased; format and length validation, including total maximum 254 characters |
| Phone | Optional at registration; if supplied, Egyptian mobile format after removing formatting characters |
| Egyptian mobile format | `010`, `011`, `012`, or `015` followed by eight digits, or the corresponding `+20` international form with the leading domestic zero removed |
| New password | At least eight characters; confirmation must match; password text is not trimmed |
| Login password | Required but not forced through the new-password minimum, allowing existing credentials to reach the server |
| OTP | Exactly six numeric digits; screen describes ten-minute validity |
| OTP resend | One-minute client cooldown; reset begins after successful resend |

OTP validity, credential policy, throttling, and recovery-token expiry remain server responsibilities. Client timers do not establish server security or delivery guarantees.

### 5.2 Identity document submission

Identity verification is separate from email verification and login. The document flow can update an existing authenticated account through `auth/complete-register/`.

The represented identity package contains:

- Egyptian national ID number.
- Front of the identity card.
- Back of the identity card.
- Selfie.

The national ID, when provided, must contain exactly **14 digits**. This is format validation; the mobile app does not prove that the ID is authentic or belongs to the uploader.

Selected identity images are validated as actual decodable JPEG, PNG, or WebP files, with a **10 MiB per-file limit**. Identity-document submission does not allow GIF. Omitted document fields preserve existing submissions under the intended partial-update contract.

The client allows partial document updates. The backend returns `registration_complete`, `verification_status`, and `missing_fields` to determine completeness and the next state. A completed submission can proceed to a pending-review result; it does not establish approved identity. Required-document policy ultimately belongs to the backend.

### 5.3 Identity states

The proposed shared verification-summary service uses the following states:

| State | Meaning and customer action |
| --- | --- |
| Incomplete | Required identity information is missing; upload/continue verification |
| Pending | Documents are awaiting a decision; refresh status, without a new submission action in this summary |
| Approved | Identity review has succeeded; display the server result |
| Rejected | Review failed; show the server's rejection reason and allow correction/reupload |

The summary must agree with tenant/owner profile flags and reviewer decisions. It should not expose document URLs. The status screen is implemented, while `profiles/verification-status/` is explicitly a **proposed service**.

No guaranteed identity-review turnaround is established. A displayed review estimate supplied by a service is not a repository-wide SLA. Promotional copy about priority booking does not establish an implemented priority queue.

### 5.4 Verification policy and current enforcement

There are several independent trust signals:

| Signal | What it describes |
| --- | --- |
| Email verification | Control of the registration email |
| Account identity verification | Review of the person's identity submission |
| Listing review status | A property's moderation decision |
| Property `is_verified` | A separate verification flag on the listing |
| Ownership verification | Review of the property's private ownership proof |

These must not be collapsed into one “verified” state.

Current inconsistencies are material to the business:

- Inbox/search opening uses `conversation.isVerified` to choose normal or restricted chat. The restricted screen directs users to verification.
- Property-based conversation creation and viewing submission primarily enforce authentication and self-action restrictions; they do not consistently check the current account's KYC approval.
- A conversation's verification field can reflect participant data, so it is not a reliable universal substitute for the signed-in user's identity status.
- An unverified-tenant warning in owner request details is information, not an automatic ban on owner acceptance.

If verified identity is mandatory for communication or booking, the backend must enforce the rule on every relevant operation and the client routes must agree. The current source does not prove that this policy is consistently enforced.

Sources: [Authentication session flow](apps/sokoun_app/lib/features/shared/auth/data/auth_session_data.dart), [registration data](apps/sokoun_app/lib/features/shared/auth/data/models/register.dart), [KYC submission data](apps/sokoun_app/lib/features/shared/auth/data/models/kyc_upload_documents_data.dart), [validators](packages/core/lib/core/helpers/validators.dart), [inbox verification gate](apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_list_tile.dart), [verification-summary handoff](docs/profile_settings_support_backend.md).

## 6. Property inventory and listing lifecycle

### 6.1 What a property represents

A property is an owner-controlled rental listing, with public marketing information, structured rental preferences, viewing activity, review/performance data, and private review evidence.

| Information group | Represented fields |
| --- | --- |
| Identity and description | Stable property ID, owner ID, title, description, property type, share link when supplied |
| Rent | Price, price period, minimum rental months, deposit |
| Structure | Bedrooms, bathrooms, area in square metres, optional display-space text, floor, construction year |
| Location | Country, governorate, city, district/neighborhood, street, latitude, longitude |
| Tenant preferences | Suitability group, furnishing, smoking permission |
| Amenities | Wi-Fi, elevator, garage, security, balcony, air conditioning, near metro, natural gas, electricity meter, water meter |
| Public media | Cover photo, other photos, optional photo names/descriptions, video tour and duration |
| Trust and lifecycle | Review status, property verification, owner verification, ownership-verification flag |
| Private evidence | Ownership-proof file, visible only to its owner and authorized administrators under the contract |
| Engagement | Favorite state, rating/reviews, views and viewing requests where supplied |

Ownership proof and public property images have different audiences. An ownership document must never be treated as another gallery image.

### 6.2 Owner creation and edit journey

The active owner flow groups the form into:

1. **Property basics:** Type, governorate/city, address, title, rooms, area, floor, and map coordinates.
2. **Media:** Property photos with optional names/descriptions, and the video tour.
3. **Rental details:** Price/period, minimum rental months, suitability, description, amenities, and optional extra details/evidence.
4. **Review/submission result:** Review the entered information and submit it for platform review.

The same flow supports editing. It loads the full existing property rather than assuming the short listing card contains all fields. Leaving a changed form is guarded; there is no demonstrated durable local draft recovery after app termination.

### 6.3 Current client submission rules

| Field | Client rule or documented contract |
| --- | --- |
| Title and description | Title required; description at least ten trimmed characters |
| Property type | Required selection; supported catalog |
| Governorate and city | Both required; selected identifiers and names; city must belong to governorate under the backend contract |
| Street | Required; independent of district/neighborhood |
| Coordinates | Valid latitude/longitude ranges; stored with six-decimal formatting |
| Bedrooms and bathrooms | Positive integers in the current form |
| Area | Positive integer square metres |
| Floor | Optional integer; zero and negative floors are valid |
| Price | Positive amount in the current EGP experience |
| Price period | Daily, weekly, monthly, or yearly |
| Minimum rental period | Positive integer months |
| Suitability | All, families, singles, students, or female students |
| Furnishing | Boolean |
| Smoking | Optional yes/no; an unspecified value is distinct from “no” |
| Construction year | Optional; 1800 through the current year |
| Deposit | Optional; `none`, `half_month`, `one_month`, `two_months`, or a non-negative numeric amount |
| Amenities | Supported slugs only; furnishing is a separate field |
| Photos | Between **10 and 25** usable photos for client submission |
| Video | Required by the current mobile submission form; new selected video duration **1–60 seconds** |
| Ownership proof | Optional in the form; private JPG/PNG evidence under the handoff |

The positive-bedroom rule currently applies even when a studio type is selected. If zero-bedroom studios should be valid, that rule needs an explicit product/client change.

The media contract permits incomplete drafts while upload composition is in progress and nullable/removed video. The mobile form is stricter at submission: it requires enough photos and a video. The prototype's skippable-video concept is not the current mobile rule.

Marketing describes a recent electricity/water bill, ownership contract, or lease contract as possible ownership evidence. These are advertised examples; the repository does not prove that a deployed reviewer policy accepts every such document or validates an uploader's legal authority to list.

### 6.4 Media handling and failure recovery

- The first selected photo becomes the cover. The cover also appears first in the image collection and is counted once.
- Public images have stable IDs. Optional names and descriptions support Arabic text; empty captions can clear existing values.
- Creation first stores the property and initial media, then uploads remaining photos through the image endpoint.
- If some uploads fail, the client keeps the created property ID and successful image records. Retrying uploads the remaining work rather than creating another property.
- Editing sends retained existing-image IDs. Existing images omitted from that list are removed under the documented contract.
- Metadata updates identify photos by ID, and a retained photo can be promoted to cover. Replacing a photo is a removal/upload operation rather than silently mutating its stable identity.
- Omitted video or ownership-proof changes preserve existing files. Explicit removal fields clear them. New-video upload and simultaneous removal are incompatible.
- Removing ownership proof resets its ownership-verification result under the returned contract. The older proposal also requires a reset when proof is replaced; that replacement behavior still needs confirmation against the deployed service.
- New video files are documented as MP4/H.264-compatible, with a playable HTTPS response URL.

Maximum image count and image-retention operations must be enforced by the server, including concurrent uploads. Failed uploads or rejected edits must not be presented as successful publication.

### 6.5 Review status, publication, and rejection

The owner Properties screen uses three review tabs:

| Review state | Business interpretation |
| --- | --- |
| Under review | New or edited submission awaiting a moderation decision; default owner tab |
| Accepted | Moderation has accepted the listing |
| Rejected | Moderation declined the listing; the owner can correct and resubmit |

The returned edit contract states that **every owner PATCH sets `status=under_review`**. Edited listings move out of their prior tab and are reconsidered.

The backend must filter by the authenticated owner and the requested review status before counting and paginating. The mobile asks for ten listings per page. [The status-tabs handoff](docs/owner_property_status_tabs_backend.md) explicitly says server filtering still requires implementation/verification.

Review acceptance and `is_verified` are separate: the status-tabs handoff allows an accepted but unverified property. The property-media handoff says unverified or under-review listings stay out of public feeds until admin verification. These statements leave the exact **public publication gate** to be reconciled with the backend. This document does not assume that “Accepted” alone means publicly visible.

Additional constraints:

- Publication/admin approval requires at least ten unique images under the media handoff.
- Owners can retrieve their own pending/rejected drafts; tenants must not receive those drafts or private evidence.
- Owners cannot grant themselves approval, verification, ratings, or moderation privileges through writable property fields.
- The current rejection page says detailed review feedback is not yet available. It offers correction/resubmission but does not render a real rejection-reason contract.
- Hide/pause and mark-rented concepts exist in enums/prototype controls, but the active listing card does not wire them as completed owner actions.
- A readable listing change-history feature is not implemented, despite marketing/prototype references.

Whether an old accepted version remains public while edits are reviewed is unspecified. The client should not be treated as a versioned-publication system.

### 6.6 Property deletion

Deletion is an implemented owner action with confirmation. The client removes the listing only after the server acknowledges the **requested property ID** with `deleted=true`. An error leaves the listing available to the owner; duplicate submissions are disabled during the request.

The documented server contract requires:

- Only the authenticated listing owner can delete it.
- A conflict blocks deletion if **pending/confirmed viewing requests or active leases** exist.
- Deleted properties disappear from the owner's lists and totals; public listings and related favorite/availability references must be handled consistently.
- Unauthorized, missing, and conflicting resources return appropriate errors.

Historical record retention, cancellation of dependent records, media lifecycle, and active-lease verification require server policy. The mention of leases in deletion rules does not establish a working mobile lease-creation feature.

Sources: [Owner property form data](apps/sokoun_app/lib/features/owner/home/data/models/owner_add_property_content.dart), [create/edit screen](apps/sokoun_app/lib/features/owner/home/presentation/screens/owner_property_flow_screen.dart), [property services](apps/sokoun_app/lib/features/owner/properties/data/owner_properties_data.dart), [property-media/edit/delete handoff](MOBILE_PROPERTY_MEDIA_EDITING_DELETION_HANDOFF.md), [review-status tabs](docs/owner_property_status_tabs_backend.md).

## 7. Tenant discovery, property details, and saved properties

### 7.1 Home and search

Tenant Home loads backend-provided recommendations/listings and optional banner content. Calling a section “suggested” does not establish machine-learning recommendations or a guaranteed personalized ranking method.

Search supports:

- Free text and area selection using city/district text.
- Minimum/maximum rent with non-negative values and minimum no greater than maximum.
- Property type and price period.
- Suitability, furnishing, property verification, and smoking preference.
- Bedrooms, bathrooms, and supported amenities.
- Ordering and paginated results; default newest first, ten items per requested page.

Catalog choices and labels come from backend type/filter/place services. The app combines free text, city, and district into one `search` parameter. It does not establish structured radius search or independent geographic filtering merely because those fields appear in an older API example.

The search interface retains active filters, supports clearing/removing individual filters, distinguishes an empty result from a failed request, and provides retry behavior. Floor, deposit, building year, and minimum rental months are not demonstrated as active search filters.

### 7.2 Recent search and nearby discovery

Recent searches are local convenience data: keep up to **five**, reuse an entry, remove one, or clear them.

Nearby discovery requests device location, reverse-geocodes an area name, and feeds that area into the normal text search. It does not demonstrate distance-ranked inventory, a radius threshold, route travel times, or a real-time geospatial matching contract.

Location permission is optional. Manual area selection remains available when permission or location services are unavailable. A privacy preference concerning location-based search is separate from the operating system's permission.

### 7.3 Property evaluation

Property details can show all available public listing fields, rental/deposit terms, amenities, suitability, owner identity/badges, rating/reviews, gallery, and video. Missing optional values should remain absent rather than become fabricated facts.

- Descriptions can expand for full reading.
- Photo galleries deduplicate media and preserve captions/cover order.
- Actual video URLs enable a playable tour.
- A map action opens the property coordinates in Google Maps.
- Sharing uses the available property-link information.
- Photos can be saved to the device album named **سكون**, subject to platform access and download success; this is distinct from saving a listing to the account's shortlist.
- The location UI may describe a location as approximate, but the repository does not prove a server coordinate-obfuscation policy.
- Ownership proof is private; tenants may see its verification result, not the document itself.

### 7.4 Favorites / Saved

Saved properties are a signed-in account collection, read from the server. Saving and unsaving use separate server operations. Optimistic favorite changes are rolled back on API failure.

The Saved screen supports search/filter/sort of fetched favorites, including price, type, period, suitability, furnishing, verification, smoking, rooms, and amenities. Sort choices include price, rating, and saved date, in both directions. Amenity matching requires the selected amenities together.

Removing a favorite is persisted; Undo performs a re-save request. The screen distinguishes an empty shortlist from a shortlist with no matches for the chosen filters. Favorites provide a shortlist for evaluation; there is no implemented side-by-side property comparison tool.

Sources: [Search model and request rules](apps/sokoun_app/lib/features/tenant/home/data/models/property_search_model.dart), [location-derived search](apps/sokoun_app/lib/features/tenant/home/data/current_location_data.dart), [public property model](apps/sokoun_app/lib/features/tenant/home/data/models/property_details_model.dart), [favorites services](apps/sokoun_app/lib/features/tenant/favorites/data/favorites_data.dart), [saved-property filtering](apps/sokoun_app/lib/features/tenant/favorites/data/favorite_property_filter.dart), [photo saving](apps/sokoun_app/lib/features/tenant/home/presentation/cubits/property_photo_save_cubit.dart).

## 8. Viewing requests and reviews

### 8.1 Requesting a viewing

A tenant selects a date, a time, and an optional note for a property. The mobile sends a property-linked viewing request and displays the submitted summary. The intended next step is an owner decision, not immediate lease/occupancy confirmation.

Current date/time behavior matters:

- The screen generates **seven days starting today** locally.
- Time is selected using a time picker; the screen does not fetch authoritative property slots from the collection's `available_dates/` service.
- The client does not establish a universal rule preventing selection of a past time today.
- Booking conflicts reported as already booked/unavailable cause the selected time to be cleared for correction.

The backend must validate ownership restrictions, identity policy, future times, availability, duplicate requests, and concurrent slot conflicts. Selecting a time in the UI does not prove that the slot is available or reserved.

### 8.2 Viewing states and permitted actions

| State | Business meaning | Client fallback actions when server action flags are absent |
| --- | --- | --- |
| Pending | Waiting for owner response | Cancel |
| Accepted | Owner agreed to the viewing | Cancel, contact/chat when owner ID exists, review |
| Rejected | Owner declined | Find alternative properties |
| Completed | Viewing marked completed by a service | Review |
| Canceled | Request canceled | No active decision/review action by default |

The client recognizes compatibility aliases such as approved/confirmed for accepted and cancelled for canceled. Server-provided `can_cancel`, `can_chat`, `can_review`, and `can_find_alternative` take precedence over fallback permissions.

Tenant filters are All, Approved, Pending, and Rejected. Completed and canceled records remain accessible through All. Details display the property, date/time, status, owner information, and additional server details or an existing review.

Cancellation requires confirmation and updates the server to `canceled`. The local record changes only after success. No complete mobile rescheduling service or tenant/owner “mark completed” action is demonstrated.

Accepted visit details can show an owner phone number when it is supplied. Phone disclosure must be decided by the backend; the client is not evidence that contact details are always hidden or always revealed at a particular event.

### 8.3 Owner request decisions

Owners receive request lists and details with tenant/property information, scheduling, notes, verification indicators, and decision permissions.

- Filters include All, New, Accepted, Rejected, and Completed; pending requests are grouped with new requests.
- Accept/reject are intended for new/pending requests and respect server permission flags.
- Accept invokes the request-specific accept service.
- The active reject action sends the fixed reason **`timing_not_suitable`** with an empty custom reason. Prototype reason selectors and wider API examples do not establish configurable rejection reasons in the active mobile screen.
- Messaging uses the tenant ID attached to the request.
- Full versus masked tenant phone display depends on server data, including the phone-revealed flag.

Availability and request conflicts must be checked atomically by the server; owner UI permission flags alone cannot enforce them.

### 8.4 Reviews and reputation

A visit-linked review asks for three required integer scores from **1 to 5**:

1. Property cleanliness.
2. Accuracy of the property details/listing.
3. Interaction with the owner.

An optional comment is trimmed and submitted with the scores. Successful review submission refreshes the relevant visit detail. Property review lists and the account's own reviews are separate read destinations; summary averages/counts come from the server.

The product/marketing describes post-visit reviews, but fallback client permissions allow review for **accepted as well as completed** visits. Existing-review display alone does not establish a universal duplicate-submission guard. The backend must define and enforce visit eligibility, one-review policy, review visibility, moderation, and rating aggregation. No specific weighted-average formula or review-edit policy is established by this repository.

The review action from a notification currently opens the rating form without its required visit ID, so that entry cannot complete a submission. The visit-details entry supplies the ID. This is a separate integration gap from review eligibility.

Sources: [Booking screen](apps/sokoun_app/lib/features/tenant/visits/presentation/screens/book_visit_screen.dart), [tenant visit services](apps/sokoun_app/lib/features/tenant/visits/data/tenant_visits_data.dart), [visit permissions](apps/sokoun_app/lib/features/tenant/visits/data/models/tenant_visit_content.dart), [review body](apps/sokoun_app/lib/features/tenant/visits/data/models/visit_review_body.dart), [owner request services](apps/sokoun_app/lib/features/owner/visits/data/owner_visit_requests_data.dart).

## 9. Owner operations, availability, analytics, and revenue

### 9.1 Dashboard and inventory access

The owner dashboard displays backend-sourced owner identity and verification, visits this week, active properties, overall rating, pending-request count, and pending viewing previews. Quick request decisions use the real request services.

The active property list offers property details, editing, analytics, and deletion. Tapping a rejected listing opens its rejection/resubmission destination. Review tabs maintain distinct collections and pagination; an empty tab is a valid result.

Displayed dashboard values are not an independent accounting or audit system. The backend defines how “active property,” weekly visits, overall rating, and pending request totals are calculated.

### 9.2 Calendar and property availability

The owner calendar reads visits by month/year. The availability editor represents a property's weekly schedule as dates with time slots and enabled/disabled flags.

Implemented availability behavior includes:

- Move between weeks and select a day.
- Inspect enabled, disabled/unspecified, and booked slots.
- Toggle editable slots and add a custom time.
- Prevent duplicate times locally and keep booked slots locked.
- Save changed dates through the availability service; preserve unsaved changes when a save fails.

The client reads using `week_start` and writes the date plus its slots. An older root collection example uses `start_date`; those request contracts need to agree. A recurring weekly-rule engine, timezone policy, holiday calendar, and automated reminder cadence are not specified.

**Current access limitation:** The Requests toolbar opens the calendar using the first loaded request with a property ID. The calendar's availability action requires a property ID; there is no completed all-properties selector or direct availability action on the active listing card. An owner without a suitable loaded request has limited access to setting a property's schedule. Tenant booking also does not consume these authoritative slots, as explained in section 8.

### 9.3 Property performance

The property analytics destination requests performance for **7, 30, or 90 days**, defaulting to 30 days.

| Metric/content | Business interpretation |
| --- | --- |
| Views | Recorded attention to the listing |
| Viewing requests | Requests associated with the property |
| Saves | Shortlist interest |
| Acceptance rate | A server-provided percentage; its exact denominator is not documented here |
| Daily chart series | Server-supplied activity over the requested period |
| Search criteria percentages | Server-provided audience/search insights where available |

When detailed metrics are unavailable, the screen uses an empty state rather than inventing activity. The source does not establish unique-versus-total view rules, attribution windows, bot exclusion, conversion to signed leases, or an independently verified analytics pipeline.

### 9.4 Revenue information

The owner revenue destination reads:

- Total revenue this month.
- Percentage change, direction, and comparison text.
- Property-associated amounts, due dates, and statuses: **paid, due, late, upcoming**.
- Recent transactions with stable IDs, titles, dates, amounts, type, and credit/debit direction.

Amounts are displayed in EGP. This is a read/reporting interface. It does not let an owner request a payout, collect a payment, reconcile a bank transfer, or issue a refund. The reader exists in client source and the profile handoff references it, but the root API collection is not complete evidence for this revenue service.

The source does not establish whether “revenue this month” means cash received, rent accrued, gross rent, or net proceeds after fees. Accounting definitions and reconciliation must be confirmed before treating it as a financial statement.

Sources: [Owner dashboard data](apps/sokoun_app/lib/features/owner/home/data/models/owner_dashboard_model.dart), [calendar](apps/sokoun_app/lib/features/owner/visits/presentation/screens/owner_requests_calendar_screen.dart), [availability editor](apps/sokoun_app/lib/features/owner/visits/presentation/screens/owner_availability_screen.dart), [owner visit services](apps/sokoun_app/lib/features/owner/visits/data/owner_visit_requests_data.dart), [analytics screen](apps/sokoun_app/lib/features/owner/properties/presentation/screens/owner_property_analytics_screen.dart), [revenue model](apps/sokoun_app/lib/features/owner/properties/data/models/owner_revenue_content.dart).

## 10. Messaging and communication

### 10.1 Conversation model and entry points

Tenant and owner workspaces use shared account conversations. Entry points include the Messages tab, a property's contact action, and eligible viewing/request details.

The inbox shows the other participant, optional property label, latest-message preview, timestamp, unread count, and server-supplied verification/online indicators. Search matches conversation names, property labels, and latest previews; it is not demonstrated as full-text search of every historical message.

Conversation creation submits **the recipient's `user_id`**. It does not submit a property ID. A conversation may display property information returned by the backend, but the client does not guarantee one independent conversation per listing. The exact backend grouping/deduplication rule is unspecified.

Normal chat and read-only previous-history screens are separate destinations. Read-only history has no composer or live sending connection. Restricted chat provides verification guidance. Verification gating varies by entry point, as recorded in section 5.4.

### 10.2 Supported messages and delivery behavior

The active customer messaging flow supports **text**, including Arabic and other Unicode text, with a maximum **5,000 characters** and a non-blank requirement.

The client combines paginated REST conversation/history services with a session-authenticated raw WebSocket at `/ws/chat/`. It handles incoming events, message/read updates, reconnect behavior, unread indicators, stable-ID deduplication, and pending/sent/failed states. A REST send fallback is used when live confirmation is unavailable.

Pending outgoing messages are maintained by the running chat state. This is not a durable offline mailbox across closing the thread or restarting the app. Server persistence, acknowledgments, authorization, unread calculation, and duplicate prevention remain service responsibilities.

Photo/file attachments, voice messages, voice/video calls, and a complete block-user action are not active mobile messaging features. Prototype attachment sheets and legacy calling libraries do not establish them.

### 10.3 Contact privacy and complaints

Business copy encourages in-app communication and includes privacy banners. Actual phone disclosure depends on backend fields in visit/request details; no universal phone-number secrecy rule can be inferred from banners.

The chat report sheet lists reasons including inaccurate property information, offensive content, possible fraud, phone numbers in photos, unavailable property, and other issues. **Its submit action only closes the sheet successfully; it does not create a server report.** Returning to the inbox afterward is not evidence that an administrator received a complaint.

Formal support tickets include owner/tenant complaint categories through a separate **proposed** service. Reporting, blocking, enforcement, and support tickets must not be treated as interchangeable working features.

Sources: [Chat services](apps/sokoun_app/lib/features/shared/chat/data/chat_data.dart), [conversation/message data](apps/sokoun_app/lib/features/shared/chat/data/models/chat_content.dart), [live thread behavior](apps/sokoun_app/lib/features/shared/chat/presentation/cubits/chat_thread_cubit.dart), [conversation creation](apps/sokoun_app/lib/features/shared/chat/presentation/cubits/create_conversation_cubit.dart), [unconnected report sheet](apps/sokoun_app/lib/features/shared/chat/presentation/widgets/report/chat_report_sheet.dart).

## 11. Notifications and engagement

### 11.1 Notification center

The signed-in notification center supports paginated reads, unread-only filtering, detail views, marking one notification read, marking all read, unread counts, and relevant navigation/actions. Requested page size is **20**.

The payload model recognizes these business event families:

| Family | Examples represented in the client |
| --- | --- |
| Viewing activity | New request, acceptance, rejection, review/rate-visit prompt |
| Communication | New message |
| Owner inventory | Property verified, property views, daily visibility/bump event |
| Tenant discovery | New property, property update |
| Account | Identity-verification update, security alert |
| Marketing | Promotion/product update |

A supported event name does not prove that the corresponding business service exists. For example, a daily-bump payload is not evidence of a purchased listing-boost product.

Notification routing uses the event context and validated IDs to select the appropriate workspace and destination. Owner requests/listing events lead to owner activity; tenant viewing events lead to tenant activity; message events use Messages; identity/security events lead to Profile verification or Settings. This navigation does not authorize access to a resource the recipient does not own.

### 11.2 Preferences, permissions, and devices

Server-backed notification preference keys are:

- `visit_notifications`
- `owner_messages`
- `property_updates`
- `security_alerts`
- `promotions_and_updates`

The server supplies setting labels/values and whether a setting can change. Required alerts can be locked through that contract. Each preference update persists through the notification-settings service; failed changes must not be presented as saved.

Server subscriptions and operating-system push permission are separate. The app explains permission before the native prompt, remembers its automatic prompt decision per installation, and offers device/settings guidance when delivery is disabled. Denying push does not remove the core browsing experience.

FCM device registration is linked to the authenticated account, including token refresh and unregistering on logout. Foreground events refresh relevant unread data. Push delivery, event creation, delivery retries, and correct recipient selection are backend/platform obligations.

Chat unread counts, notification unread counts, and workspace activity counts are different measures. A saved-property total is not a count of unread notifications.

### 11.3 Retention and release communication

- A local inactivity notification is scheduled **24 hours** after tracked foreground/successful-API activity. Its Arabic return-to-app copy is a retention prompt, not proof that unread conversations actually exist.
- A What's New mechanism records the first installation without showing an upgrade announcement, then can show release changes once for a subsequent version.
- Update prompting can use remote minimum-version configuration. This is an app-maintenance mechanism, not a defined customer service SLA.

No campaign calendar, message-frequency cap, marketing eligibility policy, or promotional offer terms are established by these mechanisms.

Sources: [Notification contract](apps/sokoun_app/MOBILE_NOTIFICATIONS_README.md), [notification reads](apps/sokoun_app/lib/features/shared/notifications/data/notifications_data.dart), [notification settings](apps/sokoun_app/lib/features/shared/notifications/presentation/cubits/notification_settings_cubit.dart), [notification routing](apps/sokoun_app/lib/features/shared/notifications/presentation/notification_navigation.dart), [inactivity reminder](packages/core/lib/core/notification/inactivity_notification_service.dart), [release announcements](apps/sokoun_app/lib/features/shared/whats_new/whats_new_service.dart).

## 12. Profiles, preferences, legal pages, and account closure

### 12.1 Profile and account summaries

Both workspaces end in a shared Profile layout with account identity, editing, verification status, Settings, and Support. Settings and Support remain available when a profile read fails.

| Tenant-specific content | Owner-specific content |
| --- | --- |
| Saved/visit/chat and completion information where supplied; contracts entry; own reviews; detailed account summary | Property/request/rating statistics and recent received reviews; revenue entry |

The owner More menu has been consolidated into Profile. Visits remain in the tenant Visits tab; properties and requests remain in their owner tabs. Common identity edits must be reflected in both workspaces.

### 12.2 Profile editing

The shared editor supports name, phone, avatar, and optional editable metadata such as gender and city when loaded. Email and birth date are read-only in this editor.

- Name/phone drafts remain visible while extended profile data loads or a read is retried.
- A failed extended read does not require replacing known identity fields with blanks.
- Saves send known name/phone, an optional new avatar, and only changed optional metadata.
- Omitted city/gender values preserve existing data. An explicit city clear is different from an unchanged city.
- A rejected save preserves the signed-in account and entered draft. Navigation back and identity replacement follow server success.

Avatar selection uses account-image validation rather than accepting an arbitrary file extension. Identity-edit permissions are shared across workspaces; selecting owner does not grant different ownership over the common account.

### 12.3 Language, appearance, and privacy

| Preference | Scope and behavior |
| --- | --- |
| Language | Arabic initial/fallback; English available; saved preference respected; legal/help content requests carry language |
| Appearance | Device default, light, or dark; device-level preference survives account changes |
| Location for search | Server-backed `share_location_for_search` when supplied |
| Profile visibility | Server-backed `show_profile_in_search` when supplied |
| Notifications | Owned by the dedicated notification settings service, rather than duplicated in privacy settings |

Privacy controls display supported values from the service; unsupported options are not assumed to exist. Location privacy preference does not grant OS location permission. Dark/light appearance is implemented in current app source, even though an older profile handoff describes appearance as later work.

### 12.4 Password and public information

Change-password screens are implemented against **proposed** `auth/users/set_password/`. The body contains the current password, new password, and confirmation. Client rules require at least eight characters for the new password and matching confirmation. The implemented navigation expects the current session to remain valid after success; the backend's session-revocation and social-account policy is unresolved.

Terms, privacy policy, and About use public-page services with the selected language. About includes the application logo and installed version. The repository does not supply approved legal terms, a confirmed contracting entity, binding fees, or a retention policy merely by displaying links/screens.

### 12.5 Logout and account deletion

Logout requires confirmation and server success before local account cleanup. If revocation fails, the app does not simply report a successful logout. Expired authentication follows the app's session-reset behavior.

Account deletion uses a dedicated screen and explicit acknowledgment. A successful delete response triggers sign-out/account cleanup. A rejected deletion keeps the user signed in.

The deletion screen's irreversible-removal copy must be reconciled with the backend's approved policy. Treatment of active leases/viewings, listings, conversations, reviews, documents, audit records, financial history, device tokens, and retention obligations is not established by client copy. Account deletion is distinct from deleting one property.

Sources: [Shared Profile](apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_screen.dart), [profile editor](apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_edit_screen.dart), [settings](apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_settings_screen.dart), [delete-account screen](apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_delete_account_screen.dart), [profile/settings backend handoff](docs/profile_settings_support_backend.md), [design system](design.md).

## 13. Contracts and customer support

The screens in this section are implemented against services explicitly marked **proposed** in the profile/settings/support handoff. They should not be represented as confirmed deployed customer services.

### 13.1 Tenant contracts

The tenant contract list displays existing contracts, with property title, start/end dates, and **active, expired, or cancelled** status. If a private authorized document URL is present, the user can open the document in a system viewer.

The service must scope results to the authenticated user and return authorized, expiring HTTPS document links. Missing documents omit the action; a profile contract count must not be used to fabricate contract records.

This flow does not create leases, negotiate terms, collect signatures, renew/terminate contracts, or generate legally executed agreements. The existence of active-lease deletion restrictions is a separate backend-contract concern.

### 13.2 Help center and contact information

Help content is requested for the current workspace and language. Users can search the returned FAQ content and navigate to New Ticket or My Tickets. Tenant questions and owner questions can differ.

Phone, email, and opening hours are displayed only when the service provides real values. Empty contact values omit the corresponding contact action. Placeholder prototype numbers and live-support-chat controls are not implemented service channels.

### 13.3 Ticket categories and creation

Common categories are viewing, payment, verification, property, and other. Tenant context adds a complaint about an owner; owner context adds a complaint about a tenant. Selecting a payment category does not establish in-app payment processing.

| Ticket input | Rule |
| --- | --- |
| Workspace | Tenant or owner context; does not override identity/authorization |
| Subject | 3–160 trimmed characters |
| Description | 10–4,000 trimmed characters |
| Attachments | Up to three images; maximum 5 MiB each; JPG/JPEG, PNG, or WebP |
| Successful creation | Must return a real stable ticket ID/reference and the initial message |

Attachment-free tickets use JSON; attached tickets use multipart data. Rejected submissions retain the draft. The app does not synthesize a ticket number when the service is unavailable.

### 13.4 Ticket lifecycle and replies

| Ticket state | Reply behavior |
| --- | --- |
| Open | User can reply |
| In progress | User can reply while support handles the issue |
| Resolved | Read thread/history; create a new ticket for a new issue |
| Closed | Read thread/history; no reply |

My Tickets reads a user/workspace-scoped paginated list, requested at **20 per page**, ordered by recent update. Ticket details show chronological user/support messages and available attachments. Replies require **1–4,000 trimmed characters** and a service-confirmed updated thread. A ticket closed during reply should cause a conflict instead of accepting an invalid message.

The backend must enforce user/workspace ownership for every ticket, reply, and attachment. Attachment links must be private/authorized. A complaint does not automatically ban an account. Assignment, escalation, response times, reopening, and resolution guarantees remain unspecified operational policies.

Sources: [Profile/contracts/support handoff](docs/profile_settings_support_backend.md), [proposed service collection](docs/profile_settings_support.postman_collection.json), [contract screen](apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_contracts_screen.dart), [support screens](apps/sokoun_app/lib/features/shared/support/presentation/screens), [ticket submission model](apps/sokoun_app/lib/features/shared/support/data/models/support_ticket_body.dart).

## 14. Administration and operational design

### 14.1 Administrative scope

The exported React design includes administrative dashboards and many operational screens. They use sample values and illustrative controls, with no demonstrated end-to-end backend integration. All capabilities in this section are **design only**, unless a separate customer/backend contract is explicitly identified elsewhere.

| Operational area | Intended business responsibilities shown in the design |
| --- | --- |
| Executive dashboard | Summarize users, inventory, verification queues, activity, revenue, and operational workload |
| Identity review | Queue submissions, inspect ID front/back/selfie, approve/reject, request correction, add internal notes |
| Listing moderation | Inspect photos, address/map, rent, description, ownership evidence, and reviewer checklist; accept/reject submissions |
| User management | Search account records, inspect activity and verification, suspend/ban/unban, inspect flagged/banned users |
| Complaints and reports | Triage allegations, inspect context, make enforcement decisions, and retain a case history |
| Support console | Review tickets/threads, assign or handle work, reply, and resolve cases |
| Content moderation | Inspect potentially misleading content, poor photos, and contact information in media |
| Finance | Review rent/platform-fee concepts, transaction logs, and refund designs |
| Communication oversight | Chat-monitoring concept in the storyboard; no established live oversight service or access policy |
| Campaigns | Compose audience-targeted push messages and inspect illustrative delivery/open histories |
| Roles | Define operator access and assign role membership |
| Operations | System-health views, errors/performance, activity logs, administrative audit/export concepts |
| Platform settings | Intended document/review and other operational configuration |

The listing-review design includes checks such as clear/enough photos, plausible price, accurate description, correct coordinates, verified owner, and no phone number displayed in images. Earlier prototype photo examples/checklists conflict with the current **10–25** photo contract; current mobile/handoff rules take precedence.

Risk labels and content flags are sample moderation concepts. An initialized shared image-safety helper is not evidence of active listing scanning, fraud detection, phone-number redaction, or automatic enforcement.

### 14.2 Intended operator permission matrix

The prototype represents the following permission separation:

| Operator role | Review KYC | Accept/reject listings | Suspend users | Resolve tickets | Edit roles |
| --- | --- | --- | --- | --- | --- |
| System owner | Yes | Yes | Yes | Yes | Yes |
| Lead administrator | Yes | Yes | Yes | Yes | No |
| KYC reviewer | Yes | No | No | No | No |
| Property reviewer | No | Yes | No | No | No |
| Customer support | No | No | No | Yes | No |

This is a design permission matrix. It does not prove implemented server RBAC, admin login, audit controls, or restricted document access. Customer owner workspace is unrelated to the administrative “system owner” role.

Review SLAs, escalation thresholds, appeal procedures, financial approval limits, reviewer staffing, audit retention, and campaign consent rules are unspecified.

Sources: [Admin design screens](<Sokoon Figma Prototype Design/src/app/screens-admin.tsx>), [complete storyboard specification](<Sokoon Figma Prototype Design/src/imports/pasted_text/sokoon-app-flow-overview.md>), [prototype grouping](<Sokoon Figma Prototype Design/src/app/App.tsx>).

## 15. Marketing, distribution, and user experience

### 15.1 Marketing website

The Flutter landing page is a product introduction with Arabic/English switching, tenant/owner audience selection, a hero, trust/features sections, journey explanations, illustrative property cards/app previews, FAQs, and final download-oriented calls to action.

Business boundaries:

- Property examples are illustrative; they are not live available inventory.
- Sample favorites affect the current web page, not a customer's server shortlist.
- The website is not a second authenticated property-management client.
- App Store and Google Play availability is explicitly **coming soon**. Actual public store URLs and production availability are not established by these badges.
- The React prototype also has marketing/design screens; it is separate from the Flutter landing-page implementation.

Some content is ahead of current client behavior. Owner feature copy includes hiding/editing a property and tracking change history; hide/history are not complete mobile capabilities. FAQs/trust copy also imply verification gating and useful rejection feedback that current routes/contracts do not consistently provide. The website should not be used as the sole feature specification.

The landing README identifies real store links, approved legal/support destinations, release screenshots, production canonical/social metadata, and backend-aligned privacy/review statements as outstanding launch inputs.

### 15.2 Product experience and accessibility

The design direction is calm, trustworthy, private, and practical, with clear property facts, price, status, and next action. Tenant and owner share one visual system; teal is the shared primary/tenant color and gold marks owner identity.

The app supports:

- Arabic RTL and English LTR.
- Tajawal typography and localized strings.
- Device-default, light, and dark appearance.
- Phone/tablet layouts, including navigation rail on wider devices and wider detail/form layouts.
- Visible loading, empty, disabled, error, and success states.
- Text scaling, usable control targets, and reduced-motion behavior in the design system and landing implementation.

These are implementation/design capabilities, not evidence of a completed external accessibility certification or exhaustive device testing.

### 15.3 Distribution and dependencies

The mobile package is versioned `1.0.0+6` in the reviewed source, with development/production flavors and development as the configured default. That source version does not establish a public release.

Important business dependencies include the remote application API, authenticated sessions, Google sign-in, FCM/push services, private/public media hosting, device location and reverse geocoding, map/document launching, and store/update metadata. Failure or missing configuration in those services can affect the corresponding customer journey.

Sources: [Landing scope and launch inputs](apps/landing_page/README.md), [landing content](apps/landing_page/lib/landing/models/landing_content.dart), [mobile package](apps/sokoun_app/pubspec.yaml), [app design system](design.md), [localized content](packages/core/assets/translations/lang.json).

## 16. Business data and service responsibilities

### 16.1 Principal business entities

| Entity | Core relationships and purpose |
| --- | --- |
| Account | One person's identity, authentication, contact/profile information; usable in both workspaces |
| Identity submission/status | Belongs to an account; document completeness and reviewer decision are separate |
| Property | Belongs to an owner account; public rental facts plus private review evidence |
| Property image | Belongs to a property; stable ID, URL/file, name/description, cover/order information |
| Video tour | Property media with duration and playback URL |
| Ownership evidence | Private property document plus an independent verification result |
| Geography/catalog | Governorate, city, available area, property type, filter choices, amenity identifiers |
| Saved property | Account-to-property relationship with save timing and current listing representation |
| Viewing request | Links property, requesting tenant, owner, date/time, note, status, and allowed actions |
| Availability | Property-to-date/time-slot relationship, including enablement and booked state |
| Review | Visit-linked reputation record, component scores, optional comment, author and property/owner context |
| Conversation | Account participants and optional server-returned property context; no guaranteed property-specific creation rule |
| Message/read state | Conversation content, sender, stable ID/time, delivery and unread/read information |
| Notification | Recipient event, payload, read state, and destination/action information |
| Device registration | Authenticated recipient's push token/device association |
| Contract | User-associated existing lease/document summary; proposed read service |
| Support ticket/message | User/workspace-scoped case, category, reference/status, attachments, and reply thread; proposed service |
| Revenue/transaction view | Owner financial reporting fields; underlying collection/settlement origin unspecified |
| Administrative decision/audit | Intended operator actions/history; prototype scope here |

### 16.2 Data visibility and privacy boundaries

| Data | Intended/observed visibility |
| --- | --- |
| Approved public listing content | Public discovery/detail audience, subject to the unresolved exact publication gate |
| Pending/rejected listing drafts | Their owner and authorized review services; not public inventory under the handoff |
| Identity photos/national ID | Account-submission and authorized review use; not public profile material |
| Ownership proof | Listing owner and authorized administrators only; non-owner details omit it |
| Private contracts/support attachments | Authorized account/case access; expiring/private links required by the proposed contract |
| Conversations/messages | Authorized participants; the storyboard's monitoring concept does not establish a blanket admin-access policy |
| Phone/contact details | Returned according to service disclosure rules; current client contains both full and masked displays |
| Search history/appearance | Local convenience/preferences, with appearance device-wide |
| Activity/financial records | Account-scoped service reads; retention and authorized operational access unspecified |

Identity UI says documents are encrypted and used internally. That wording is an intended trust claim; the client repository alone cannot verify encryption at rest, key access, document retention, or operator controls. The same distinction applies to approximate-location and phone-privacy copy.

### 16.3 Backend business obligations represented by contracts

Across the marketplace, the server must:

1. Derive identity from the authenticated session and enforce account/property/ticket ownership; workspace is only UI context.
2. Enforce complete business rules even when a client bypasses or omits a visual guard.
3. Validate property catalogs/geography, rental/media constraints, private-file access, and approved publication status.
4. Resolve viewing availability, duplicate/conflicting requests, acceptance/cancellation eligibility, and review eligibility consistently.
5. Persist writes before reporting success; return real IDs, totals, status transitions, and readable errors.
6. Apply filters before totals/pagination, maintain deterministic ordering, and isolate users/workspaces where required.
7. Keep profile verification, listing status, ownership verification, event payloads, and counts synchronized with authoritative decisions.
8. Revoke sessions/devices and handle account/property deletion according to an approved dependent-record/retention policy.

These are documented integration requirements and business necessities, not proof that the absent backend implements them today.

## 17. Service and API inventory

This inventory links business activities to current client routes. Paths are relative to `/api/v1/` and retain trailing slashes. The live chat socket is a separate `/ws/chat/` connection. “Client uses” indicates source integration, not independently verified deployment.

### 17.1 Customer account and catalog services

| Business capability | Methods and relative paths | Status |
| --- | --- | --- |
| Register/email OTP | POST `auth/users/`, `auth/verify/`, `auth/resend-otp/` | Client uses |
| Login/account/session | POST `auth/login/`, `auth/google/`, `auth/refresh/`; GET `auth/users/me/` | Client uses |
| Password recovery/KYC | POST `auth/users/reset_password/`, `auth/complete-register/` | Client uses; reset-link completion external |
| Logout/delete account | POST `auth/logout/`; DELETE `auth/delete-account/` | Client uses; deletion policy needs confirmation |
| Shared profile and editing | GET `profiles/my-account/`, `profiles/user/my-profile/`; PATCH `profiles/edit/` | Client uses; `profiles/user/update/` retained for compatibility |
| Activity/reviews/counts | GET `profiles/account-summary/`, `profiles/my-rates/`, `profiles/tenant/unread-counts/`, `profiles/owner/unread-counts/` | Client uses |
| Privacy preferences | GET/PATCH `profiles/settings/` | Client uses |
| Public information | GET `pages/about-us/`, `pages/privacy-policy/`, `pages/terms/` | Client uses with language |
| Home/discovery | GET `homepage/`, `properties/`, `properties/{id}/` | Client uses |
| Search/location catalog | GET `properties/types/`, `properties/filter-options/`, `properties/available_places/`, `properties/governorates/`, `properties/cities/` | Client uses |
| Saved collection | GET `properties/saved/`; POST `properties/{id}/save/`; DELETE `properties/{id}/unsave/` | Client uses |
| Public reviews | GET `properties/{id}/reviews/` | Client uses |

### 17.2 Property, viewing, and owner services

| Business capability | Methods and relative paths | Status |
| --- | --- | --- |
| Create/edit/media/delete | POST `properties/create/`; PATCH `properties/{id}/`; POST `properties/{id}/images/`; DELETE `properties/{id}/delete/` | Client uses returned property handoff; live behavior unverified |
| Owner inventory | GET `properties/owned/?status=...` | Client uses; status filtering explicitly awaits server verification/implementation |
| Viewing submission | POST `properties/{id}/visits/` | Client uses |
| Tenant visit reads | GET `properties/visits/`, `properties/visits/{id}/`; request paths `properties/visits/requests/` and `properties/visits/requests/{id}/` also retained | Multiple paths need consistent backend semantics |
| Cancel/review viewing | PATCH `properties/visits/{id}/update/`; POST `properties/visits/{id}/review/` | Client uses |
| Owner request list/detail | GET `properties/owner/visits/requests/`, `properties/owner/visits/requests/{id}/` | Client uses; legacy received route remains |
| Owner decisions | POST `properties/owner/visits/requests/{id}/accept/`, `properties/owner/visits/requests/{id}/reject/` | Client uses |
| Owner calendar/slots | GET `properties/owner/calendar/`; GET/PUT `properties/owner/properties/{id}/availability/` | Client uses; tenant slot selection not integrated |
| Owner dashboard/profile | GET `properties/owner/dashboard/`, `properties/owner/profile/` | Client uses |
| Owner performance/revenue | GET `properties/{id}/statistics/`, `properties/owner/revenues/` | Client readers; collection/service coverage needs confirmation |

### 17.3 Communication, notification, and proposed services

| Business capability | Methods and relative paths | Status |
| --- | --- | --- |
| Conversations | GET `chat/conversations/`; POST `chat/conversations/create/` | Client uses; create body contains recipient `user_id` |
| History/send/read | GET `chat/conversations/{id}/messages/`; POST `chat/conversations/{id}/messages/create/`, `chat/conversations/{id}/read/` | Client uses plus raw WebSocket |
| Notification reads | GET `notifications/`, `notifications/{id}/`, `notifications/unread-count/` | Client uses |
| Notification read actions | PATCH `notifications/{id}/read/`; POST `notifications/mark-all-read/` | Client uses |
| Notification preferences/devices | GET/PATCH `notifications/settings/`; POST `notifications/devices/`, `notifications/devices/unregister/` | Client uses |
| Change password | POST `auth/users/set_password/` | **Proposed service** |
| Identity summary | GET `profiles/verification-status/` | **Proposed service** |
| Contract list | GET `profiles/contracts/` | **Proposed service** |
| Help center | GET `support/help-center/` with workspace/language | **Proposed service** |
| Ticket list/create | GET/POST `support/tickets/` | **Proposed service** |
| Ticket detail/reply | GET `support/tickets/{id}/`; POST `support/tickets/{id}/replies/` | **Proposed service** |

The authoritative request samples are in [the root collection](collection.json). Proposed profile/support routes have their own [draft collection](docs/profile_settings_support.postman_collection.json). [API constants](packages/core/lib/core/network/api_endpoints.dart) also contain legacy non-rental endpoints; those are excluded from this business inventory.

## 18. Implementation gaps and unresolved business decisions

### 18.1 Observable differences between intent and current delivery

| Area | Current evidence | Business consequence |
| --- | --- | --- |
| Identity gate | Verified-account copy; inconsistent chat/booking checks | The promise and actual eligible actions need one authoritative policy |
| Publication | Accepted status independent of verification; media contract hides unverified inventory | Exact public-listing gate needs confirmation |
| Rejection feedback | Current screen lacks detailed server reasons | Owners cannot yet rely on actionable rejection feedback |
| Listing state/actions | Hide/pause, mark rented, and change-history references lack complete active actions | These should not be sold as available capabilities |
| Media rules | Current mobile requires video and 10–25 photos; older designs are looser | Product/specification must use the current rule or explicitly change it |
| Viewing availability | Owner editor exists; tenant chooses locally generated dates/arbitrary time | Backend validation is essential and slot-based selection remains incomplete |
| Availability access | Calendar inherits a property from loaded requests | Owners cannot reliably manage every property's schedule through a dedicated inventory entry |
| Rescheduling/completion | Designs/statuses exist; complete mobile mutation absent | Do not promise full visit lifecycle self-service |
| Reviews | Marketing says post-visit; client fallback includes accepted visits | Eligibility/uniqueness must be settled and server-enforced |
| Notification review action | Opens rating form without a visit ID | This entry cannot submit a review; the visit-details route carries the required ID |
| Chat context | Creation uses recipient ID only | A distinct listing-specific thread is not guaranteed |
| Chat reporting/blocking/media | Report closes locally; blocking/attachments/voice/calls incomplete | Complaint delivery and richer chat are not confirmed services |
| Support/contracts/password/status | Screens exist; handoff calls services proposed | Customers need real deployed contracts before relying on these features |
| Payment/fees | Revenue readers and admin samples; no transaction journey | Revenue data is not proof of collection, settlement, or approved pricing |
| Administration | Broad static console prototype | Reviewer/support/enforcement operations need a separate working system |
| Owner status filtering | Client tabs implemented; server work explicitly outstanding | Counts and tab accuracy depend on backend filtering |
| API consistency | Legacy/new visit routes and differing availability query names | Integration contracts need reconciliation |
| Website distribution | Coming-soon badges, sample listings, pending launch inputs | The repository does not establish a live public launch |
| Privacy claims | UI claims versus absent server/private-file implementation | Access, encryption, disclosure, and retention require actual service evidence |

### 18.2 Commercial and operational decisions not settled by the code

The repository leaves the following questions open:

- Who operates/contracts for Sokoun, and which approved legal/privacy documents apply?
- What cities and property segments are included in launch, and who may list on behalf of an owner?
- Is approved KYC mandatory to list, message, request a viewing, accept a request, or complete a rental?
- Which documents prove identity and ownership, who reviews them, and what rejection/appeal and retention policies apply?
- What exact approval/verification combination publishes a property, and what happens to an accepted version during edits?
- What are request expiry, no-show, duplicate-request, late-cancellation, rescheduling, completion, and timezone rules?
- When are phone/address details disclosed, and is there any enforceable privacy masking or location-obfuscation rule?
- Who can review, how many reviews are permitted, can reviews change, and how are ratings/moderation/disputes handled?
- Does Sokoun collect rent/deposits/fees, and if so who pays, when, through which provider, with what payout/refund/tax rules?
- What produces revenue records, and do totals represent gross/net, cash/accrual, or another accounting basis?
- How are leases created/signed, and how do they affect property availability, deletion, payments, and account closure?
- What are support hours, response targets, escalation rules, abuse enforcement, and operator permissions in the real service?
- What account/property deletion is blocked, what data is retained, and what happens to historical messages/reviews/contracts?
- Are promotions/boosts paid or free, what controls visibility/ranking, and what marketing consent/frequency rules apply?
- What public domain/store destinations and production integration services are approved?

These are missing decisions, not invented requirements or recommended prices.

### 18.3 Business measures already represented

The client/design exposes a starting set of business measures: property views/saves, viewing requests and acceptance, pending requests, visits this week, active properties, reputation scores/review counts, profile completion, chat/notification unread totals, monthly owner revenue and change, and support case status. Administrative designs add queue/finance/campaign/system measures as examples.

Definitions, reporting ownership, targets, acquisition cost, retention cohorts, signed-lease conversion, marketplace liquidity, realized platform revenue, and unit economics are unspecified. Prototype totals are not real traction metrics.

## 19. Evidence and source index

### 19.1 Main references

| Reference | Business information supported |
| --- | --- |
| [Root workspace](pubspec.yaml) and [mobile package](apps/sokoun_app/pubspec.yaml) | Product areas, app dependencies/version/flavors |
| [Design system](design.md) | Brand direction, role identity, language, appearance, responsive/accessibility intentions |
| [Workspace navigation](apps/sokoun_app/lib/features/main_view/presentation/workspace_navigation.dart) | One-account workspaces, authentication access and destination recovery |
| [Authentication feature](apps/sokoun_app/lib/features/shared/auth) and [validators](packages/core/lib/core/helpers/validators.dart) | Registration, email OTP, Google login, recovery, Egyptian inputs, KYC submission |
| [Tenant discovery](apps/sokoun_app/lib/features/tenant/home) and [favorites](apps/sokoun_app/lib/features/tenant/favorites) | Search, area lookup, property evaluation, saved listings/photo saving |
| [Tenant visits](apps/sokoun_app/lib/features/tenant/visits) | Date/time submission, status/actions, cancellation, reviews |
| [Owner home](apps/sokoun_app/lib/features/owner/home), [properties](apps/sokoun_app/lib/features/owner/properties), and [visits](apps/sokoun_app/lib/features/owner/visits) | Inventory form, owner dashboard, request decisions, calendar, analytics/revenue |
| [Returned property handoff](MOBILE_PROPERTY_MEDIA_EDITING_DELETION_HANDOFF.md) | Current media, full edit, privacy, publication, and deletion contract |
| [Original property notes](docs/property_media_edit_delete_backend.md) and [status-tabs handoff](docs/owner_property_status_tabs_backend.md) | Contract history and explicit server filtering obligations |
| [Chat feature](apps/sokoun_app/lib/features/shared/chat) | Conversation creation, text delivery/history, restriction gates, incomplete reporting |
| [Notification handoff](apps/sokoun_app/MOBILE_NOTIFICATIONS_README.md) and [notification feature](apps/sokoun_app/lib/features/shared/notifications) | Business events, settings, device lifecycle, read state, routing |
| [Profile/settings/support handoff](docs/profile_settings_support_backend.md) | Shared account behavior, proposed endpoints, contracts/support privacy and state rules |
| [Profile](apps/sokoun_app/lib/features/shared/profile), [support](apps/sokoun_app/lib/features/shared/support), and [appearance](apps/sokoun_app/lib/features/shared/appearance) | Actual customer screens, account preferences and edits |
| [API constants](packages/core/lib/core/network/api_endpoints.dart), [root collection](collection.json), and [proposed collection](docs/profile_settings_support.postman_collection.json) | Current/draft route inventory and compatibility differences |
| [Landing README](apps/landing_page/README.md) and [content](apps/landing_page/lib/landing/models/landing_content.dart) | Marketing scope, sample inventory, distribution status and copy |
| [Prototype storyboard](<Sokoon Figma Prototype Design/src/imports/pasted_text/sokoon-app-flow-overview.md>) and [admin screens](<Sokoon Figma Prototype Design/src/app/screens-admin.tsx>) | Design-only flows, operational roles, moderation and financial examples |

### 19.2 Existing verification evidence

The repository includes focused test definitions for [workspace navigation](apps/sokoun_app/test/workspace_navigation_test.dart), [account validation](apps/sokoun_app/test/account_validation_test.dart), [OTP behavior](apps/sokoun_app/test/auth_otp_contract_test.dart), [property media](apps/sokoun_app/test/property_media_handoff_test.dart), [owner tabs](apps/sokoun_app/test/owner_listings_status_test.dart), [tenant visits](apps/sokoun_app/test/tenant_visits_flow_test.dart), [owner requests](apps/sokoun_app/test/owner_visit_requests_flow_test.dart), [notifications](apps/sokoun_app/test/notification_flow_test.dart), and [profile/settings/support](apps/sokoun_app/test/profile_settings_support_test.dart), alongside other tests.

These definitions help identify intended edge cases. Their existence does not prove all features passed in the reviewed working tree, that a backend is deployed, or that a customer journey works end to end. Application tests were not rerun for this documentation-only change.

This file should be updated when commercial policies are approved, proposed services are confirmed, or implemented behavior changes. Its business facts are bounded by the repository snapshot reviewed on 6 October 2026.
