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

## 05: Keine Verwendung von JavaScript für Hauptfunktionen

### Meta

Status  
: **Decided**

Updated  
: 26-Jun-2025

### Problem statement

Sollen Kernfunktionen (z. B. Angebote erstellen/bearbeiten, mieten) auch ohne JavaScript funktionieren?  
Ziel: Barrierefreiheit und Kompatibilität sicherstellen.

### Decision

Die Hauptfunktionen sind vollständig serverseitig umgesetzt. JS wird nur für Komfort-Features (z. B. dynamisches Nachladen von Features) genutzt.  
Dadurch bleibt die Anwendung barrierefrei und funktioniert auch ohne aktiviertes JS.

*Decision was taken by:* team/backpackerrent

### Regarded options

| Criterion | **Server-seitige Umsetzung (gewählt)** | Voll-JavaScript-Lösung |
| --- | --- | --- |
| **Barrierefreiheit** | ✔️ Hohe | ❌ Gering ohne JS |
| **Komplexität** | ✔️ Einfacher | ❌ Komplexere Architektur |
| **User Experience** | ❔ Weniger dynamisch | ✔️ Sehr dynamisch |
