# Sokoun / سكون — Business overview and latest changes

**Updated:** 7 October 2026.

**Audience:** Product owners, business stakeholders, operations, customer support, marketing and delivery teams.

**Purpose:** Explain what Sokoun does, how its customers use it, what the latest changes mean for the business, and what must be delivered before those changes can become reliable customer services. This is the business companion to [SOKOUN_ALL_FEATURES_BACKEND_HANDOFF.md](SOKOUN_ALL_FEATURES_BACKEND_HANDOFF.md), using [PROJECT_BUSINESS_DETAILS.md](PROJECT_BUSINESS_DETAILS.md) as the earlier project baseline.

## 1. How to read the business status

The project represents a rental discovery and viewing marketplace, with additional tools for managing rental decisions, documents and rent. A screen or business requirement does not establish that the corresponding service is running in production.

| Status used here | Business meaning |
| --- | --- |
| Business rule | A decision described by the current handoff that the application and services must respect. |
| Implemented in the app | Customer screens and client behavior exist; online actions still depend on compatible services. |
| Local capability | Works on the device, such as a private note or an owner draft. It is not publication, cross-device synchronization or a server transaction. |
| Awaiting service delivery | The service behavior is proposed, unverified or requires implementation before the customer action can be enabled reliably. |
| Open business decision | The sources do not settle the policy; product and operations must define it before making a customer promise. |

The baseline was reviewed on 6 October. The updated consolidated handoff describes later changes, including free tools, durable drafts, comparison, real report submission and rental offers. Those later requirements take precedence when the earlier baseline describes a capability as absent. This guide does not independently verify a live backend, a store release, signatures or payments.

## 2. Product, customers and value

Sokoun connects people offering accommodation with people looking for a suitable rental. Its main journey is:

**Owner describes accommodation → platform reviews it → tenant discovers and evaluates it → tenant chooses the accommodation and requests a viewing or contacts the owner → owner responds → both manage the appointment.**

A tenancy, lease and rent obligation require a separate explicit agreement. Accepting a viewing does not complete that agreement.

| Participant | Need | Value offered by the project |
| --- | --- | --- |
| Tenant | Find suitable accommodation and understand the costs before committing | Search, photos/video, clear offer terms, favorites, comparison, communication, viewing tracking and reviews. |
| Owner | Present accommodation clearly and organize rental interest | Property and offer management, drafts, review feedback, requests, viewing schedules, conversations and measured performance. |
| Platform operations | Maintain trustworthy information and respond to problems | Identity/ownership review, property moderation, private support records and consistent permissions; a working operational system is still required. |
| A person who both rents and lists | Use both sides of the marketplace without a second account | One authenticated account with tenant and owner workspaces. |

The current experience is oriented toward Egypt, uses Egyptian pounds, and supports Arabic and English. Arabic layouts run right to left; English layouts run left to right. Launch cities, supply targets and acquisition plans are not established by sample listings.

## 3. Access and the free-feature business decision

All customer tools described in the consolidated handoff are free to use. Promotion, search alerts, analytics, AI assistance, digital lease tools and rent management must not require a subscription, feature purchase, promotion credit or paid token allowance.

**Free tool access does not make rent free.** A tenant may still pay the amount owed on a real, authorized rent invoice. The current handoff approves no feature surcharge, inferred platform commission or verification fee. Examples in old designs do not establish actual commercial terms.

Guest users can browse public tenant discovery and details. Personal actions require authentication. Owner actions apply only to the signed-in owner's resources; tenant actions apply only to their own records. Switching workspace changes the interface and does not grant ownership of another person's data.

Identity rules, moderation, participant permissions, operational limits and availability checks still apply. Free access also does not activate an unsupported service: new rental-offer server operations remain disabled until their contracts are supported and verified.

## 4. The main change: a property and its rental offers are different

Previously, several application flows treated one property as one indivisible rental listing. The new business model separates the physical accommodation from what the owner is actually offering.

