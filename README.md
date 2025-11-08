# Vacation Email Extractor

Extrahuje vacation/OOO related emaily z mbox souborů pro právní případy.

## Funkce

- ✅ Prohledává celé textové tělo emailu (plain text + HTML)
- ✅ Filtruje podle emailové adresy v From/To/Cc/Reply-To
- ✅ Detekuje české i anglické vacation/OOO keywords
- ✅ Ukládá kompletní emaily jako EML (včetně příloh)
- ✅ Collision handling s incrementálním suffixem
- ✅ Charset fallback (cp1250 → utf-8 → latin1)
- ✅ CSV logging s detaily
- ✅ Graceful Ctrl+C handling
- ✅ Dry-run mode pro testování
- ✅ Email limit pro částečné zpracování

## Instalace

### 1. Python Requirements

Vyžaduje Python 3.7+

```bash
# Instalace dependencies
pip install -r requirements.txt
```

### 2. Ověření instalace

```bash
python vacation_email_extractor.py --help
```

## Použití

### Základní použití

```bash
python vacation_email_extractor.py --mbox archive.mbox --email jan.novak@firma.cz
```

### Pokročilé použití

```bash
# S vlastním output adresářem
python vacation_email_extractor.py \
    --mbox archive.mbox \
    --email jan.novak@firma.cz \
    --output ./results

# Dry run (pouze spočítat matches)
python vacation_email_extractor.py \
    --mbox archive.mbox \
    --email jan.novak@firma.cz \
    --dry-run

# Zpracovat pouze prvních 100 emailů
python vacation_email_extractor.py \
    --mbox archive.mbox \
    --email jan.novak@firma.cz \
    --email-limit 100

# Všechny parametry dohromady
python vacation_email_extractor.py \
    --mbox archive.mbox \
    --email jan.novak@firma.cz \
    --output ./legal_case_001 \
    --log-file case_001_log.csv \
    --email-limit 1000
```

## Parametry

### Povinné

- `--mbox PATH` - Cesta k mbox souboru
- `--email EMAIL` - Cílový email (case-insensitive)

### Volitelné

- `--output DIR` - Output adresář (default: `./output`)
- `--email-limit N` - Zpracovat max N emailů
- `--dry-run` - Pouze spočítat matches, neukládat soubory
- `--log-file PATH` - Cesta k CSV logu (default: `extraction_log.csv`)

## Output struktura

```
output/
├── 20240115_143022_jan.novak_abc123_dovolen.eml
├── 20240128_091544_petr.svoboda_xyz456_nemocenska.eml
├── 20240203_162315_marie.nova_def789_ooo_001.eml  ← collision suffix
└── failed/
    ├── failed_email_0001.eml  ← nedekódovatelné emaily
    └── failed_email_0002.eml

extraction_log.csv  ← Detailní log všech matchů
```

## CSV Log formát

Log obsahuje následující sloupce:

| Sloupec | Popis |
|---------|-------|
| `filename` | Skutečný název uloženého souboru |
| `original_filename` | Původně generovaný název |
| `collision` | TRUE/FALSE - byla kolize? |
| `date` | Datum emailu |
| `from` | Odesílatel |
| `to` | Příjemce |
| `subject` | Předmět |
| `matched_keywords` | Nalezené klíčová slova |
| `match_positions` | Pozice matchů v textu |

## Detekované keywords

Script detekuje tyto typy vacation/OOO zpráv:

### České výrazy
- Dovolená, dov., čerpám dovolenou
- Prázdniny
- Volno
- Nepřítomen, nepřítomnost
- Mimo kancelář, mimo provoz
- Nemocenská, PN, pracovní neschopnost
- Zdravotní volno
- Absence
- Nedostupný
- Rodičovská, mateřská, otcovská
- Vrátím se, budu zpět
- K dispozici, k zastižení

### Anglické výrazy
- Vacation, holiday
- Out of office, OOO
- Sick leave, sick day
- Time off, PTO
- Unavailable, away
- Autoreply, automatic reply

### Časové fráze
- Od 15.5., do 31.8.
- Až do pondělí
- Vrátím 1.6.

