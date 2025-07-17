---
title: Design Decisions
nav_order: 3
---

{: .label }
[Backpacker Rent Team]

{: .no_toc }
# Design decisions

<details open markdown="block">
{: .text-delta }
<summary>Table of contents</summary>
+ ToC
{: toc }
</details>

## 01: Datenmodellierung mit relationaler DB + Feature-Zuordnung

### Meta

Status  
: **Decided**

Updated  
: 26-Jun-2025

### Problem statement

Wie sollen Angebote (Offers) und deren dynamische Eigenschaften (Features) strukturiert werden, sodass neue Kategorien und deren spezifische Merkmale flexibel erweiterbar bleiben?  
Ziel: Vermeidung redundanter Spalten, gute Erweiterbarkeit (z. B. neue Kategorien + neue Features).

### Decision

Wir haben uns entschieden, eine relationale Datenbankstruktur mit separaten Tabellen für `offers`, `features` und einer Verknüpfungstabelle `offer_features` zu nutzen.  
Dadurch bleiben wir flexibel bei neuen Kategorien und Features, und die Daten bleiben sauber normalisiert.  

*Decision was taken by:* team/backpackerrent

### Regarded options

| Criterion | Eigene Spalten je Kategorie | JSON-Feld in `offers` | **Separate Features-Tabelle + Verknüpfung** |
| --- | --- | --- | --- |
| **Flexibilität** | ❌ Neue Spalten nötig | ✔️ Dynamisch | ✔️ Dynamisch | <!-- https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-tables -->
| **SQL-Filterbarkeit** | ✔️ Einfach | ❌ Komplex (nur JSON-Funktionen) | ✔️ Einfach |
| **Erweiterbarkeit** | ❌ Schema-Änderung nötig | ✔️ Ohne Schema-Änderung | ✔️ Ohne Schema-Änderung |
| **Komplexität** | ✔️ Einfach | ❔ Mittel | ❌ Höher (mehr Tabellen) |

---

## 02: Authentifizierung mit Session-basiertem Login statt Tokens

### Meta

Status  
: **Decided**

Updated  
: 26-Jun-2025

### Problem statement

Wie sollen Nutzer authentifiziert bleiben, um eine Session zwischen Anfragen sicher aufrechtzuerhalten (z. B. beim Mieten, im Profil)?  
Ziel: Einfache Umsetzung für Web-Umgebung, ohne komplexe Token-Logik.

### Decision

Wir nutzen serverseitig gespeicherte Session-Daten mit dem Flask-Session-Mechanismus.  
Dadurch wird die Authentifizierung einfach umgesetzt, ohne dass komplexe Token- oder API-Logik erforderlich ist.

*Decision was taken by:* team/backpackerrent

### Regarded options

| Criterion | **Session (gewählt)** | Token (z. B. JWT) |
| --- | --- | --- |
| **Einfachheit** | ✔️ Einfach zu implementieren | ❌ Komplexer (Token-Handling, Blacklist) |
| **API-Tauglichkeit** | ❌ Nicht geeignet für reine API | ✔️ Gut für APIs |
| **Security (CSRF)** | ✔️ CSRF-Schutz nativ machbar | ❔ Eigene Maßnahmen nötig |
| **Overhead** | ✔️ Kein Overhead | ❌ Mehr Aufwand im Backend + Frontend |

---

## 03: Filterung von Angeboten in SQL statt in Python

### Meta

Status  
: **Decided**

Updated  
: 26-Jun-2025

### Problem statement

Sollen Angebotsfilter (Preis, Kategorie, Region, Verfügbarkeit) in SQL oder nachträglich im Python-Backend umgesetzt werden?  
Ziel: Effiziente Filterung auch bei großen Datenmengen.

### Decision

Die Filterlogik wird direkt in SQL umgesetzt.  
So wird nur die benötigte Datenmenge überhaupt vom DB-Server an das Backend übergeben, was die Performance verbessert.

*Decision was taken by:* team/backpackerrent

### Regarded options

| Criterion | **SQL-Filterung (gewählt)** | Python-Filterung |
| --- | --- | --- |
| **Performance** | ✔️ DB-seitig effizient, nutzt Indexe | ❌ Hoher Overhead im Backend |
| **Komplexität** | ❔ Komplexere SQL-Statements | ✔️ Einfacher Python-Code |
| **Wartbarkeit** | ✔️ Queries direkt filternd | ❌ Schwer nachzuvollziehen bei größerem Datenvolumen |

