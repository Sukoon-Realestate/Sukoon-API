# Postman Testing Guide: Real-Time Chat & Messaging

This guide explains how to test both the **REST API** and **real-time WebSockets** in Postman for **Sukoon-API**.

---

## 1. Start the ASGI Server

Django Channels requires an ASGI server (Uvicorn). Start it locally:

```bash
pipenv run uvicorn config.asgi:application --reload --host 127.0.0.1 --port 8000
```

> [!NOTE]
> Plain `python manage.py runserver` only handles HTTP. To test WebSockets (`ws://`), you must run Uvicorn.

---

## 2. Import the Postman Collection

1. Open Postman.
2. Click **Import** (top left).
3. Select the file:
   `docs/postman/Sukoon_Chat_Messaging.postman_collection.json`
4. The collection **Sukoon API - Chat & Messaging** will appear in your workspace with predefined variables:
   - `baseUrl`: `http://127.0.0.1:8000`
   - `wsUrl`: `ws://127.0.0.1:8000`
   - `userA_email`: `user@example.com`
   - `userB_email`: `owner@example.com`

---

## 3. Testing the REST API Flow

Run the requests in the collection in numerical order:

### Folder `01 - Authentication`
1. **`01 - Login User A`**: Logs in User A. Postman retains the `access` cookie and automatically extracts `accessToken` into a collection variable for WebSockets.
2. **`02 - Login User B`**: Authenticates User B.
3. **`03 - Get User B Profile`**: Retrieves User B's profile and saves their user UUID into `{{userB_id}}`.
4. **`04 - Re-login User A`**: Switches active session back to User A.

### Folder `02 - REST Conversations`
1. **`01 - Create or Get Direct Conversation`**:
   - `POST /api/v1/chat/conversations/create/`
   - Body: `{"user_id": "{{userB_id}}"}`
   - Creates or returns the 1:1 conversation between User A and User B. Automatically sets `{{conversationId}}`.
2. **`02 - List Conversations`**:
   - `GET /api/v1/chat/conversations/`
   - Returns paginated conversations with `other_participant`, `last_message_preview`, `unread_count`, etc.
3. **`03 - Send Message (REST fallback)`**:
   - `POST /api/v1/chat/conversations/{{conversationId}}/messages/create/`
   - Body: `{"content": "Hello from Postman REST!"}`
   - Returns HTTP 201 with the created message and dispatches WebSocket broadcast.
4. **`04 - Get Message History`**:
   - `GET /api/v1/chat/conversations/{{conversationId}}/messages/`
   - Returns message history ordered oldest-first.
5. **`05 - Mark Conversation Read`**:
   - `POST /api/v1/chat/conversations/{{conversationId}}/read/`
   - Resets unread counter for the requesting user and broadcasts read receipt.

---

## 4. Testing WebSockets in Postman

Postman includes native WebSocket support:

### Step 1: Open a WebSocket Request Tab
1. In Postman, click **New** -> **WebSocket** (or the `+` icon and select **WebSocket Request**).
2. Enter the connection URL:
   ```
   ws://127.0.0.1:8000/ws/chat/?token=<YOUR_ACCESS_TOKEN>
   ```
   *(If using collection variables, you can reference `{{wsUrl}}/ws/chat/?token={{accessToken}}`)*.
3. Click **Connect**.
4. The status badge will turn **green ("Connected")**.

> [!TIP]
> If you connect without a valid token, the connection will be immediately rejected with close code `4401` (Unauthenticated).

---

### Step 2: Send a Message Over WebSocket

In the **Message** box at the bottom of the WebSocket tab:
1. Select **JSON** format.
2. Paste the message payload (replace `<CONVERSATION_UUID>` with your conversation ID):
   ```json
   {
     "type": "message.send",
     "conversation_id": "<CONVERSATION_UUID>",
     "content": "Hello real-time WebSocket from Postman!"
   }
   ```
3. Click **Send**.
4. In the **Messages log**, you will see:
   - Outbound frame (`message.send`)
   - Inbound frame received from server:
     ```json
     {
       "type": "message.new",
       "payload": {
         "id": "...",
         "conversation": 1,
         "sender": {
           "id": "...",
           "full_name": "Test User",
           "email": "user@example.com",
           "avatar_url": "",
           "is_online": true
         },
         "content": "Hello real-time WebSocket from Postman!",
         "created_at": "2026-09-15T02:25:00Z"
       }
     }
     ```

---

### Step 3: Send a Read Receipt Over WebSocket

Paste:
```json
{
  "type": "message.read",
  "conversation_id": "<CONVERSATION_UUID>"
}
```
Click **Send**. This marks the conversation as read and pushes a `message.read` notification to other connected participants.

---

### Step 4: Two-Way Live Chat Test (Simulating 2 Users)

1. **Tab 1 (User A)**:
   - Connect to `ws://127.0.0.1:8000/ws/chat/?token=<USER_A_TOKEN>`
2. **Tab 2 (User B)**:
   - Connect to `ws://127.0.0.1:8000/ws/chat/?token=<USER_B_TOKEN>`
3. In **Tab 1**, send:
   ```json
   {
     "type": "message.send",
     "conversation_id": "<CONVERSATION_UUID>",
     "content": "Hi User B! Can you see this instantly?"
   }
   ```
4. Look at **Tab 2**:
   - Tab 2 will instantly receive `{"type": "message.new", "payload": ...}` in real time over its personal channel group!
5. In **Tab 2**, send:
   ```json
   {
     "type": "message.read",
     "conversation_id": "<CONVERSATION_UUID>"
   }
   ```
6. Look at **Tab 1**:
   - Tab 1 will receive `{"type": "message.read", "payload": {"conversation_id": "...", "reader_id": "<USER_B_ID>"}}`!
