Please update the existing Sokoon Figma Make project organization.

I want to create a new section next to the existing “Flow Overview” section called:

“Shared Components”

This section should act as a clean reusable library for everything that is used more than once across the app.

Important:
- Do NOT redesign the project from scratch.
- Do NOT change the existing visual style.
- Keep the same Sokoon design system.
- Keep Arabic RTL.
- Keep Tajawal font.
- Keep the same colors, spacing, rounded cards, icons, buttons, inputs, sheets, and screen style.
- This task is mainly about organization, reusable components, shared screens, and cleaner prototype structure.

==================================================
1. CREATE NEW SECTION NEXT TO FLOW OVERVIEW
==================================================

Create a new section/page next to “Flow Overview” called:

“Shared Components”

Inside it, divide the content into two clear sub-sections:

1. Shared Components
2. Shared Screens

Use clear section headers:
- “Shared Components”
- “Shared Screens”

The goal is to keep the project clean and avoid duplicated design logic.

==================================================
2. SHARED COMPONENTS RULE
==================================================

Any UI element that appears in more than one screen should be treated as a shared component.

Rule:
If a component is used in 2 or more screens, move/copy it into the “Shared Components” library.

Examples of shared components:
- Buttons
- Inputs
- Search bars
- Bottom navigation bars
- Top navigation/header bars
- Property cards
- User cards
- Owner cards
- Request cards
- Notification cards
- Chat bubbles
- Status badges
- Verification badges
- Privacy banners
- Warning banners
- Upload cards
- Empty states
- Loading skeletons
- Filter chips
- Category chips
- Tabs
- Metric cards
- Toast messages
- Dropdown fields
- Share buttons
- Favorite buttons
- Form fields
- Map cards
- Amenity chips
- Pricing rows
- Rating rows

Also include any repeated overlay or sheet:
- Bottom sheets
- Action sheets
- Confirmation sheets
- Share sheet
- Delete confirmation sheet
- Logout confirmation sheet
- Filter sheet
- Report / block sheet
- Upload document sheet
- Modal dialogs
- Admin modals

Important:
Sheets and modals are also shared components if they are used more than once.

==================================================
3. SHARED SCREENS RULE
==================================================

Any screen that can be accessed from more than one place should be treated as a shared screen.

Rule:
If a screen has multiple entry points, create a reference copy of it inside:

“Shared Screens”

Examples of shared screens:
- Property Details screen
- Chat Detail screen
- Notification Detail screen
- Visit Request Detail screen
- Profile / More screen if accessed from multiple flows
- Settings screen
- Help Center
- Terms of Service
- About Sokoon
- Privacy & Security
- Verification Status
- Login Required / Visitor Restricted screen
- Share flow / Share bottom sheet screen
- Support Ticket Detail
- Admin User Profile Detail
- Admin Listing Review Detail
- Admin Report Detail

Example:
The Property Details screen can be opened from:
- Tenant Home
- Search Results
- Saved
- Nearby Properties
- Notifications

So it should be listed inside “Shared Screens” as a shared destination.

==================================================
4. HOW TO ORGANIZE THE SHARED SECTION
==================================================

Inside “Shared Components”, group components by type:

A. Navigation
- Tenant Bottom Navigation
- Owner Bottom Navigation
- Admin Sidebar
- Top Header
- Back Header

B. Cards
- Property Card
- Property Mini Card
- User Mini Card
- Owner Card
- Visit Request Card
- Notification Card
- Metric Card
- Support Ticket Card

C. Inputs & Forms
- Text Input
- Password Input
- Email Input
- Number Field
- Dropdown
- Search Bar
- Upload Field
- Map Location Field

D. Badges & Chips
- Verified Badge
- Pending Badge
- Status Badge
- Property Status Chip
- Filter Chip
- Category Chip
- Suitable For Chip
- Amenity Chip

E. Banners
- Privacy Banner
- Chat Restricted Banner
- Warning Banner
- Success Banner
- Visitor Mode Banner

F. Chat Components
- Sent Bubble
- Received Bubble
- Image Message
- Voice Note
- Chat Input Bar
- Attachment Sheet

