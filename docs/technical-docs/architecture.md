---
title: Architecture
parent: Technical Docs
nav_order: 1
---

{: .label }
[Jane Dane]

{: .no_toc }
# Architecture

{: .attention }
> This page describes how the application is structured and how important parts of the app work. It should give a new-joiner sufficient technical knowledge for contributing to the codebase.
> 
> See [this blog post](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html) for an explanation of the concept and these examples:
>
> + <https://github.com/rust-lang/rust-analyzer/blob/master/docs/dev/architecture.md>
> + <https://github.com/Uriopass/Egregoria/blob/master/ARCHITECTURE.md>
> + <https://github.com/davish/obsidian-full-calendar/blob/main/src/README.md>
> 
> For structural and behavioral illustration, you might want to leverage [Mermaid](../ui-components.md), e.g., by charting common [C4](https://c4model.com/) or [UML](https://www.omg.org/spec/UML) diagrams.
> 
>
> You may delete this `attention` box.

<details open markdown="block">
{: .text-delta }
<summary>Table of contents</summary>
+ ToC
{: toc }
</details>

## Overview

Backpacker Rent ist eine webbasierte Ausleihplattform, über die Nutzer:innen physische Gegenstände – wie Zelte, technische Geräte oder andere Outdoor-Produkte – temporär vermieten und ausleihen können. Die Plattform richtet sich insbesondere an reisende oder minimalistisch lebende Nutzergruppen, die funktionale Dinge für begrenzte Zeit benötigen, ohne sie dauerhaft zu besitzen.

Das System basiert auf einer relationalen Datenbankstruktur mit sauberer Entkopplung von Nutzerdaten, Angeboten, Kategorien, Regionen und buchbaren Zeitfenstern. Registrierte Nutzer:innen können Angebote erstellen, inklusive Beschreibung, Preis, Foto und optionalen Features (z. B. "wasserdicht", "für 2 Personen"). Weitere Nutzer können diese Angebote durchsuchen und für bestimmte Zeiträume buchen. Die App prüft dabei automatisch, ob ein Angebot im gewählten Zeitraum bereits gebucht wurde.

## Codemap

Die Anwendung basiert auf **Flask** und folgt einem klassischen MVC-ähnlichen Muster:

- **app.py**  
  Enthält alle Routen, Controller-Logik und die App-Initialisierung. Hier wird die App konfiguriert, CSRF-Schutz aktiviert und das Zusammenspiel zwischen Frontend (Templates) und Backend gesteuert.
  
- **db.py**  
  Stellt die Verbindung zur SQLite-Datenbank her und enthält Funktionen zur Initialisierung und zum Zugriff (z. B. `get_db_con`, `init_app`).

- **templates/**  
  Beinhaltet alle Jinja2-Templates, die für die dynamische HTML-Generierung verwendet werden (z. B. `home.html`, `profil.html`, `angebot_erstellen.html`).

- **static/**  
  Speichert statische Ressourcen wie hochgeladene Bilder (`/uploads`), CSS-Dateien und JS-Dateien (falls nötig).

- **forms.py**  
  Enthält Flask-WTF Formulare wie das `EditProfileForm`, das Validierung und Formlogik kapselt.

## Cross-cutting concerns

Einige wichtige technische Aspekte für das Verständnis der Codebasis:

- **Sicherheitsmechanismen**
  - CSRF-Schutz wird über `Flask-WTF` sichergestellt.
  - Passwörter werden mit `werkzeug.security` gehasht (z. B. `generate_password_hash`, `check_password_hash`).
  - Sitzungen werden über Flask-Session verwaltet; sensible Aktionen prüfen die Session (z. B. `if "user_id" not in session`).

- **Validierung und Fehlerbehandlung**
  - Routen validieren Eingaben streng (z. B. Datumskonsistenz bei Buchungen).
  - Buchungs-Logik prüft immer auf Terminüberschneidungen mit bestehenden Rentals.
  - Viele Aktionen (z. B. Angebote löschen/bearbeiten) sind zusätzlich gegen Missbrauch durch ID-Prüfungen geschützt (z. B. nur der Eigentümer darf löschen).

-**Datenmodell**
  - Die Datenbank folgt einer klaren Normalisierung:
    - `users` enthält Nutzerdaten mit Region-Relation.
    - `offers` verknüpft Angebote mit User, Kategorie, Region.
    - `features` + `offer_features` bilden eine n:m-Relation, um Angebote flexibel zu erweitern.
    - `rentals` hält alle Buchungen inkl. Start-/Enddatum und Gesamtpreis.
    - `category` speichert die verschiedenen Angebotskategorien und dient als Basis für Features.
    - `region` enthält die geografischen Gebiete, denen Nutzer und Angebote zugeordnet sind.


- **Warenkorb-Mechanismus**
  - Der Warenkorb wird session-basiert gespeichert, ohne persistente Speicherung in der Datenbank.
  - Die Mietlogik prüft beim Checkout die Verfügbarkeit aller Artikel erneut.

