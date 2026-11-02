#!/usr/bin/env python3
"""Build dances.ics (the calendar feed people subscribe to) from the confirmed
listings in index.html. Each confirmed card carries data-cal="start/end"
(Alberta local time, written out as UTC; or just a date for all-day) and optional data-rrule."""
import hashlib, html, re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

AB = ZoneInfo('America/Edmonton')  # tzdata 2026f+: Alberta stays on UTC-6 year-round from Nov 1, 2026

def utc(local):
    return datetime.strptime(local, '%Y%m%dT%H%M').replace(tzinfo=AB).astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def text(frag):
    frag = re.sub(r'<span class="(pill|drive)[^"]*"[^>]*>.*?</span>', '', frag, flags=re.S)
    return html.unescape(re.sub(r'<[^>]+>', '', frag)).strip()

def esc(v):
    return v.replace('\\', '\\\\').replace(';', r'\;').replace(',', '\\,').replace('\n', '\\n')

def fold(line):
    out, b = [], line.encode()
    while len(b) > 74:
        cut = 74
        while (b[cut] & 0xC0) == 0x80: cut -= 1
        out.append(b[:cut].decode()); b = b[cut:]
    out.append(b.decode())
    return '\r\n '.join(out)

def main():
    with open('index.html', encoding='utf-8') as f: src = f.read()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Two-Step Alberta//Dances//EN',
             'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', 'X-WR-CALNAME:Two-Step Alberta dances',
             'X-WR-TIMEZONE:America/Edmonton', 'REFRESH-INTERVAL;VALUE=DURATION:PT12H',
             'X-PUBLISHED-TTL:PT12H']
    n = 0
    for m in re.finditer(r'<li class="ticket"[^>]*data-cal="([^"]+)"([^>]*)>(.*?)</li>\s*(?=<li class="ticket"|</ol>)', src, re.S):
        cal, rest, body = m.groups()
        rr = re.search(r'data-rrule="([^"]+)"', rest)
        title = text(re.search(r'<h3>(.*?)</h3>', body, re.S)[1])
        where = text(re.search(r'<p class="where">(.*?)</p>', body, re.S)[1]).split(' · ')[0].rstrip(' ·')
        link = re.search(r'<p class="src">.*?href="([^"]+)"', body, re.S)
        when = re.search(r'<b>When:</b>(.*?)</li>', body, re.S)
        desc = (text(when[1]) if when else '') + '\nCheck with the hall before you go.'
        if link: desc += '\n' + html.unescape(link[1])
        uid = hashlib.sha1((title + cal).encode()).hexdigest()[:16] + '@twostepalberta.ca'
        ev = ['BEGIN:VEVENT', 'UID:' + uid, 'DTSTAMP:' + stamp]
        if '/' in cal:
            a, b = cal.split('/')
            ev += ['DTSTART:' + utc(a), 'DTEND:' + utc(b)]
        else:
            d = datetime.strptime(cal, '%Y%m%d').toordinal() + 1
            ev += ['DTSTART;VALUE=DATE:' + cal, 'DTEND;VALUE=DATE:' + datetime.fromordinal(d).strftime('%Y%m%d')]
        if rr: ev.append('RRULE:' + rr[1])
        ev += ['SUMMARY:' + esc(title), 'LOCATION:' + esc(where), 'DESCRIPTION:' + esc(desc)]
        if link: ev.append('URL:' + html.unescape(link[1]))
        ev.append('END:VEVENT')
        lines += ev; n += 1
    lines.append('END:VCALENDAR')
    with open('dances.ics', 'w', encoding='utf-8', newline='') as f: f.write('\r\n'.join(fold(l) for l in lines) + '\r\n')
    print('Wrote dances.ics with', n, 'events')

if __name__ == '__main__':
    main()
