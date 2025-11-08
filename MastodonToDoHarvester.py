#!/usr/bin/env python3
"""
Mastodon ToDo Harvester
Ruft ToDo-Beiträge von mehreren Mastodon-Accounts über die Mastodon API ab.
"""

import requests
import csv
from datetime import datetime
import sys
from typing import List, Dict
import os
from html import unescape
import re

# ============================================================================
# KONFIGURATION - BITTE ANPASSEN!
# ============================================================================
# Füge hier deine Mastodon-Accounts hinzu oder passe die vorhandenen an.
# Für jeden Account benötigst du:
# - name: Ein Anzeigename für die Ausgabe (frei wählbar)
# - instance: Die URL deiner Mastodon-Instanz (z.B. https://mastodon.social)
# - account_id: Dein Benutzername auf der Instanz (ohne @)
# - access_token: Dein Access Token (siehe Anleitung unten)
#
# So erstellst du einen Access Token:
# 1. Logge dich bei Mastodon ein
# 2. Einstellungen → Entwicklung → Neue Anwendung
# 3. Name vergeben (z.B. "ToDo Harvester")
# 4. Berechtigungen: Nur read:accounts und read:statuses aktivieren
# 5. Speichern und Access Token kopieren
# ============================================================================

ACCOUNTS = [
    {
        "name": "account1",  # Ändere den Anzeigenamen
        "instance": "https://mastodon.social",  # Ändere die Instanz-URL
        "account_id": "username1",  # Ändere den Benutzernamen
        "access_token": "DEIN_ACCESS_TOKEN_HIER"  # Füge deinen Token ein
    },
    {
        "name": "account2",
        "instance": "https://mastodon.social",
        "account_id": "username2",
        "access_token": "DEIN_ACCESS_TOKEN_HIER"
    },
    {
        "name": "account3",
        "instance": "https://mastodon.social",
        "account_id": "username3",
        "access_token": "DEIN_ACCESS_TOKEN_HIER"
    }
]


def clean_html(text: str) -> str:
    """
    Entfernt HTML-Tags und bereinigt den Text.

    Args:
        text: HTML-Text

    Returns:
        Bereinigter Text
    """
    # HTML-Tags entfernen
    text = re.sub('<[^<]+?>', '', text)
    # HTML-Entities dekodieren
    text = unescape(text)
    # Mehrfache Leerzeichen durch einfache ersetzen
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def get_account_id(instance: str, username: str, access_token: str) -> str:
    """
    Holt die numerische Account-ID für einen Benutzernamen.

    Args:
        instance: Mastodon-Instanz URL
        username: Benutzername
        access_token: Access Token für die API

    Returns:
        Account-ID oder None bei Fehler
    """
    try:
        url = f"{instance}/api/v1/accounts/lookup"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"acct": username}

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        return data.get('id')
    except Exception as e:
        print(f"Fehler beim Abrufen der Account-ID für {username}: {e}", file=sys.stderr)
        return None


def fetch_todos(instance: str, account_id: str, access_token: str, account_name: str) -> List[Dict]:
    """
    Ruft ToDo-Beiträge über die Mastodon API ab.

    Args:
        instance: Mastodon-Instanz URL
        account_id: Account-ID oder Username
        access_token: Access Token für die API
        account_name: Name des Accounts für die Anzeige

    Returns:
        Liste von Dictionaries mit den Beitragsinformationen
    """
    todos = []

    try:
        print(f"Rufe Beiträge ab für {account_name}...", file=sys.stderr)

        # Prüfe ob account_id numerisch ist, sonst hole die ID
        if not account_id.isdigit():
            numeric_id = get_account_id(instance, account_id, access_token)
            if not numeric_id:
                print(f"✗ Konnte Account-ID für {account_name} nicht finden", file=sys.stderr)
                return []
            account_id = numeric_id

        # API-Endpunkt für Account-Statuses mit Hashtag-Filter
        url = f"{instance}/api/v1/accounts/{account_id}/statuses"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "tagged": "todo",
            "limit": 40  # Maximal 40 Beiträge pro Request
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        statuses = response.json()

        for status in statuses:
            try:
                # Datum und Uhrzeit extrahieren
                created_at = status.get('created_at', '')
                if created_at:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    datum = dt.strftime('%Y-%m-%d')
                    uhrzeit = dt.strftime('%H:%M:%S')
                else:
                    datum = "N/A"
                    uhrzeit = "N/A"

                # Inhalt extrahieren und bereinigen
                content = status.get('content', '')
                inhalt = clean_html(content)

                # Sichtbarkeit prüfen (optional für Debugging)
                visibility = status.get('visibility', 'unknown')

                todos.append({
                    'Account': account_name,
                    'Datum': datum,
                    'Uhrzeit': uhrzeit,
                    'Inhalt': inhalt,
                    'Sichtbarkeit': visibility  # Optional für Debugging
                })
            except Exception as e:
                print(f"Fehler beim Parsen eines Beitrags: {e}", file=sys.stderr)
                continue

        print(f"✓ {len(todos)} Beiträge gefunden für {account_name}", file=sys.stderr)

    except requests.RequestException as e:
        print(f"✗ Fehler beim Abrufen von {account_name}: {e}", file=sys.stderr)
        if hasattr(e.response, 'text'):
            print(f"   API-Antwort: {e.response.text}", file=sys.stderr)

    return todos