| Concept | Business responsibility |
| --- | --- |
| Physical property | Owner, property type, address and location, total bedrooms/bathrooms/area, shared facilities, property photos/video and private ownership evidence. |
| Room | An identifiable room within the property, with its name, capacity and relevant details such as private/shared bathroom access. |
| Bed | An identifiable bed belonging to one identified shared room. |
| Rental offer | The accommodation available for rent, its own price and price period, minimum term, deposit, suitability, rules, description, availability and relevant photos. |

An apartment remains an apartment whether its owner offers the whole apartment, one room or a bed. The existing property-type label “room” must not be used as a substitute for this new distinction.

### 4.1 Supported offering choices

Owners are asked early: **“إيه الجزء اللي حابب تأجّره؟”**

| Choice | Arabic example | What one offer represents |
| --- | --- | --- |
| Entire property | العقار بالكامل / شقة بالكامل | The whole apartment, villa, studio or other property for one price. |
| One room | غرفة داخل شقة | One identified room rented as a whole. |
| Room group | مجموعة غرف مع بعض | Two or more distinct identified rooms rented together for one combined price. |
| Bed | سرير في غرفة مشتركة | One identified bed in one identified shared room. |

Physical room count and offered room count remain separate. A three-bedroom apartment offering two rooms still has three bedrooms, while that offer includes only two.

### 4.2 Examples that must stay distinct

The following are alternative illustrative scenarios, not actual inventory or approved prices. Conflicting scenarios must not be offered simultaneously for the same accommodation.

| Scenario | Offers | Price meaning | Availability meaning |
| --- | --- | --- | --- |
| Entire three-bedroom apartment | One entire-property offer | 8,000 EGP/month for the entire apartment | One whole-property rental availability. |
| Rooms A and B rented together | One room-group offer selecting A and B | 5,000 EGP/month for both rooms together | The group is offered together. |
| Rooms A and B rented separately | Two offers, one for A and one for B | Each room has its own owner-supplied price and terms | Either room can become rented independently. |
| Beds A1 and A2 rented separately | Two bed offers in the same identified shared room | Each bed has its own owner-supplied price | Each bed has independent availability. |

The platform never divides a property's price by its bedroom or bed count to invent an offer price. Room capacity does not establish current occupancy, and other residents' identities must not be exposed.

## 5. The owner journey

1. Sign in, switch to the owner workspace and add or edit a property.
2. Answer the offering question and choose whole-property or partial offering mode.
3. Enter the property's address, location, physical totals and shared facilities once.
4. Supply property photos/video and, where applicable, private ownership evidence.
5. For partial offers, identify rooms and beds, then select exactly what each offer includes.
6. Set each offer's price, price period and rental terms. Add additional independent offers without repeating the property's shared information.
7. Review a summary of the accommodation, shared spaces, price basis and terms.
8. Save the local draft, or submit through a supported server flow once that operation is enabled.
9. Follow property moderation and manage each offer using the server's available actions.

For the whole property, the existing full-property journey remains and its price is clearly the whole-property price. Room and bed journeys disclose only relevant fields. A room group must include at least two distinct actual rooms.

Shared defaults may supply minimum terms, deposit, suitability, description and rules. Individual offers can explicitly inherit or override them. Price and price period belong to each offer. For example, “1,500 EGP per month” and “minimum rental term: three months” are different facts.

Changing offering mode preserves useful draft input and explains affected selections. It does not automatically cancel existing requests, end leases or release accommodation. Unsaved changes and failed saves remain recoverable.

**Current delivery boundary:** the new offering editor supports durable local drafts. With the default configuration, the action is labeled as saving locally and does not publish or claim server persistence. The original property-only creation/editing path remains available. Full new offer publishing requires backend delivery.

## 6. Inventory and independent offer management

For the initial business model, owners choose either the whole property or specific parts. These are mutually exclusive active modes.

