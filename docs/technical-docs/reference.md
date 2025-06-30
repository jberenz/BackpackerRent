---
title: Reference
parent: Technical Docs
nav_order: 3
---

{: .no_toc }
# Reference documentation


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
**Purpose:** Render the home page and display available offers based on optional filters: region, category, price range, type (e.g., backpacker, radtour), and rental period. Filters out offers that are already rented in the specified period.  
**Sample output:** Renders `home.html` with a list of offers, regions, and categories.

---

## Offers

### `angebot_details(offer_id)`
**Route:** `/angebot/<int:offer_id>`  
**Methods:** `GET`  
**Purpose:** Show detail view of an offer with its category, region, and features (including features without values). Returns 404 if not found.  
**Sample output:** Renders `offer_detail.html`.

### `add_offer()`
**Route:** `/angebot_erstellen`  
**Methods:** `GET`, `POST`  
**Purpose:** Allows users to create a new offer. Handles form rendering, input validation, image upload, and inserting data (offer + features) into the database.  
**Sample output:** Renders `angebot_erstellen.html` or redirects to `/`.

### `edit_offer(offer_id)`
**Route:** `/angebot_bearbeiten/<int:offer_id>`  
**Methods:** `GET`, `POST`  
**Purpose:** Edit an existing offer. Loads current data, allows updating offer information, image, and features.  
**Sample output:** Renders `angebot_erstellen.html` or redirects to `/profil`.

### `angebot_loeschen(offer_id)`
**Route:** `/angebot_loeschen/<int:offer_id>`  
**Methods:** `POST`  
**Purpose:** Delete an offer and its features if owned by the logged-in user.  
**Sample output:** Redirects to `/profil?section=own`.

---

## Rentals

### `rental_form(offer_id)`
**Route:** `/mieten/<int:offer_id>`  
**Methods:** `GET`, `POST`  
**Purpose:** Rental form for a specific offer. Calculates price, checks date conflicts, and inserts rental into database if booked.  
**Sample output:** Renders `rental_form.html` or `rental_confirm.html`.

### `mietseite()`
**Route:** `/mieten`  
**Methods:** `GET`, `POST`  
**Purpose:** Rental page for multiple items in the cart. Validates date, checks conflicts, calculates price, and inserts rentals.  
**Sample output:** Renders `rental_form.html` or `rental_confirm.html`.

---

## Authentication

### `anmelden()`
**Route:** `/anmelden`  
**Methods:** `GET`, `POST`  
**Purpose:** Handle user login. Validates credentials and creates session or shows error.  
**Sample output:** Renders `anmelden.html`.

### `registrieren()`
**Route:** `/registrieren`  
**Methods:** `GET`, `POST`  
**Purpose:** User registration. Validates input, hashes password, creates user, redirects to login.  
**Sample output:** Renders `registrieren.html` or redirects to `/anmelden`.

### `logout()`
**Route:** `/logout`  
**Methods:** `GET`  
**Purpose:** Clear session and log user out.  
**Sample output:** Redirects to `/`.

---

## Profile

### `profil()`
**Route:** `/profil`  
**Methods:** `GET`  
**Purpose:** Display user profile, booked rentals, or own offers depending on section parameter.  
**Sample output:** Renders `profil.html`.

### `edit_profile()`
**Route:** `/profil/bearbeiten`  
**Methods:** `GET`, `POST`  
**Purpose:** Allow user to edit profile details and change password.  
**Sample output:** Renders `profile_edit.html`.

---

## Cart

### `add_to_cart(offer_id)`
**Route:** `/add_to_cart/<int:offer_id>`  
**Methods:** `POST`  
**Purpose:** Add an offer to the shopping cart stored in session.  
**Sample output:** Redirects to `/warenkorb`.

### `warenkorb()`
**Route:** `/warenkorb`  
**Methods:** `GET`  
**Purpose:** Show current shopping cart contents.  
**Sample output:** Renders `warenkorb.html`.

### `remove_from_cart(offer_id)`
**Route:** `/remove_from_cart/<int:offer_id>`  
**Methods:** `POST`  
**Purpose:** Remove an offer from the cart.  
**Sample output:** Redirects to `/warenkorb`.

---

## Other

### `features_for_category(category_id)`
**Route:** `/features_for_category/<int:category_id>`  
**Methods:** `GET`  
**Purpose:** Return the features for a selected category.  
**Sample output:** Renders `partials/_features.html`.
