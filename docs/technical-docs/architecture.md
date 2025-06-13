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

Das System basiert auf einer relationalen Datenbankstruktur mit sauberer Entkopplung von Nutzerdaten, Angeboten, Kategorien, Regionen und buchbaren Zeitfenstern. Registrierte Nutzer:innen können Angebote erstellen, inklusive Beschreibung, Preis, Foto und optionalen Features (z. B. "wasserdicht", "für 2 Personen"). Weitere Nutzer:innen können diese Angebote durchsuchen und für bestimmte Zeiträume buchen. Die App prüft dabei automatisch, ob ein Angebot im gewählten Zeitraum bereits gebucht wurde.

## Codemap

[Describe how your app is structured. Don't aim for completeness, rather describe *just* the most important parts.]

## Cross-cutting concerns

[Describe anything that is important for a solid understanding of your codebase. Most likely, you want to explain the behavior of (parts of) your application. In this section, you may also link to important [design decisions](../design-decisions.md).]