G. Sheets & Modals
- Share Bottom Sheet
- Filter Bottom Sheet
- Logout Bottom Sheet
- Delete Confirmation
- Report / Block Sheet
- Visit Booking Sheet
- Accept / Reject Request Sheet
- Upload Document State
- Admin Action Modal

H. States
- Empty State
- Loading Skeleton
- Error State
- Success State
- Rejected State
- Pending Review State

Inside “Shared Screens”, group screens by type:

A. Property Shared Screens
- Property Details
- Fullscreen Gallery
- Share Property

B. Communication Shared Screens
- Chat Detail
- Report Conversation
- Attachment Options

C. Account Shared Screens
- Profile
- Settings
- Privacy & Security
- Verification Status
- Terms
- About
- Help Center

D. Request Shared Screens
- Visit Request Detail
- Booking Status
- Request Confirmation

E. Admin Shared Screens
- User Profile Detail
- Listing Review Detail
- Report Detail
- Support Ticket Detail

==================================================
5. DO NOT BREAK EXISTING FLOWS
==================================================

Do not remove the components from existing screens unless it is safe.

The existing screens should still look the same and work the same.

If possible:
- Convert repeated UI into reusable components.
- Use component instances across screens.
- Keep master components inside the “Shared Components” section.

If true component conversion is not possible:
- Create clean reference versions inside the “Shared Components” section.
- Keep the current screens visually unchanged.

For shared screens:
- Do not duplicate multiple versions of the same screen unnecessarily.
- Keep one clean shared version where possible.
- Prototype links from different flows should point to the same shared screen when appropriate.

Example:
Tenant Home property card → Shared Property Details
Saved property card → Shared Property Details
Search Results property card → Shared Property Details
Notification property CTA → Shared Property Details

==================================================
6. ADD USAGE NOTES
==================================================

For each shared component or shared screen, add a small label/note showing where it is used.

Example:

Component:
“Property Card”

Used in:
- Tenant Home
- Search Results
- Saved
- Nearby Properties

Component:
“Privacy Banner”

Used in:
- Chat
- Property Details
- Booking
- Profile
- KYC

Screen:
“Property Details”

Opened from:
- Tenant Home
- Search Results
- Saved
- Notifications
- Nearby Properties

Keep these notes small and clean, like documentation labels.

==================================================
7. NAMING SYSTEM
==================================================

Use clear names.

Shared Components naming examples:
- COMP-NAV-TENANT-BOTTOM
- COMP-NAV-OWNER-BOTTOM
- COMP-CARD-PROPERTY
- COMP-CARD-VISIT-REQUEST
- COMP-BADGE-VERIFIED
- COMP-BANNER-PRIVACY
- COMP-SHEET-SHARE
- COMP-SHEET-FILTER
- COMP-STATE-EMPTY
- COMP-STATE-LOADING

Shared Screens naming examples:
- SHARED-SCREEN-PROPERTY-DETAILS
- SHARED-SCREEN-CHAT-DETAIL
- SHARED-SCREEN-VISIT-REQUEST-DETAIL
- SHARED-SCREEN-HELP-CENTER
- SHARED-SCREEN-TERMS
- SHARED-SCREEN-ABOUT
- SHARED-SCREEN-VERIFICATION-STATUS

==================================================
8. VISUAL PRESENTATION
==================================================

The “Shared Components” section should be organized and clean.

Use:
- Dark or neutral background like the Flow Overview
- Clear section headers
- Spacing between component groups
- Labels above each component
- Small usage notes
- Components displayed in their real visual style

Make it look like a real design system library, not random copied elements.

==================================================
9. FINAL CHECK
==================================================

Before finishing, confirm:

- A new section/page called “Shared Components” exists next to Flow Overview.
- It contains two sub-sections:
  1. Shared Components
  2. Shared Screens
- Any component used in 2 or more screens is included.
- Any sheet/modal used in 2 or more places is included.
- Any screen opened from multiple places is included as a shared screen.
- Existing app flows are not broken.
- Repeated prototype links point to shared screens where appropriate.
- The project is cleaner and easier to understand.
- Arabic RTL is still correct.
- Tajawal font is still used.
- Sokoon visual identity is unchanged.

Final output:
Create a clean shared design system section next to Flow Overview, divided into Shared Components and Shared Screens, containing every repeated component, sheet, modal, and reusable screen used across the Sokoon app.