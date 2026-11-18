# Profile verification card

Refined the requested identity card with a 44px tinted shield tile, clear title, compact status pill with the app-green seal badge, and consistent 16px padding/12px gaps. Existing workspace-specific destination and backend status labels remain. Verification badge is gated by isVerified; only the legacy decorative trailing tick is removed from verified text.

90 tests passed: 32 layout variants (RTL/LTR, dark/light, verified/unverified, 1x/2x text, 320/390 widths) plus 58 existing profile checks. Added a height assertion to prevent accidental card expansion under bounded constraints. Arabic light/dark previews rendered; light preview visually inspected. No new navigation, motion or persistence behavior introduced. Physical device review not performed.