---

## 04: Verwendung von Flask-WTF für Formulare

### Meta

Status  
: **Decided**

Updated  
: 26-Jun-2025

### Problem statement

Wie sollen Formulare validiert und gegen CSRF abgesichert werden? Ziel: Wenig Boilerplate, saubere Validierung, integrierter CSRF-Schutz.

### Decision

Wir verwenden Flask-WTF + WTForms, um deklarativ Formulare zu definieren und serverseitig validieren zu lassen, inklusive CSRF-Absicherung.

*Decision was taken by:* team/backpackerrent

### Regarded options

| Criterion | **Flask-WTF (gewählt)** | Plain HTML + eigene Prüfung |
| --- | --- | --- |
| **Sicherheit** | ✔️ CSRF-Schutz integriert | ❌ Muss selbst implementiert werden |
| **Wartbarkeit** | ✔️ DRY, klar strukturiert | ❌ Viel redundanter Code |
| **Flexibilität** | ✔️ Viele Features, einfach erweiterbar | ❔ Volle Freiheit, aber mehr Aufwand |

---

## 05: Passwort-Hashing mit Werkzeug statt Klartext

### Meta

**Status**  
: **Decided**

**Updated**  
: 02-Jul-2025

---

### Problem statement

Wie sollen Passwörter von Benutzer*innen gespeichert werden?  
Ziel ist es, sichere Authentifizierung zu gewährleisten und Sicherheitslücken zu vermeiden, z. B. bei Datenbank-Leaks.

---

### Decision

Statt Passwörter im Klartext zu speichern, werden sie beim Registrieren mit `generate_password_hash()` (aus `werkzeug.security`) gehasht.  
Beim Login wird das eingegebene Passwort mit `check_password_hash()` validiert.  
Dadurch erfüllen wir aktuelle Sicherheitsstandards und sind gegen viele gängige Angriffe geschützt (z. B. Credential Dumps oder SQL Leaks).

*Decision was taken by:* team/backpackerrent

---

### Regarded options

| Criterion             | **Hashing mit Werkzeug (gewählt)** | Klartextspeicherung       |
|-----------------------|-------------------------------------|---------------------------|
| **Sicherheit**         | ✔️ Sehr hoch                        | ❌ Kritisch unsicher       |
| **Brute-Force-Schutz** | ✔️ Ja, Hash-Verfahren ist langsam   | ❌ Keine Verteidigung      |
| **Best Practice**      | ✔️ Ja (Industriestandard)           | ❌ Veraltet / unsicher     |
| **Implementierungsaufwand** | ✔️ Minimal                    | ✔️ Minimal                 |

---

## 06: Direkter Checkout mit „Sofort-Mieten“ 

### Meta

Status: **Decided**

Updated  
:21-Jun-2025

### Problem statement

Wie können wir Nutzern ermöglichen, Angebote direkt zu buchen, ohne den Umweg über den Warenkorb zu gehen, insbesondere wenn sie nur ein einzelnes Produkt mieten möchten?

Ziel:

- Verkürzung des Checkout-Prozesses für Einzelnutzer
- Beibehaltung der Möglichkeit, mehrere Produkte gleichzeitig zu buchen (über den Warenkorb)
- Verbesserung der Nutzererfahrung durch flexible Buchungsoptionen

### Decision

Wir haben uns entschieden, einen „Sofort-Mieten“-Button in der offer_detail.html anzubieten, der Nutzer direkt zur rental_form.html weiterleitet, um die Buchung sofort abzuschließen, ohne den Warenkorb zu nutzen.

Gleichzeitig bleibt der „In den Warenkorb“-Button bestehen, damit Nutzer weiterhin mehrere Produkte sammeln und gemeinsam buchen können.

Dadurch bieten wir beiden Nutzertypen (sofort buchen vs. sammeln) eine passende Lösung und halten unseren Checkout-Prozess flexibel und effizient.

Decision was taken by: team/backpackerrent

### Regarded options

| Criterion | Nur Warenkorb | Nur Sofort-Mieten | Beide Optionen (Warenkorb und Sofort-Mieten) |
|---|---|---|---|
| **Usability** | ❌ Umständlich für Einzelbuchung | ❌ Kein Sammeln möglich | ✔️ Flexibel für beide Nutzergruppen |
| **Implementierungsaufwand** | ✔️ Einfach | ✔️ Einfach | ❌ Mittel (Routing und Logik für beide Pfade) |
| **Flexibilität** | ✔️ Sammelbuchung + Einzelbuchung möglich | ❌ Nur Einzelbuchung | ✔️ Beides möglich |

