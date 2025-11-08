# 🚀 Quick Start Guide

## Instalace (5 minut)

```bash
# 1. Stáhni soubory
# vacation_email_extractor.py
# requirements.txt

# 2. Nainstaluj dependencies
pip install -r requirements.txt

# 3. Ověř instalaci
python vacation_email_extractor.py --help
```

## První použití

### Krok 1: Test s ukázkovými daty

```bash
# Vytvoř testovací mbox
python create_test_mbox.py

# Spusť dry-run (jen spočítá matches)
python vacation_email_extractor.py \
    --mbox test_emails.mbox \
    --email jan.novak@firma.cz \
    --dry-run
```

**Očekávaný výstup:**
```
Total processed: 8
Matches found:   6
Failed emails:   0
```

### Krok 2: Zkouška s reálným exportem

```bash
# Spusť na reálných datech
python vacation_email_extractor.py \
    --mbox your_archive.mbox \
    --email target@email.cz \
    --output ./results
```

## Běžné use cases

### Právní případ - kompletní extrakce

```bash
python vacation_email_extractor.py \
    --mbox /path/to/legal_archive.mbox \
    --email subject.person@company.com \
    --output ./case_2024_001 \
    --log-file case_001_extraction.csv
```

### Částečné zpracování (test na prvních 100 emailech)

```bash
python vacation_email_extractor.py \
    --mbox large_archive.mbox \
    --email person@company.com \
    --email-limit 100 \
    --output ./test_run
```

### Pouze zjistit počet matchů (bez ukládání)

```bash
python vacation_email_extractor.py \
    --mbox archive.mbox \
    --email person@company.com \
    --dry-run
```

## Výsledky

Po dokončení najdeš:

```
results/
├── 20240115_143022_jan.novak_abc123_dovolen.eml  ← Nalezené emaily
├── 20240128_091544_petr.svoboda_xyz456_nemocenska.eml
├── ...
└── failed/
    └── failed_email_0001.eml  ← Emaily s chybou dekódování

extraction_log.csv  ← Detailní log (Excel/CSV kompatibilní)
```

## Otevření výsledků

### EML soubory můžeš otevřít v:
- **Outlook** - dvojklik na .eml soubor
- **Thunderbird** - File → Open Saved Message
- **Gmail** - nahrát jako attachment a otevřít
- **Windows Mail** - dvojklik

### CSV log:
- **Excel** - otevři přímo
- **LibreOffice Calc** - otevři přímo
- **Text editor** - pro rychlé prohlédnutí

## Tips & Tricks

### 1. Dry-run první!
Vždy nejdřív spusť s `--dry-run` pro zjištění počtu matchů.

### 2. Email limit pro velké archivy
Pro archivy s 10,000+ emaily použij `--email-limit` pro postupné zpracování.

### 3. Zkontroluj failed složku
Pokud jsou nějaké emaily v `failed/`, otevři je ručně - většinou jde o poškozené emaily.

### 4. CSV log pro přehled
CSV log obsahuje všechny detaily - ideální pro filtrování a analýzu v Excelu.

## Typické problémy

### "No module named 'bs4'"
```bash
pip install beautifulsoup4
```

### "Permission denied" na Windows
Spusť command prompt jako Administrator.

### Script je pomalý
- HTML emaily jsou pomalé na parsing
- Pro rychlejší běh bez HTML podpory: neinstaluj BeautifulSoup

### Chybějící emaily ve výsledcích
- Zkontroluj, že target email je správně zadaný (case-insensitive)
- Email musí být v From/To/Cc/Reply-To
- Email musí obsahovat vacation keywords

## Další kroky

Po extrakci můžeš:
1. Otevřít EML soubory v email klientovi
2. Analyzovat CSV log v Excelu
3. Zpracovat EML soubory dalšími nástroji
4. Archivovat výsledky pro právní účely

---

**Podporované formáty:**
- ✅ Plain text emaily
- ✅ HTML emaily (s BeautifulSoup)
- ✅ Multipart emaily
- ✅ Emaily s přílohami
- ✅ České charset (UTF-8, CP1250, ISO-8859-2)
- ✅ Anglické charset (UTF-8, ASCII)

**Testováno na:**
- Windows 10/11
- Python 3.7 - 3.12

**Otázky? Problémy?**
Viz README.md pro detailní dokumentaci.
