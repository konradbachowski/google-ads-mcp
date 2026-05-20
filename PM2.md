# PM2 Management Guide

Instrukcje zarządzania serwerem MCP przez PM2 dla ciągłego działania w tle.

---

## 🚀 Pierwsze uruchomienie

```bash
cd /Users/mac/kodziki/mcp/google-keyword-planner-mcp

# Start serwera w PM2
pm2 start ecosystem.config.js

# Sprawdź status
pm2 status
```

Powinieneś zobaczyć:
```
┌─────┬──────────────────────────────┬─────────┬─────────┐
│ id  │ name                         │ status  │ restart │
├─────┼──────────────────────────────┼─────────┼─────────┤
│ 0   │ google-keyword-planner-mcp   │ online  │ 0       │
└─────┴──────────────────────────────┴─────────┴─────────┘
```

---

## 📊 Monitoring

### Zobacz logi na żywo
```bash
pm2 logs google-keyword-planner-mcp
```

### Tylko błędy
```bash
pm2 logs google-keyword-planner-mcp --err
```

### Monitoring w czasie rzeczywistym
```bash
pm2 monit
```

### Informacje o procesie
```bash
pm2 info google-keyword-planner-mcp
```

---

## 🔄 Zarządzanie

### Restart serwera
```bash
pm2 restart google-keyword-planner-mcp
```

### Stop serwera
```bash
pm2 stop google-keyword-planner-mcp
```

### Start ponowny
```bash
pm2 start google-keyword-planner-mcp
```

### Usuń z PM2
```bash
pm2 delete google-keyword-planner-mcp
```

---

## ⚙️ Auto-start po restarcie systemu

### Konfiguracja (tylko raz)
```bash
# Wygeneruj skrypt startowy
pm2 startup

# Zapisz obecną konfigurację
pm2 save
```

Teraz PM2 uruchomi się automatycznie po restarcie macOS, a wszystkie zapisane procesy wystartują.

---

## 🔧 Aktualizacja kodu

Gdy zmienisz kod w projekcie:

```bash
# Restart z przeładowaniem
pm2 restart google-keyword-planner-mcp
```

---

## 📋 Wszystkie serwery MCP

Zobacz wszystkie serwery naraz:
```bash
pm2 list
```

Restart wszystkich:
```bash
pm2 restart all
```

Stop wszystkich:
```bash
pm2 stop all
```

---

## 🐛 Troubleshooting

### Serwer nie startuje
```bash
# Zobacz pełne logi błędów
pm2 logs google-keyword-planner-mcp --err --lines 50

# Sprawdź czy venv istnieje
ls -la /Users/mac/kodziki/mcp/google-keyword-planner-mcp/.venv

# Test ręczny
cd /Users/mac/kodziki/mcp/google-keyword-planner-mcp
source .venv/bin/activate
python src/main.py
```

### Status: errored
```bash
# Usuń i uruchom ponownie
pm2 delete google-keyword-planner-mcp
pm2 start ecosystem.config.js
```

### Wysokie zużycie pamięci
```bash
# Restart z limitem
pm2 restart google-keyword-planner-mcp --max-memory-restart 300M
```

---

## 📁 Pliki logów

Logi znajdują się w:
```
/Users/mac/kodziki/mcp/google-keyword-planner-mcp/logs/
├── error.log  # Błędy
└── out.log    # Standardowy output
```

Czyszczenie logów:
```bash
pm2 flush google-keyword-planner-mcp
```

---

## 🔐 Credentials w PM2

**Ważne:** PM2 korzysta z `.env` file w katalogu projektu.

Upewnij się że `.env` jest poprawnie skonfigurowany:
```bash
cat /Users/mac/kodziki/mcp/google-keyword-planner-mcp/.env
```

Jeśli zmieniasz credentials:
```bash
# Po edycji .env
pm2 restart google-keyword-planner-mcp
```

---

## 📚 Przydatne komendy

```bash
# Szczegółowy status
pm2 show google-keyword-planner-mcp

# Metryki
pm2 monit

# Lista procesów w JSON
pm2 jlist

# Restart z zero downtime
pm2 reload google-keyword-planner-mcp
```

---

## 🆘 Reset całkowity

Jeśli coś poszło źle:

```bash
# Stop i usuń
pm2 delete google-keyword-planner-mcp

# Wyczyść logi
rm -rf logs/*.log

# Zainstaluj zależności ponownie
source .venv/bin/activate
pip install -r requirements.txt

# Uruchom od nowa
pm2 start ecosystem.config.js
```