| Inventory rule | Business consequence |
| --- | --- |
| A room cannot be in two active room/group offers | An owner cannot offer Room A individually while also including it in an active A+B group. |
| A whole-room offer cannot coexist with bed offers in that room | Choose renting the room as a whole or renting its identifiable beds. |
| One bed cannot be in multiple active offers | Two independently rentable beds require two distinct beds and offers. |
| Whole and partial offers cannot conflict | The same accommodation cannot be offered twice through different scopes. |
| Rented/unavailable offers retain their allocation until an explicit permitted transition | Hiding availability alone does not make the same room or bed available for a conflicting offer. |
| Existing requests and leases constrain changes/archive/deletion | Removing an offer must not remove its property or erase dependent records. |

The application assists with validation, but the server must enforce these rules for ownership and simultaneous updates. Two devices cannot both allocate the same room because they happened to pass local validation.

When a server confirms one independent room or bed as rented, other non-overlapping offers keep their own availability. Property-level moderation may still affect public visibility separately. “Mark rented,” “Make available” and “Archive” are server-backed actions, not local switches or viewing status changes.

## 7. The tenant journey and price transparency

1. Browse Home or search as a guest or signed-in tenant.
2. Filter by physical property type and, when supported, rental scope alongside location, price period, suitability and other existing criteria.
3. Open a grouped property card and inspect the available accommodation.
4. Explicitly choose the room, group, bed or whole-property offer, including when only one offer is shown.
5. Review the selected price/terms, relevant photos, property facts and shared spaces.
6. Sign in for protected actions, save the exact offer or start communication where supported.
7. Choose an available viewing appointment, review the accommodation and current terms again, then send the viewing request.
8. Follow the request, notifications and eligible review actions.

### 7.1 One search result is one physical property

The chosen discovery unit is a grouped property with explicit offer selection inside details. Result counts, page sizes, map markers, comparisons and grouped favorites refer to properties. Offers are shown and counted separately within their parent property.

Cards explain rental scope, physical type/location, offer labels and price basis. If a card says “starting from,” the amount must be the server-confirmed minimum among eligible available offers for the stated price period. Weekly and monthly prices cannot be mixed into a misleading single minimum.

Price filtering and ordering use actual eligible offer prices and a selected price period. “Three property bedrooms” must not imply that a chosen bed offer includes three rooms. Suitability and relevant rules come from the selected offer's effective terms.

### 7.2 Details and favorites preserve the choice

Details separate **“المعروض للإيجار”**, **“تفاصيل العقار”** and **“المرافق والمساحات المشتركة”**. Photos and price information must describe the chosen accommodation. Shared-space photos are identified separately; unrelated bedrooms are not presented as photos of a selected bed.

Offer favorites remember the tenant's exact choice. If that offer becomes rented, archived or unavailable, the saved record remains understandable and must not silently switch to another room. Selecting an alternative is a new explicit tenant choice.

Old property links still open the property, with clear selection when several offers exist. Offer-specific links and review links retain the selected accommodation when supplied. Device link activation still requires deployment configuration and verification.

## 8. Three different states: review, rental and viewing

| State dimension | Question it answers | Example |
| --- | --- | --- |
| Moderation/publication | Has the platform approved this information, and may it appear publicly? | Under review, accepted or rejected; actual public eligibility needs an agreed rule. |
| Rental availability | Is this particular accommodation currently offered for rent? | Available, unavailable, rented; archival is tracked separately. |
| Viewing appointment | What is happening to this appointment request or time slot? | Pending, accepted, rejected, completed or canceled. |

An accepted viewing means the owner agrees to the appointment. It does not mark a bed rented, reduce accommodation inventory, create a lease, generate an invoice or record revenue. Appointment schedules remain property-based; this change introduces no new scheduling engine.