def save_to_csv(todos: List[Dict], filename: str = 'mastodon_todos.csv'):
    """
    Speichert die ToDo-Beiträge in eine CSV-Datei.

    Args:
        todos: Liste der ToDo-Dictionaries
        filename: Name der CSV-Datei
    """
    if not todos:
        print("Keine Beiträge zum Speichern gefunden.", file=sys.stderr)
        return

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Account', 'Datum', 'Uhrzeit', 'Inhalt']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for todo in todos:
                # Entferne optionale Debug-Felder
                row = {k: v for k, v in todo.items() if k in fieldnames}
                writer.writerow(row)

        print(f"\n✓ {len(todos)} Beiträge erfolgreich in '{filename}' gespeichert!", file=sys.stderr)

    except IOError as e:
        print(f"✗ Fehler beim Speichern der CSV: {e}", file=sys.stderr)
        sys.exit(1)


def display_todos(todos: List[Dict]):
    """
    Zeigt die ToDo-Beiträge in der Konsole an.

    Args:
        todos: Liste der ToDo-Dictionaries
    """
    if not todos:
        print("\nKeine ToDo-Beiträge gefunden.")
        return

    print(f"\n{'=' * 80}")
    print(f"{'MASTODON TODO-BEITRÄGE':^80}")
    print(f"{'=' * 80}\n")

    for i, todo in enumerate(todos, 1):
        print(f"[{i}] Account: {todo['Account']}")
        print(f"    Datum: {todo['Datum']} | Uhrzeit: {todo['Uhrzeit']}")
        print(f"    Inhalt: {todo['Inhalt'][:150]}{'...' if len(todo['Inhalt']) > 150 else ''}")
        print(f"{'-' * 80}\n")


def check_tokens():
    """Prüft, ob Access Tokens konfiguriert wurden."""
    for account in ACCOUNTS:
        if account['access_token'] == "DEIN_ACCESS_TOKEN_HIER":
            print("=" * 80)
            print("FEHLER: Access Tokens nicht konfiguriert!")
            print("=" * 80)
            print("\nBitte konfiguriere die Access Tokens in der Datei:")
            print("1. Gehe zu Mastodon → Einstellungen → Entwicklung")
            print("2. Erstelle eine neue Anwendung für jeden Account")
            print("3. Kopiere die Access Tokens")
            print("4. Ersetze 'DEIN_ACCESS_TOKEN_HIER' im Script")
            print("\nBenötigte Berechtigungen: read:accounts, read:statuses")
            print("=" * 80)
            sys.exit(1)


def main():
    """Hauptfunktion des Tools."""
    print("=" * 80)
    print("Mastodon ToDo Harvester (API-Version)")
    print("=" * 80)
    print()

    # Prüfe ob Tokens konfiguriert sind
    check_tokens()

    all_todos = []

    # Alle Accounts durchgehen
    for account in ACCOUNTS:
        todos = fetch_todos(
            account['instance'],
            account['account_id'],
            account['access_token'],
            account['name']
        )
        all_todos.extend(todos)

    # Sortiere nach Datum (neueste zuerst)
    all_todos.sort(key=lambda x: (x['Datum'], x['Uhrzeit']), reverse=True)

    # Zeige die Beiträge an
    display_todos(all_todos)

    # Speichere in CSV
    csv_filename = f"mastodon_todos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    save_to_csv(all_todos, csv_filename)

    print(f"\nGesamt: {len(all_todos)} ToDo-Beiträge abgerufen")


if __name__ == "__main__":
    main()