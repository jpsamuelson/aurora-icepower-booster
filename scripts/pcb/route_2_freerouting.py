#!/usr/bin/env python3
"""
Phase 2: Run Freerouting on the DSN file.
Produces SES session file.
"""
import subprocess, os, sys

DSN = '/tmp/aurora-booster.dsn'
SES = '/tmp/aurora-booster.ses'
JAR = '/tmp/freerouting.jar'
JAR_URL = 'https://github.com/freerouting/freerouting/releases/download/v2.0.1/freerouting-2.0.1.jar'

if not os.path.exists(DSN):
    print(f'ERROR: DSN file not found: {DSN}')
    print('Run route_1_export_dsn.py first!')
    sys.exit(1)

# Download Freerouting if not present
if not os.path.exists(JAR):
    print(f'Downloading Freerouting → {JAR}')
    r = subprocess.run(['curl', '-L', '-o', JAR, JAR_URL], capture_output=True, text=True)
    if r.returncode != 0:
        print(f'ERROR: Download failed: {r.stderr}')
        sys.exit(1)
    print(f'  Downloaded: {os.path.getsize(JAR):,} bytes')
else:
    print(f'Freerouting JAR: {JAR} ({os.path.getsize(JAR):,} bytes)')

# Remove old SES
if os.path.exists(SES):
    os.remove(SES)

print(f'\nRunning Freerouting...')
print(f'  DSN: {DSN}')
print(f'  SES: {SES}')
print(f'  Max passes: 20, Threads: 4')

result = subprocess.run(
    ['java', '-Djava.awt.headless=true', '-jar', JAR, '-de', DSN, '-do', SES, '-mp', '30', '-mt', '1'],
    capture_output=True, text=True, timeout=600
)

print(f'\nFreerouting stdout:')
for line in result.stdout.strip().split('\n')[-20:]:
    print(f'  {line}')

if result.returncode != 0:
    print(f'\nFreerouting stderr:')
    print(result.stderr[:500])

if os.path.exists(SES):
    size = os.path.getsize(SES)
    print(f'\n✅ SES file: {SES} ({size:,} bytes)')
else:
    print(f'\n❌ SES file NOT created!')
    sys.exit(1)