Before an offer viewing request is submitted, current accommodation availability, terms and appointment availability must be rechecked. Changed terms require another review; conflicts retain the tenant's choice and show a useful error. Server permissions continue to decide the allowed request actions.

Historical visits, owner requests, calendars, reviews and related records must retain the selected accommodation and the terms at that event. Renaming a room or changing today's price must not rewrite an earlier request. If historical details were never supplied, the app must explain that they are missing rather than reconstruct them from current values.

## 9. Trust, moderation, media and privacy

Property moderation remains part of the existing submission process. Under the documented contract, owner edits return the property to review. The proposed offer edits, media associations and availability/archive actions currently use that same review policy; any different policy requires explicit agreement.

Accepted moderation status, account identity verification, property verification and ownership verification describe different facts. Operations must settle which combination permits public publication and whether an older accepted version stays visible during re-review. Promotion must not buy verification or bypass this policy.

The submission requirement remains **10–25 unique photos and a required 1–60 second video for the property**. It is not another ten photos and video for every room or bed. Existing relevant photos may be associated with offers when supported, while cover handling, captions and retained photos keep their established behavior.

Ownership evidence and identity documents remain private. Tenants may see a verification result without receiving the private document. Contracts, support attachments and conversations are restricted to authorized users. No resident identity or invented occupancy figure should appear in a shared-room listing.

Current-user identity and permissions must govern communication and booking; a peer's verification badge is not permission for the caller. Phone/address disclosure, document retention and reviewer access require approved policies. Draft or service failure must not appear as successful publication, a delivered complaint or a completed payment.

## 10. Free tools included in the consolidated handoff

The six tools below have implemented client entry points and no purchase gate. Their network-dependent capabilities require compatible deployed services; “free” does not mean “already live.”

| Tool | Business value and normal entry | Service dependency or important boundary |
| --- | --- | --- |
| Listing promotion | Owner property card/action → promote an eligible listing to improve its visibility | Requires real campaign creation/ranking/expiry. No credits, feature charge, guaranteed position or automatic verification. Promotion remains property-based. |
| Search alerts | Tenant Home or saved search/results → receive relevant new matches | Requires persisted criteria and delivery workers. Scope and offer price semantics must match search. Saving a manual search locally does not create an alert. |
| Advanced owner analytics | Owner dashboard or property → understand measured interest and performance | Requires real measurements, periods, definitions and authorized exports. Missing information is unknown, not invented activity or income. |
| AI listing assistance | Owner description section → request a suggestion, review/edit it and apply to the draft | Requires an AI service and consent. It cannot invent facts, publish or verify. Current inputs are property-level; individual-offer assistance needs further agreement and integration. |
| Digital leases and signing | Contracts or an owned property → eligible documents, draft and signing journey | Requires explicit tenancy agreement, eligible parties, approved templates and confirmed signing. New lease creation for offer-based properties remains blocked until a selected-offer contract exists. |
| Rent management and checkout | Tenant Home due-rent preview or a lease's invoices; owner rent-management history | Requires actual authorized invoices and provider-confirmed payments. Tools are free; rent owed is still payable. No owner payout or refund service is implied. |

These tools are reached in their relevant Home, property, search, contract and rent journeys. Duplicate Profile “Sokoun tools” shortcuts have been removed; the existing main workspace tabs remain.

## 11. Other customer and owner improvements

