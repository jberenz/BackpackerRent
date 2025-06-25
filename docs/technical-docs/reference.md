---
title: Reference
parent: Technical Docs
nav_order: 3
---

{: .label }
[Jane Dane]

{: .no_toc }
# Reference documentation

{: .attention }
> This page collects internal functions, routes with their functions, and APIs (if any).
> 
> See [Uber](https://developer.uber.com/docs/drivers/references/api) or [PayPal](https://developer.paypal.com/api/rest/) for exemplary high-quality API reference documentation.
>
> You may delete this `attention` box.

<details open markdown="block">
{: .text-delta }
<summary>Table of contents</summary>
+ ToC
{: toc }
</details>

## Home

### `index()`

**Route:** `/`

**Methods:** `GET`

**Purpose:** Render the home page and display available offers based on optional filters: region, category, price range, type (e.g., backpacker, radtour), and rental period. Filters out offers that are already rented in the specified period. The function dynamically limits categories depending on the selected type (e.g., "backpacker" or "radtour").

**Sample output:**

Renders home.html with a list of offers, regions, and categories.

---

## Angebote

### `angebot_details(offer_id)`

**Route:** `/angebot/<int:offer_id>`

**Methods:** `GET`

**Purpose:** Render the detail page for a specific offer. Loads the offer with its category and region, as well as all features of the offer’s category (including features without assigned values). Returns a 404 page if the offer does not exist.

**Sample output:**

![get_lists() sample](../assets/images/fswd-intro_00.png)

---

### `anmelden()`

**Route:** `/anmelden", methods=["GET", "POST"]`

**Methods:** `GET` `POST`

**Purpose:** Handle user login. On GET, render the login form. On POST, validate credentials (email and password). If valid, create a session and redirect to the home page; if invalid, redisplay the form with an error message.

**Sample output:**


---

## [Example, delete this section] Insert sample data

### `registrieren()`

**Route:** `/registrieren", methods=["GET", "POST"]`

**Methods:** `GET` `POST`

**Purpose:** Handle user registration. On GET, render the registration form with available regions. On POST, validate input (region, email uniqueness, etc.), create a new user with hashed password, and store it in the database. Redirects to the login page upon success; otherwise, redisplays the form with error messages.

**Sample output:**