---

## 07: Datumsauswahl direkt im Rental Form

### Meta

Status: **Decided**

Updated  
: 01-Jul-2025

### Problem statement  
Wie ermöglichen wir es Nutzern, das Mietdatum individuell und spontan direkt beim Buchungsprozess anzupassen, ohne:

- zurück zur Angebotsseite oder Warenkorb navigieren zu müssen,
- die Seite neu aufzuschlagen,
- den Buchungsfluss zu unterbrechen?

Ziel:

- Verbesserte Nutzerfreundlichkeit, indem Nutzer das Start- und Enddatum direkt im Buchungsformular (rental_form.html) ändern können.
- Reduktion von Frustration durch unnötige Navigation.
- Flexibilität bei kurzfristigen Planänderungen.

### Decision  
Wir haben uns entschieden, zwei Datumseingabefelder (Startdatum und Enddatum) direkt im rental_form.html zu integrieren, sodass Nutzer vor der Preisberechnung und Buchung das gewünschte Datum anpassen können.

Dies ermöglicht es Nutzern, den Buchungszeitraum spontan zu ändern, ohne:

- die Angebotsübersicht erneut aufrufen zu müssen,
- den Warenkorb anzupassen,
- den Buchungsprozess zu verlassen.

Decision was taken by: team/backpackerrent

### Regarded options

| Criterion | Datum vorher wählen | Datum im Rental Form (gewählt) |
|---|---|---|
| **Usability** | ❌ Nutzer muss zurück navigieren, wenn sich der Zeitraum ändert | ✔️ Nutzer kann Datum direkt im Buchungsprozess ändern |
| **Flexibilität** | ❌ Datum ist fix und muss im Warenkorb oder Detail erneut angepasst werden | ✔️ Spontane Planänderung möglich ohne Navigation |
| **Implementierungsaufwand** | ✔️ Einfach, da Datum fix übergeben wird | ✔️ Einfach, nur zwei Felder im Template erforderlich |
| **Flow-Unterbrechung** | ❌ Hoch (erneutes Laden oder Navigieren nötig) | ✔️ Keine Unterbrechung, direkt im Prozess anpassbar |

---

## 08: Gebuchte und erstellte Angebote im Profil anzeigen

### Meta

Status: **Decided**

Updated  
: 21-Jun-2025

### Problem statement  
Nach einer Buchung/Erstellung benötigen Nutzer einen klaren Ort, an dem sie ihre Angebote jederzeit einsehen können, um:

- den Überblick zu behalten, welche Produkte sie wann gebucht haben,
- ihre Ausgaben nachzuverfolgen,
- evl. eigene Angebote anzupassen

Ziel:

- Nutzerfreundlichkeit durch eine transparente Übersicht über eigene Buchungen
- Vermeidung von Verwirrung und Unsicherheit, ob eine Buchung erfolgreich war
- Zentrale Verwaltung aller Buchungen innerhalb des Profils

### Decision  
Wir haben uns entschieden, im Profilbereich eine eigene Kategorie „Gebuchte Angebote“ (section="booked") + „Eigene Angebote“ (section="own") einzurichten, in der Nutzer alle ihre Produkte inkl. Titel, Buchungszeitraum und Gesamtpreis bzw. Titel, Kategorie, Region und den Preis sehen können.

Dazu nutzen wir das bereits bestehende profil.html-Template, erweitern dieses jedoch um eine dynamische Abfrage des section-Parameters und eine saubere Kartenansicht für gebuchte/erstellte Angebote.

Decision was taken by: team/backpackerrent

### Regarded options

| Criterion | Keine Übersicht im Profil | Übersicht „Gebuchte Angebote“ im Profil (gewählt) |
|---|---|---|
| **Usability** | ❌ Nutzer muss Buchungen anderweitig prüfen | ✔️ Nutzer sieht alle Buchungen direkt im Profil |
| **Transparenz** | ❌ Keine Einsicht in Buchungshistorie | ✔️ Vollständige Übersicht über Buchungen vorhanden |
| **Implementierungsaufwand** | ✔️ Kein Aufwand | ✔️ Einfach durch Erweiterung der bestehenden Profilseite |
| **Planbarkeit** | ❌ Nutzer kann keine Planungen auf Basis von Buchungen vornehmen | ✔️ Nutzer kann geplante Zeiträume nachvollziehen |