| Capability | Business behavior | Boundary |
| --- | --- | --- |
| Comparison and costs | Compare up to three properties and explicitly selected accommodation; understand known rent/deposit costs | Uses stated terms. Unknown utilities/fees remain unknown; the known subtotal is not a promise of the full move-in cost. |
| Private decision notebook/checklists | Keep personal notes, groups and viewing checks | Local/private. No automatic upload to owners or cross-device synchronization. |
| Manual saved searches | Resume the chosen criteria without re-entering them | Device/account-scoped convenience; automatic alerts are separate server records. |
| Search map and explained matches | Inspect actual coordinates and understand matches to chosen criteria | Current map filtering operates on loaded results. Whole-catalog geographic search, travel times and nearby services require further delivery. |
| Owner draft and upload recovery | Resume fields/media and retry incomplete work | Local recovery preserves confirmed property/media identities. Reliable handling of an ambiguous server response also requires server duplicate prevention. |
| Viewing slots and calendar export | Choose server-provided appointments, review the request and export an accepted appointment | Server scheduling/conflict rules are authoritative. Calendar export is not automatic calendar synchronization. Rescheduling/completion/reminders need agreed lifecycle services. |
| Rejection feedback and listing quality | Correct a rejected submission using actual feedback; inspect useful quality suggestions | Suggestions do not replace moderation or weaken mandatory submission rules. |
| Reviews and reputation | Score cleanliness, listing accuracy and owner interaction after an eligible viewing | Eligibility, uniqueness, moderation and aggregate ratings are server responsibilities. A viewing review is not proof of a completed tenancy. |
| Chat recovery and permissions | Retain recoverable local text drafts/uncertain messages, keep authorized history and respect sending permission | Exact delivery/duplicate prevention requires coordinated server acknowledgements. A reported problem is not an automatic user block. |
| Reports and support | Send a contextual complaint and follow a private case with a real reference/history | Success requires durable server storage. Assignment, escalation and response times require operating policies. |
| Account, settings and notifications | Shared profile, identity/status, language/theme, privacy preferences and event navigation | Settings must reflect supported services; account deletion/financial retention and message disclosure need explicit rules. |

## 12. Communication, notifications and operations

Tenant and owner share account conversations. Starting a conversation identifies the other person; the rental change does not create one chat thread per room or bed. The app can show selected accommodation context in that conversation. Keeping that context permanently in message history requires a supported service extension.

Notifications about viewings, property activity, messages, identity or alerts must identify the correct recipient and destination. Supplied offer context should name the accommodation. A viewing acceptance notification must not say the property has been rented. Notification preferences and device push permission remain separate.

Support references should keep the relevant property/offer/request understandable, subject to authorized access. A support complaint, an account block and a moderation decision are separate outcomes. No support response time or automatic refund is promised here.

The repository includes a marketing website and an administrative design prototype. Website listings are illustrative and store badges do not prove a public launch. The prototype does not establish a working reviewer/support/payment administration system. Public marketing should match enabled services, actual price meanings and confirmed privacy/review policies.

Arabic/English, light/dark appearance, phone/tablet layouts and accessible text scaling remain part of the shared product experience.

## 13. Contracts, invoices and money

| Business item | Meaning |
| --- | --- |
| Asking rent | The owner's offered price for clearly identified accommodation and a stated price period. It is not received revenue. |
| Minimum term | The minimum rental length, recorded separately in months. |
| Deposit | A stated rental term. Describing it does not establish collection, escrow, deductions or refund handling. |
| Viewing request | An appointment; no lease, occupancy allocation or rent obligation is created automatically. |
| Lease | An explicit agreement between authorized eligible parties, identifying the accommodation and agreed terms. |
| Invoice | A real authorized obligation created from approved lease/accounting rules. |
| Payment | A provider-confirmed transaction applied to the correct invoice; opening checkout is not payment completion. |
| Revenue | Actual accounting information with a defined cash/accrual/gross/net basis, not a sum of asking prices or accepted viewings. |

Existing documents and invoices remain readable. Offer-based financial records should preserve their agreed accommodation and historical terms; changing a current offer's price must not change an older invoice. Signing/payment completion requires authoritative service evidence, not returning from a browser.

The current rent checkout journey covers a complete authorized invoice. Partial payments, refund requests, settlement rules and owner payouts require separate approved contracts. No particular provider, commission rate or verification fee is approved by this guide.

## 14. Measures and truthful reporting

