# Account pages UI cleanup

Cleaned up the four screens supplied by the user:

- Experience preferences: grouped data saving, housing priorities, and eligible sync into quiet settings surfaces; smaller contextual copy; priorities use wrapping chips with numbered selection and existing move-up actions. Consent, activity clearing, suggestion toggles, conditional detail inputs, save and sync conflict resolution remain available.
- Sessions: removed the oversized slogan; grouped account events/support links; consolidated device identity and platform/version; current-session label precedes timestamps; grouped logout actions use clear error color. Original confirmation dialogs, loading guards, revocation, frozen/error feedback, reload and logout ownership remain.
- Suggest improvement/support: removed the duplicate hero heading; compact topic chips and tighter field grouping; shorter initial details field that can grow; attachments, payment context, draft retention, validation, uncertain submission recovery and the original submit footer remain.
- Password change: removed the large slogan and colored policy card; retained intro as quiet text, all three fields, visibility controls, validation, policy text, save footer, dirty guard and logout behavior.

Added optional compact/title-hidden presentation to SokounPageIntro; existing defaults remain. New SokounSettingsSection uses Material so native tile ink feedback remains visible.

Verification: 65 responsive/interaction checks passed (four screens; Arabic/English, dark/light, 320/390 widths, 1x/2x text; priority maximum-three selection, reordering, and deselection). Existing profile settings/support suite passed all 477 checks. Earlier profile, experience and support-recovery checks passed in the combined run; two stale icon-based verification navigation selectors were updated to target their actual card, and the full affected suite was rerun successfully. Analyzer reports the same 12 existing unrelated diagnostics. Formatting and git diff whitespace checks passed.

Arabic previews inspected and saved in output/account-pages-cleanup. Runtime on a physical device, keyboard transitions and frame pacing were not reviewed in this task. No real password, revocation, support submission, consent change or activity clearing was performed.
