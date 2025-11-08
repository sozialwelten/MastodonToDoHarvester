# Mastodon ToDo Harvester

Ein einfaches Python-Tool für die Kommandozeile, das deine mit #ToDo getaggten Mastodon-Beiträge von mehreren Accounts abruft und in eine CSV-Datei exportiert. Es ist konzipiert für nicht öffentlich gepostete Beiträge (unlisted), weshalb ein Token notwendig ist.

## Features

- Ruft ToDo-Beiträge von mehreren Mastodon-Accounts ab
- Nutzt die offizielle Mastodon API (funktioniert auch mit privaten Beiträgen)
- Zeigt alle Beiträge übersichtlich in der Konsole
- Exportiert die Daten in eine CSV-Datei mit Spalten: Account, Datum, Uhrzeit, Inhalt
- Sortiert Beiträge nach Datum (neueste zuerst)

## Installation

```bash
pip install requests
```

## Konfiguration

1. Öffne `mastodon_todos.py` in einem Editor
2. Passe die Konfiguration im `ACCOUNTS`-Bereich an:
   - Trage deine Mastodon-Instanz-URL ein
   - Trage deine Benutzernamen ein
   - Erstelle Access Tokens (siehe unten)

### Access Token erstellen

Für jeden Account:

1. Bei Mastodon einloggen
2. **Einstellungen** → **Entwicklung** → **Neue Anwendung**
3. Name vergeben (z.B. "ToDo Harvester")
4. **Berechtigungen:** Nur `read:accounts` und `read:statuses` aktivieren
5. Speichern und Access Token kopieren
6. Token im Script eintragen

## Verwendung

```bash
python mastodon_todos.py
```

Das Tool erstellt automatisch eine CSV-Datei mit Zeitstempel im Namen, z.B. `mastodon_todos_20241108_143022.csv`

## Ausgabe

Die CSV-Datei enthält folgende Spalten:
- **Account**: Name des Accounts
- **Datum**: Erstellungsdatum des Beitrags (YYYY-MM-DD)
- **Uhrzeit**: Erstellungszeit des Beitrags (HH:MM:SS)
- **Inhalt**: Textinhalt des Beitrags (bereinigt von HTML-Tags)

## Lizenz

GPL-3.0

## Autor

Michael Karbacher