| Measure | Required business interpretation |
| --- | --- |
| Property count | Number of physical properties; several offers do not multiply that total. |
| Offer count | Number of distinct rental offers. A two-room group is one offer; two independently offered rooms are two. |
| Search count | Eligible grouped properties for the current criteria, counted before paging. |
| Available offer count | Eligible independently available accommodation; distinguish this from physical property totals. |
| Views/saves/requests | Measured interest with a stated definition and period; they are not completed rentals. |
| Viewing acceptance rate | A measured appointment statistic with an explicit numerator/denominator. |
| Rating/reviews | Server-calculated eligible reputation records; no invented averages or duplicate reviews. |
| Rent due/received | Real authorized obligations and confirmed accounting events, with a stated reporting basis. |

Missing data is unknown; a confirmed zero is zero. The app must not label an asking-price total as income, a viewing as occupancy, or a property count as an offer count. Advanced analysis requires the service to define measurement windows, attribution and exclusions.

## 15. Current delivery position

| Area | Current business position |
| --- | --- |
| Core marketplace | Existing owner/tenant flows remain. Deployment and exact service behavior are not independently established by this document. |
| Local decision tools and owner drafts | Implemented local behavior; these do not require a new cloud service to be useful. |
| New rental scope/inventory editing | Implemented in the app with local draft save/recovery and validation. New server publishing/editing is disabled by default. |
| Offer-aware discovery and context | App models/screens can render supplied offer information and preserve exact selections. New search/favorite/viewing operations require separately supported services and enablement. |
| Offer rental availability/archive | Implemented server-backed client path behind capability and permission gates; local-only occupancy is not simulated. |
| Free promotion/alerts/analytics/AI/lease/rent tools | Client journeys have no payment gate; services/workers/providers need implementation or confirmation. |
| New leases for offer-based properties | Blocked until a contract identifies and validates the exact offer. Rental-operation enablement alone does not remove this block. |
| Historical records | Client reads preserve supplied offer references and event-time terms. The service must create and retain those records correctly. |
| Offer sharing/device links | Selection-aware application routing exists; hosted/native link deployment and real-device verification remain required. |
| Administration, production rollout and providers | Not established by the client repository or prototype. |

Client testing supports the implementation evidence, not service deployment. The consolidated handoff records a 2,997-test full regression run, 48 focused checks after the final review-link adjustment and 216 rental UI layout/language/theme configurations. No live-backend payment, signing, inventory enforcement or device-link completion is claimed.

## 16. Delivery responsibilities and launch acceptance

| Responsibility | Business outcome needed |
| --- | --- |
| Product/business | Approve publication, identity, legacy migration, dependency, privacy and tenancy policies; keep customer promises proportionate to delivery. |
| Backend/services | Persist real records, assign stable identities, validate ownership/conflicts simultaneously, calculate truthful results and retain history/private boundaries. |
| Mobile | Keep the chosen accommodation consistent, show useful reviews/errors, preserve drafts and enable each new operation only after its service is verified. |
| Operations/support | Apply agreed moderation, identity and complaint policies with real authorized tools and durable case handling. |
| Marketing/release | Advertise actual enabled features, accurate prices and verified distribution information. |

The delivery sequence is: confirm the business rules → deliver property/offer identities and conflict rules → deliver eligible public discovery/favorites/viewings/history → validate each supported operation → enable it deliberately → extend leases/other tools where the accommodation must be identified → verify release/device/provider behavior.

