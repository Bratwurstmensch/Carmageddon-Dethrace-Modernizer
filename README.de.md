# Carmageddon Dethrace Modernizer

Der **Carmageddon Dethrace Modernizer** ist ein Windows-orientiertes Komfort- und Kompatibilitätspaket für das originale **Carmageddon** und **Splat Pack** auf Basis von [Dethrace](https://github.com/dethrace-labs/dethrace).

Das Projekt wird von **Bratwurstmensch** entwickelt und getestet, mit umfangreicher Unterstützung durch **ChatGPT von OpenAI**.

> **Originale Carmageddon- oder Splat-Pack-Spieldaten werden nicht mitgeliefert.**
> Benötigt werden eigene, legal erworbene Spieldaten.

## Stand: v1.0 Release Candidate

Der aktuelle Vorbereitungszweig ist **v1.0-rc1**. Die Runtime-Arbeit ist auf Basis des erfolgreich getesteten **RC9** funktional eingefroren.

Unter Windows mit Carmageddon und Splat Pack bestätigt:

- echtes 16:9-Spielbild mit 854×480 im HiRes/OpenGL-Pfad;
- separate 4:3-Modernizer-Runtime im Original-Seitenverhältnis;
- 16:9-Cockpit-3D-Welt über den kompletten 854×480-Frame hinter dem originalen 4:3-Cockpitbild;
- rechts ausgerichteter 16:9-Rückspiegel;
- zentrierte Menüs, Karte, Videos und Rennanzeigen;
- korrigierte Mauskoordinaten in zentrierten Menüflächen;
- native analoge XInput-Lenkung;
- analoges Beschleunigen mit RT sowie Bremsen/Rückwärtsfahren mit LT;
- 500 Einheiten Sichtweite im HiRes-Modus;
- Gegnerfahrzeuge bleiben auch auf Distanz im vollen Hauptmodell;
- weniger Pop-in bei entfernten Fußgängern/Objekten, ohne deren kurze Gameplay-Aktivierungsdistanz zu verändern;
- Hauptspiel und Splat Pack;
- Installer mit Backup-/Rollback-/Uninstall-Verhalten;
- optionale experimentelle German/Uncut-Integration aus eigenen deutschen Spieldaten;
- direkte Extraktion von eXoDOS-artigen CUE/BIN-Cutscenes;
- verlustfreie Extraktion von Red-Book-CD-Audio aus CUE/BIN;
- Dethrace-Wiedergabe mit OGG-Vorrang und WAV-Fallback;
- verifizierter 16:9-Damage-HUD-Fix inklusive der getesteten alternativen verschlüsselten eXoDOS-Datenvariante.

## Getestete RC9-Hashes

Die erfolgreich getesteten RC9-Runtimes besitzen folgende SHA-256-Werte:

- **16:9:** `1df66ba28020f08635773a992e1254ce1b746a11f7a4d77598aff236d7f8ddf6`
- **4:3:** `80dd90f4a74b6caaae19fb336cbd86e5ce0dc3058c509d0da691ecf1511dc9f7`

Beim RC9-Test wurden eine eXoDOS-artige Carmageddon-Quelle sowie die CUE/BIN-Abbilder von Hauptspiel und Splat Pack verwendet. Videos, Musik und Damage HUD wurden praktisch bestätigt.

Details: [docs/RELEASE-CANDIDATE.md](docs/RELEASE-CANDIDATE.md)

## Controller-Belegung

| Eingabe | Funktion |
| --- | --- |
| Linker Stick | Analog lenken |
| RT | Analog beschleunigen |
| LT | Analog bremsen / rückwärts |
| A | Handbremse |
| B | Wheelspin |
| X | Reparieren |
| Y | Recover |
| Back / View | Karte |
| Start / Menu | Escape / Pause / Menü |
| D-Pad | Menü / Pfeiltasten |
| Rechter Stick links/rechts | Links/rechts schauen |
| Rechter Stick oben | Nach vorne schauen |
| LB / RB | Links/rechts schauen |
| Rechter Stick drücken | Cockpit umschalten |
| Linker Stick drücken | Hupe |

Action Replay besitzt ein deutlich größeres eigenes Tastatur-/Maus-Schema und wird absichtlich nicht vollständig auf das normale XInput-Fahrschema gelegt.

## 16:9 und 4:3

Die **16:9-Runtime** ist der moderne Darstellungsweg. Die 3D-Welt füllt 854×480; originale 640 Pixel breite 2D-Oberflächen werden dort zentriert, wo das Spielmaterial dies erfordert.

Das Cockpit selbst bleibt originales 4:3-2D-Artwork. Beim seitlichen Umschauen können deshalb weiterhin Grenzen der Originalgrafiken sichtbar werden.

Die separate **4:3-Runtime** behält die klassische Darstellung und enthält trotzdem die Modernizer-Verbesserungen für Sichtweite, Detailgrad und native analoge XInput-Steuerung.

## GOG- und eXoDOS-artige Quellen

Der Installer unterstützt normale Loose-File-/GOG-artige Installationen sowie den getesteten eXoDOS-Aufbau.

Bei CUE/BIN-Quellen kann er:

- Carmageddon- und Splat-Pack-CD-Images erkennen;
- unterstützte MODE1/MODE2-Datentracks lesen;
- ISO9660 direkt aus dem BIN lesen;
- originale SMK-Videos ohne Mounten extrahieren;
- Red-Book-Audiotracks verlustfrei als 44,1 kHz / 16 Bit / Stereo WAV extrahieren;
- Musik des Hauptspiels nach `MUSIC\Track0N.wav` installieren;
- Musik des Splat Pack nach `CARSPLAT\MUSIC\Track0N.wav` installieren.

Die Runtime bevorzugt vorhandene `Track0N.ogg`-Dateien und verwendet nur bei fehlendem OGG die entsprechende WAV-Datei.

## German / Uncut

Die German/Uncut-Integration bleibt **experimentell** und ist an verifizierte Quellrevisionen gebunden.

Originale deutsche Assets werden nicht verteilt. Der Installer validiert eigene Nutzerdaten und führt die Transformation lokal aus.

Eine aktuell getestete eXoDOS-Splat-Pack-Revision ist noch nicht für die deutsche Transformation freigegeben. In diesem Fall wird kein unbekannter Datensatz blind gepatcht.

## Quellcode und Reproduzierbarkeit

Die Source-Patcher gegen **Dethrace v0.10.1** liegen unter [source-port/](source-port/).

Der mit RC9 praktisch bestätigte CD-Audio-Fix liegt als:

```text
source-port/apply-rc9-cdda-wav-fallback.py
```

Eine eigene GitHub-Actions-Pipeline baut beide Release-Candidate-Runtimes reproduzierbar aus dem Upstream-Quellcode.

## Verhältnis zu Dethrace

Dieses Projekt basiert auf der Arbeit der [Dethrace-Mitwirkenden](https://github.com/dethrace-labs/dethrace), ist aber **kein offizielles Dethrace-Projekt**.

Mehrere Modernizer-Änderungen passen direkt zu offenen Upstream-Wünschen, insbesondere XInput, Widescreen und größere Sichtweite. Siehe [docs/UPSTREAM.md](docs/UPSTREAM.md).

Vor dem ersten öffentlichen Binary-Release soll zusätzlich die Lizenzdarstellung mit den Dethrace-Maintainern kurz geklärt werden, weil im Upstream-Repository eine GPLv3-LICENSE liegt, während im README noch ältere Public-Domain-/Non-Commercial-Formulierungen vorkommen.

## Credits und Lizenz

Carmageddon, Splat Pack und alle Originalassets gehören ihren jeweiligen Rechteinhabern. Dieses Repository enthält keine originalen Spieldaten.

Weitere Angaben: [docs/CREDITS.md](docs/CREDITS.md)

Der Modernizer-Code und die Werkzeuge dieses Repositories stehen unter **GNU GPL v3.0**. Siehe [LICENSE](LICENSE).
