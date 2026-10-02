# Carmageddon Dethrace Modernizer

Dieses Projekt von **Bratwurstmensch** soll das originale **Carmageddon** und **Splat Pack** auf Basis von [Dethrace](https://github.com/dethrace-labs/dethrace) komfortabler nutzbar machen.

Ziel ist langfristig ein nachvollziehbares Modernizer-/Installer-Paket mit:

- getestetem 16:9-Pfad,
- zentrierten Menüs und Videos,
- korrigierten Mauskoordinaten,
- zentrierten Bonus-, Checkpoint-, Countdown- und Rennmeldungen,
- optionaler XInput-Unterstützung,
- sowie einer lokalen Integration legal vorhandener deutscher Spieldaten.

**Originale Carmageddon-Spieldaten werden nicht mitgeliefert.**

## Stand

Der intern getestete **v1.5-Prototyp** für 16:9 und XInput funktioniert mit Hauptspiel und Splat Pack.

Die gepatchte EXE wird hier zunächst **nicht** veröffentlicht. Der nächste Schritt ist, die bestätigten Änderungen als reproduzierbare Source-Änderungen an Dethrace und/oder als sauberen Installer abzubilden.

Die technischen Details stehen in [docs/TECHNICAL.md](docs/TECHNICAL.md).

## Deutsche Version

Die deutsche Integration ist ein Projektziel. Öffentlich soll keine Sammlung originaler deutscher Spieldateien verteilt werden. Stattdessen soll ein zukünftiger Installer vorhandene, legal erworbene deutsche Daten erkennen und lokal übernehmen bzw. patchen.

## Credits

Das Projekt baut auf Dethrace auf. Die 16:9-Untersuchung, die Patches, das Packaging und die Controller-Werkzeuge wurden von **Bratwurstmensch** mit umfangreicher Unterstützung durch **ChatGPT von OpenAI** entwickelt.

Weitere Hinweise: [docs/CREDITS.md](docs/CREDITS.md).


## Aktueller Validierungsstand

- 16:9-Source-Port gegen Dethrace v0.10.1: validiert
- Hauptspiel: validiert
- Splat Pack: validiert
- Windows-Installer: kompletter Installations- und Deinstallationsdurchlauf erfolgreich getestet
- vorhandene Modernizer-Dateien werden vor dem Überschreiben gesichert und beim Uninstall wiederhergestellt
- normale `dethrace.exe` und originale Spieldaten bleiben unangetastet

**Installer-Meilenstein: validiert.**