## Troubleshooting

### Problem: "BeautifulSoup not installed"

```bash
pip install beautifulsoup4
```

### Problem: Velký mbox soubor (10GB+)

```bash
# Zpracuj po částech s --email-limit
python vacation_email_extractor.py --mbox huge.mbox --email jan@firma.cz --email-limit 10000
# Pak pokračuj od místa přerušení (zatím není implementováno - bude v v2.0)
```

### Problem: Script běží pomalu

HTML emaily jsou pomalé na konverzi. Pokud není potřeba HTML konverze:
- Odinstaluj BeautifulSoup - script bude rychlejší ale méně přesný

### Problem: Charset errors i s fallbackem

Velmi vzácné - pokud se stane:
1. Email se uloží do `failed/` složky
2. Můžeš ho ručně otevřít v email klientovi
3. Script pokračuje dál

## Progress tracking

Script vypisuje progress každých 100 emailů:

```
Processed: 1,200 | Matches: 23 | Failed: 2
Processed: 1,300 | Matches: 25 | Failed: 2
```

## Ctrl+C handling

Script lze kdykoliv bezpečně přerušit Ctrl+C:

```
^C
[!] Ctrl+C detected - graceful shutdown...
Processed: 1,247
Matches:   24
Failed:    2

Partial results saved.
```

Všechny doposud zpracované emaily jsou uložené.

## Známá omezení

1. **Deduplikace**: Script nedetekuje duplicitní emaily (by design - pro legal case)
2. **Resume**: Nelze pokračovat od místa přerušení (plánováno v2.0)
3. **Multiprocessing**: Single-threaded processing (pro jednoduchost a bezpečnost)
4. **Velké přílohy**: Emaily s velmi velkými přílohami (100MB+) mohou být pomalé

## Best practices pro legal cases

### 1. Vždy použij dry-run nejdřív

```bash
# Zjisti počet matchů bez ukládání
python vacation_email_extractor.py --mbox archive.mbox --email jan@firma.cz --dry-run
```

### 2. Uchovej originální mbox

Nikdy nepřepisuj originální mbox soubor!

### 3. Dokumentuj parametry

```bash
# Vytvoř script pro reprodukovatelnost
cat > extract_case_001.sh << 'EOF'
#!/bin/bash
python vacation_email_extractor.py \
    --mbox /path/to/archive.mbox \
    --email subject@firma.cz \
    --output ./case_001_results \
    --log-file case_001_extraction.csv
EOF
chmod +x extract_case_001.sh
```

### 4. Ověř výsledky

```bash
# Zkontroluj CSV log
head -n 20 extraction_log.csv

# Zkontroluj počet souborů
ls -la output/*.eml | wc -l

# Otevři pár náhodných EML v Outlook/Thunderbird
```

## Technické detaily

### Encoding handling

1. Script používá deklarovaný charset z email headeru
2. Pokud selže → fallback na cp1250 (Windows Czech)
3. Pokud selže → fallback na utf-8
4. Pokud selže → fallback na latin1 (nikdy neselže)

### HTML konverze

- BeautifulSoup odstraňuje `<script>` a `<style>` tagy
- Extrahuje jen viditelný text
- Zachovává mezery mezi elementy

### Filename sanitization

- Odstraňuje neplatné znaky pro Windows: `< > : " / \ | ? *`
- Maximální délka: 255 znaků
- Collision handling: `_001`, `_002`, atd.

## Výkon

Typické časy zpracování:

- **Malý mbox** (1,000 emailů): ~30 sekund
- **Střední mbox** (10,000 emailů): ~5 minut
- **Velký mbox** (100,000 emailů): ~45 minut

*Závisí na velikosti emailů, počtu HTML emailů a rychlosti disku.*

## Podpora

Pro bug reporty a feature requesty kontaktujte vývojáře.

## Changelog

### v1.0 (2025-11-08)
- Initial release
- Kompletní Czech + English keyword detection
- Collision handling
- Charset fallback
- HTML to text conversion
- CSV logging
- Ctrl+C handling
- Dry-run mode

## License

Pro interní použití.
