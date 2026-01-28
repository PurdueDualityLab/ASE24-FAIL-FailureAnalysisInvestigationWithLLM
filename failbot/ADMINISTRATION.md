# FailBot Administration Guide

This document outlines how to administrate users and chat history for the FailBot application.

## 1. User Administration

FailBot uses the Django authentication system. All user management is performed through the Django backend.

### Accessing the Admin Interface
1. Ensure the Django server is running:
   ```bash
   docker compose -f local.yml up -d
   ```
2. Navigate to: `http://localhost:8000/admin/`
3. Log in with a superuser account.

### Creating a New Superuser (CLI)
If you need to create an initial administrator account, run the appropriate command for your environment:

**Local Development:**
```bash
docker compose -f local.yml run --rm django python manage.py createsuperuser
```

**Production:**
```bash
docker compose -f production.yml run --rm django python manage.py createsuperuser
```

> **Important:** The Local and Production environments use separate databases. Users created in the local environment **will not** exist in the production environment. You must create necessary accounts (like the superuser) separately in production.

### Creating Regular Users
1. Log in to the **Django Admin** interface.
2. Navigate to **Users** under the **Authentication and Authorization** section.
3. Click **Add User**.
4. Enter the username and password.
5. Once created, you can add details (e.g., email) and permissions.

### Deleting Users
1. In the **Django Admin** -> **Users** list, select the user(s) you wish to delete.
2. Select **Delete selected users** from the action dropdown menu.
3. Click **Go** and confirm the deletion.
   * **Note:** This deletes the user account from the database.

---

## 2. Chat History Administration

### Storage Configuration
The application is configured to store chat history (threads, steps, feedbacks, elements) in the PostgreSQL database, co-located with your Django application data.

*   **Schema Management:** The necessary database tables (`Thread`, `Step`, `User`, `Element`, `Feedback`) are managed via Django migrations. Specifically, migration `0046_chainlit_tables` in the `articles` app handles the creation of these tables.
    *   **Action:** Ensure migrations are always applied on deployment:
        ```bash
        python manage.py migrate
        ```

*   **Enabling Database Storage:** 
    For Chainlit to use these tables instead of the local file system, you **must** set the `CHAINLIT_DB_URI` environment variable in your docker-compose file (or environment).
    ```env
    CHAINLIT_DB_URI="postgresql://<user>:<password>@<host>:5432/<dbname>"
    ```
    *   **Local:** If not set, it defaults to local file storage in `.chainlit/`.
    *   **Production:** This is **required** for persistence.

### Manipulating Chat History

#### Database Administration (SQL)
Since chat history is stored in standard SQL tables, you can manage it using SQL queries via `pgAdmin` or `psql`.

**Common Operations:**

1.  **Delete a User's History:**
    ```sql
    -- Deleting a user from the Chainlit 'User' table (linked to threads)
    DELETE FROM "User" WHERE identifier = 'target_username';
    -- Due to CASCADE constraints defined in the migration, this will automatically 
    -- delete all associated Threads, Steps, and Elements.
    ```

2.  **Delete Specific Threads:**
    ```sql
    DELETE FROM "Thread" WHERE id = 'thread_uuid';
    ```

3.  **Analytics:**
    You can query the `"Feedback"` table to analyze user satisfaction.
    ```sql
    SELECT value, comment, "createdAt" FROM "Feedback" ORDER BY "createdAt" DESC;
    ```

### Deleting a User's Data
When you delete a User from the **Django Admin** interface, it removes their access to the system. However, their **Chat History** (stored in the Chainlit tables) is **NOT** automatically linked to the Django User model by a foreign key constraint (they are loosely coupled by the `identifier` string).

**To fully remove a user:**
1.  **Django:** Delete the user in the Django Admin.
2.  **Chainlit:** Execute the SQL command above to remove their entry from the `"User"` table and cascade delete their chat history.


### Deleting a User's Data
When deleting a user via Django Admin, their **Chat History is NOT automatically deleted** unless a custom link was established in the code. To fully remove a user's footprint:
1. **Delete the User** in Django Admin.
2. **Delete their Chat History** manually using **Method A** (login as them before deleting) or **Method C** (SQL command matching their username/ID).
