# Sukoon product context

<!-- impeccable:product-schema 1 -->

## Platform

web

## Scope

This record covers the existing Sukoon public website and its Arabic administration workspace. The current redesign is limited to the admin workspace in frontend/landing; public landing content and mobile applications are outside the change.

## Product Purpose

Sukoon is a real-estate platform connecting landlords and tenants. Its administration workspace manages property listings, identity verification, user accounts, reports, support, revenue, notifications, and platform settings. These capabilities are evidenced by the existing routes and API clients.

## Users

Administrators and staff reviewing and operating the platform. Their exact staffing structure and usage frequency are open questions; daily operational review is the working assumption for this redesign.

## Capabilities and Constraints

Preserve all existing routes, API integrations, authorization behavior, and Arabic RTL support. The combined Next.js app serves the dashboard under /admin and the public website under localized routes. Mock mode already exists; demonstration data must be identified as demonstration data. Do not invent platform statistics, online status, successful exports, or completed staff invitations.

## Brand Commitments

The user explicitly requested the landing page as the main design reference. Preserve Sukoon branding and its warm paper / forest-green identity. The user has now requested a whole-dashboard redesign and regrouping of categories, using Frontend Design and Impeccable guidance.

## Evidence on Hand

Existing routes: frontend/landing/src/app/(admin)/admin. API definitions: frontend/landing/src/lib/api. Brand logo: frontend/landing/src/assets/brand/logo.png. Landing identity: frontend/landing/src/app/globals.css and the landing sections. Existing example datasets: frontend/landing/src/data/mock.

## Product Principles

Keep important operational work easy to find. Group navigation by staff workflow. Preserve factual data and clear failure states. Support keyboard access, mobile layouts, and RTL reading. Distinguish real data from demonstration data.

## Open Decisions

The user was asked whether the home should prioritize operations or executive reporting and whether to retain the landing palette. No answer has arrived; operations and the previously requested landing palette are the stated working defaults for this session, not permanent user preferences.
