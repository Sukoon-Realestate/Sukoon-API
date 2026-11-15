# Favorites unexpected scroll

Reproduced the screenshot's missing page title by scrolling saved properties and switching to favorite chats. The page used AppScaffold's collapsible NestedScrollView around independently scrolling tab views, so the collapsed outer header offset carried into the other tab. The regression test failed before the fix because the app bar had scrolled out of the tree.

Favorites now uses a fixed flat app bar (scrollAppBar: false); the property/chat/group tab bodies remain scrollable, with their existing filters, data, pagination and retained list positions. No forced jump-to-top or data refresh was added.

60 Favorites/card checks passed after the fix, including a regression that scrolls properties, switches to empty favorite chats and checks that the app bar is visible above the tabs, then switches back. Diff whitespace check passed. Physical-device reopen behavior was not reviewed.