The backend team must return [the consolidated handoff's delivery format](SOKOUN_ALL_FEATURES_BACKEND_HANDOFF.md#7-backend-return-file--required-response-format) in `SOKOUN_ALL_FEATURES_BACKEND_DELIVERY.md`, stating actual delivered behavior, evidence and gaps. A route existing or a screen opening is not sufficient acceptance.

Business acceptance must demonstrate the following scenarios:

1. A whole property, one room, a room group and a shared-room bed each have unambiguous identities and price meanings.
2. A three-bedroom property offering two rooms retains both facts; independent rooms/beds have separate prices and availability.
3. Overlapping offers and simultaneous conflicting edits fail without partial allocation or lost owner input.
4. Renting one independent offer leaves other non-overlapping availability unchanged, while respecting property-level publication rules.
5. Search filters, sorting, “starting from,” counts and favorites use eligible actual offers and consistent price periods.
6. A tenant's bed choice survives login, viewing review/confirmation, history, notifications and review/property navigation without becoming the whole property.
7. Viewing acceptance changes only the appointment; no rent, lease, occupancy or revenue is created automatically.
8. Editing/archive/mode changes preserve historical accommodation and event-time terms; dependencies prevent inappropriate removal.
9. Property media requirements apply once, selected photos are relevant, private evidence stays private, and retries do not create duplicate properties/uploads.
10. Unsupported services and failed saves show honest local/disabled/error states rather than success.
11. Old listings/requests/links remain readable, and ambiguous legacy “room” records are not automatically called whole-property offers.
12. Free tools operate without purchases; real signing/payment statuses come from verified service evidence and actual obligations.

## 17. Decisions still needed

| Open area | Business decision or evidence required |
| --- | --- |
| Public publication | Exact review/verification combination, visibility during edits and handling of property-wide re-review. |
| Identity/ownership | Who can list or act, which documents are accepted, when verified identity is mandatory and how review/appeal works. |
| Existing ambiguous inventory | How legacy room/shared listings are classified, how owners confirm them and what older app versions may see. |
| Inventory dependencies | Permitted mode changes, renting/reopening/archive, outstanding requests and active-lease constraints. |
| Appointments/reviews | Slot policy, expiry/no-shows, cancellation, reschedule/completion/reminders and eligible unique reviews. |
| Tenancy and financial operations | Explicit agreement, eligible participants/templates, invoice generation, approved provider/settlement and any future partial-payment/refund process. |
| Privacy/support | Contact/location disclosure, document/history retention, account deletion dependencies, operator access and case escalation/response policy. |
| Offer extensions to other tools | Alert matching/versioning, individual-offer AI assistance, permanent chat context and selected-offer lease creation. |
| Launch | Actual geography, release/store links, service readiness and device/provider integration evidence. |

Any future monetization policy requires a separate business decision. The current approved tool-access policy remains free, with real rent obligations handled separately.

## 18. Source map

| Source | Role in this business guide |
| --- | --- |
| [PROJECT_BUSINESS_DETAILS.md](PROJECT_BUSINESS_DETAILS.md) | Earlier project-wide business baseline, audiences, existing marketplace, account, privacy and operational context. |
| [SOKOUN_ALL_FEATURES_BACKEND_HANDOFF.md](SOKOUN_ALL_FEATURES_BACKEND_HANDOFF.md) | Current consolidated free-tool decisions, customer journeys, rental-offer rules, service responsibilities, delivery requirements and verification boundaries. |
| [Rental offers handoff](docs/rental_offers_backend_handoff.md) | Detailed property/offer relationships, availability/history/media rules, proposed services, legacy migration and staged enablement. |
| [Free improvements](SOKOUN_FREE_IMPROVEMENTS_IMPLEMENTATION.md) | Decision tools, local recovery, media, communication and other improvements consolidated into the current handoff. |
| [Property media/edit/delete handoff](MOBILE_PROPERTY_MEDIA_EDITING_DELETION_HANDOFF.md) | Property-level media, privacy, editing, stable records and dependency-sensitive deletion. |
| [Owner review-status tabs](docs/owner_property_status_tabs_backend.md) | Property moderation filtering/counts and unresolved publication/verification distinctions. |

This document translates the supplied project and handoff into business terms. Technical payloads, routes and release configuration remain in the consolidated handoff; approved legal terms, commercial changes and operational policies require their own authority.
