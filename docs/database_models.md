# Database & Models Design

This document details the model specifications and database guidelines for Darak.

## Core Models

### 1. User
Inherits from `AbstractUser` and replaces the username field with email.
- `pkid`: BigAutoField (Internal primary key)
- `id`: UUIDField (Public-facing identifier)
- `email`: EmailField (Unique login identifier)
- `first_name` & `last_name`: CharField

### 2. Profile
One-to-one link to User containing demographic details.
- `gender`: Choice Field (Male/Female)
- `birth_date`: DateField (Nullable)

### 3. ContentView
Generic relation tracking views on any content object.
- `content_type`: ForeignKey to ContentType
- `object_id`: PositiveIntegerField
- `user`: ForeignKey to User (Nullable, set to NULL on deletion)
- `viewer_ip`: GenericIPAddressField
- `last_viewed`: DateTimeField

---

## DB Conventions
- Always inherit from `TimeStampedModel` to gain `created_at` and `updated_at` tracking.
- Do not use `null=True` on string fields; use `blank=True` with empty string default instead.
- Optimize queries using `select_related` and `prefetch_related` to avoid N+1 queries.
