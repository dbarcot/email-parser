#!/usr/bin/env python3
"""
Generate sample mbox file for testing mbox_email_parser.py
"""

import mailbox
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

def create_test_mbox(filename='test_emails.mbox'):
    """Create a test mbox file with sample emails."""
    
    mbox = mailbox.mbox(filename)
    
    # Test email 1: Simple vacation Czech
    msg1 = MIMEText('Dobrý den,\n\nJsem na dovolené do 31.8. V případě potřeby kontaktujte kolegu.\n\nDěkuji', 'plain', 'utf-8')
    msg1['From'] = 'Jan Novák <jan.novak@firma.cz>'
    msg1['To'] = 'team@firma.cz'
    msg1['Subject'] = 'Dovolená'
    msg1['Date'] = email.utils.formatdate((datetime.now() - timedelta(days=10)).timestamp(), localtime=True)
    msg1['Message-ID'] = '<abc123@server.com>'
    mbox.add(msg1)
    
    # Test email 2: OOO English
    msg2 = MIMEText('Hi,\n\nI am out of office until Monday. For urgent matters contact my colleague.\n\nBest regards', 'plain', 'utf-8')
    msg2['From'] = 'Jane Smith <jane.smith@company.com>'
    msg2['To'] = 'jan.novak@firma.cz'
    msg2['Subject'] = 'Out of Office'
    msg2['Date'] = email.utils.formatdate((datetime.now() - timedelta(days=5)).timestamp(), localtime=True)
    msg2['Message-ID'] = '<xyz456@server.com>'
    mbox.add(msg2)
    
    # Test email 3: Sick leave
    msg3 = MIMEText('Dobrý den,\n\nJsem na nemocenské od dneška. Vrátím se příští týden.\n\nS pozdravem', 'plain', 'utf-8')
    msg3['From'] = 'Petr Svoboda <petr.svoboda@firma.cz>'
    msg3['To'] = 'jan.novak@firma.cz, marie.nova@firma.cz'
    msg3['Subject'] = 'Nemocenská'
    msg3['Date'] = email.utils.formatdate((datetime.now() - timedelta(days=3)).timestamp(), localtime=True)
    msg3['Message-ID'] = '<def789@server.com>'
    mbox.add(msg3)
    
    # Test email 4: No vacation - should NOT match
    msg4 = MIMEText('Ahoj,\n\nMohl bys mi poslat tu zprávu? Potřebuji ji na schůzku zítra.\n\nDíky', 'plain', 'utf-8')
    msg4['From'] = 'Karel Vomacka <karel@firma.cz>'
    msg4['To'] = 'jan.novak@firma.cz'
    msg4['Subject'] = 'Dotaz na zprávu'
    msg4['Date'] = email.utils.formatdate((datetime.now() - timedelta(days=1)).timestamp(), localtime=True)
    msg4['Message-ID'] = '<ghi012@server.com>'
    mbox.add(msg4)
    
    # Test email 5: HTML email with vacation
    msg5 = MIMEMultipart('alternative')
    msg5['From'] = 'Marie Nová <marie.nova@firma.cz>'
    msg5['To'] = 'jan.novak@firma.cz'
    msg5['Cc'] = 'team@firma.cz'
    msg5['Subject'] = 'Automatická odpověď: mimo kancelář'
    msg5['Date'] = email.utils.formatdate(datetime.now().timestamp(), localtime=True)
    msg5['Message-ID'] = '<jkl345@server.com>'
    
    text_part = MIMEText('Jsem mimo kancelář. Vrátím se za týden.', 'plain', 'utf-8')
    html_part = MIMEText('<html><body><p>Jsem <b>mimo kancelář</b>. Vrátím se za týden.</p></body></html>', 'html', 'utf-8')
    
    msg5.attach(text_part)
    msg5.attach(html_part)
    mbox.add(msg5)
    
    # Test email 6: Forward with vacation info (FYI use case)
    msg6 = MIMEText('---------- Forwarded message ---------\nFrom: Someone\nSubject: Dovolená\n\nJsem na dovolené do konce měsíce.', 'plain', 'utf-8')
    msg6['From'] = 'Anna Tesarova <anna@firma.cz>'
    msg6['To'] = 'jan.novak@firma.cz'
    msg6['Subject'] = 'FW: Info o dovolené'
    msg6['Date'] = email.utils.formatdate((datetime.now() - timedelta(days=2)).timestamp(), localtime=True)
    msg6['Message-ID'] = '<mno678@server.com>'
    mbox.add(msg6)
    
    # Test email 7: Not involving target email - should NOT match even if has keywords
    msg7 = MIMEText('Chceš jít na dovolenou společně?', 'plain', 'utf-8')
    msg7['From'] = 'random@other.com'
    msg7['To'] = 'someone@other.com'
    msg7['Subject'] = 'Dovolená plány'
    msg7['Date'] = email.utils.formatdate(datetime.now().timestamp(), localtime=True)
    msg7['Message-ID'] = '<pqr901@server.com>'
    mbox.add(msg7)
    
    # Test email 8: Czech charset (windows-1250)
    msg8 = MIMEText('Zdravím,\n\nČerpám řádnou dovolenou do 15.9.\n\nS pozdravem', 'plain', 'windows-1250')
    msg8['From'] = 'Tomáš Dvořák <tomas.dvorak@firma.cz>'
    msg8['To'] = 'jan.novak@firma.cz'
    msg8['Subject'] = 'Řádná dovolená'
    msg8['Date'] = email.utils.formatdate((datetime.now() - timedelta(days=7)).timestamp(), localtime=True)
    msg8['Message-ID'] = '<stu234@server.com>'
    mbox.add(msg8)
    
    mbox.close()
    
    print(f"[✓] Created test mbox: {filename}")
    print(f"[✓] Total emails: 8")
    print(f"[✓] Expected matches for jan.novak@firma.cz: 6")
    print(f"    - Email 1: Dovolená (from jan.novak)")
    print(f"    - Email 2: Out of office (to jan.novak)")
    print(f"    - Email 3: Nemocenská (to jan.novak)")
    print(f"    - Email 4: NO MATCH (no keywords)")
    print(f"    - Email 5: Mimo kancelář HTML (to jan.novak)")
    print(f"    - Email 6: FW with vacation (to jan.novak)")
    print(f"    - Email 7: NO MATCH (not involving jan.novak)")
    print(f"    - Email 8: Řádná dovolená (to jan.novak)")
    print(f"\n[*] Test the parser:")
    print(f"    python mbox_email_parser.py --mbox {filename} --email jan.novak@firma.cz --dry-run")

if __name__ == '__main__':
    create_test_mbox()
