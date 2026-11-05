#!/usr/bin/env python3
"""Build dances.ics (the calendar feed people subscribe to) and feed.xml (RSS for email alerts) from the confirmed
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
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Two Step Alberta//Dances//EN',
             'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', 'X-WR-CALNAME:Two Step Alberta dances',
             'X-WR-TIMEZONE:America/Edmonton', 'REFRESH-INTERVAL;VALUE=DURATION:PT12H',
             'X-PUBLISHED-TTL:PT12H']
    n = 0
    items = []
    for m in re.finditer(r'<li class="ticket"[^>]*data-cal="([^"]+)"([^>]*)>(.*?)</li>\s*(?=<li class="ticket"|</ol>)', src, re.S):
        cal, rest, body = m.groups()
        rr = re.search(r'data-rrule="([^"]+)"', rest)
        title = text(re.search(r'<h3>(.*?)</h3>', body, re.S)[1])
        where = text(re.search(r'<p class="where">(.*?)</p>', body, re.S)[1]).split(' · ')[0].rstrip(' ·')
        link = re.search(r'<p class="src">.*?href="([^"]+)"', body, re.S)
        when = re.search(r'<b>When:</b>(.*?)</li>', body, re.S)
        desc = (text(when[1]) if when else '') + '\nCheck the event page before you go.'
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
        items.append((uid, title, where, desc, html.unescape(link[1]) if link else 'https://twostepalberta.ca/'))
    lines.append('END:VCALENDAR')
    with open('dances.ics', 'w', encoding='utf-8', newline='') as f: f.write('\r\n'.join(fold(l) for l in lines) + '\r\n')
    print('Wrote dances.ics with', n, 'events')
    write_rss(items)

def write_rss(items):
    # feed.xml: one item per confirmed dance, so email services (follow.it, MailerLite)
    # can send new dances automatically. guid stays stable, so only new dances trigger mail.
    from email.utils import format_datetime
    now = format_datetime(datetime.now(timezone.utc))
    x = lambda v: html.escape(v, quote=True)
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">', '<channel>',
           '<title>Two Step Alberta: new dances</title>', '<link>https://twostepalberta.ca/</link>',
           '<atom:link href="https://twostepalberta.ca/feed.xml" rel="self" type="application/rss+xml"/>',
           '<description>Hall dances, cabarets and suppers around Edmonton, updated every Wednesday.</description>',
           '<language>en-ca</language>', '<lastBuildDate>' + now + '</lastBuildDate>']
    for uid, title, where, desc, link in items:
        body = where + '\n' + desc
        out += ['<item>', '<title>' + x(title) + '</title>', '<link>' + x(link) + '</link>',
                '<guid isPermaLink="false">' + x(uid) + '</guid>',
                '<description>' + x(body.replace('\n', '<br>')) + '</description>', '</item>']
    out += ['</channel>', '</rss>']
    with open('feed.xml', 'w', encoding='utf-8') as f: f.write('\n'.join(out) + '\n')
    print('Wrote feed.xml with', len(items), 'items')

if __name__ == '__main__':
    main()
