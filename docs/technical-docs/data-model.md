---
title: Data Model
parent: Technical Docs
nav_order: 2
---

{: .label }
[Jane Dane]

{: .no_toc }
# Data model

<details open markdown="block">
{: .text-delta }
<summary>Table of contents</summary>
+ ToC
{: toc }
</details>

![Datenmodell Backpacker Rent](/assets/images/Datamodel_BackpackerRent.png)

In der aktuellen Datenbankstruktur bilden die Tabellen users und offers das Grundgerüst eines Systems zur Verwaltung und Vermietung von Produkten. Ziel ist es, eine Plattform bereitzustellen, auf der Nutzer verschiedene Gegenstände zur Miete anbieten können, zum Beispiel Zelte, technische Geräte oder andere physische Produkte.

Die users-Tabelle verwaltet alle registrierten Benutzer. Für jede Person werden der Vorname, Nachname, die E-Mail-Adresse, ein verschlüsseltes Passwort, die zugehörige Region sowie verbindlich auch eine Telefonnummer gespeichert. Diese Informationen sind notwendig, um Nutzer eindeutig zu identifizieren und eine sichere Kommunikation zwischen Mietenden und Vermietenden zu ermöglichen. Jede E-Mail-Adresse muss dabei eindeutig sein, um Dopplungen im System zu verhindern.

Die offers-Tabelle speichert die einzelnen Produktangebote, die von den Benutzern eingestellt werden. Ein Angebot enthält Angaben wie den Titel, die zugehörige Kategorie, eine Beschreibung, die Region, den Preis pro Nacht sowie optional ein Foto, das per Dateipfad eingebunden wird. Zusätzlich gibt es ein Feld für dynamische Produktmerkmale (features) im JSON-Format. Jedes Angebot erhält außerdem eine Bewertung (z. B. durch Nutzerfeedback) und einen automatisch generierten Zeitstempel, der die Erstellung dokumentiert.

Aktuell besteht noch keine direkte Verknüpfung zwischen Angeboten und ihren Erstellern. Um dies langfristig sauber abzubilden, wäre es sinnvoll, die offers-Tabelle um ein Feld user_id zu erweitern, das als Fremdschlüssel auf die users-Tabelle verweist. Damit ließe sich eindeutig festhalten, welcher Benutzer welches Produkt anbietet. Eine 1:n-Beziehung, wie sie in solchen Systemen üblich ist.

Darüber hinaus ist bereits angedacht, künftig eine weitere Tabelle für Buchungen zu integrieren. Diese soll erfassen, welcher Nutzer welches Produkt für welchen Zeitraum und zu welchem Preis gebucht hat. Auch wenn diese Buchungstabelle aktuell noch nicht umgesetzt ist, ist sie ein zentraler Bestandteil der geplanten Funktionalität und wird in einem nächsten Schritt ergänzt werden.