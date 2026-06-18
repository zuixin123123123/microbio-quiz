#!/usr/bin/env python3
"""Build debug APK manually using Android SDK tools (no Gradle)."""

import os
import sys
import shutil
import subprocess
import tempfile

# ── Paths ──
ANDROID_HOME = r'C:\Users\Luozirui\AppData\Local\Android\Sdk'
JAVA_HOME = r'C:\Users\Luozirui\.lunarclient\jre\4dcd188552ce8876d5e55e1f6d22505109bfa4cb\zulu17.34.19-ca-jre17.0.3-win_x64'
BUILD_TOOLS = os.path.join(ANDROID_HOME, 'build-tools', '33.0.0')
PLATFORM = os.path.join(ANDROID_HOME, 'platforms', 'android-33')
ANDROID_JAR = os.path.join(PLATFORM, 'android.jar')

PROJECT = r'f:\高驰AI助手\microbio-app\android-manual'
APP_SRC = os.path.join(PROJECT, 'app', 'src', 'main')
JAVA_SRC = os.path.join(APP_SRC, 'java')
RES_DIR = os.path.join(APP_SRC, 'res')
ASSETS_DIR = os.path.join(APP_SRC, 'assets')
MANIFEST = os.path.join(APP_SRC, 'AndroidManifest.xml')

# Output APK
OUTPUT_UNSIGNED = os.path.join(PROJECT, 'app-debug-unsigned.apk')
OUTPUT_ALIGNED = os.path.join(PROJECT, 'app-debug-aligned.apk')
OUTPUT_FINAL = os.path.join(PROJECT, '..', '微生物学做题练习.apk')

# Tools
AAPT2 = os.path.join(BUILD_TOOLS, 'aapt2.exe')
D8 = os.path.join(BUILD_TOOLS, 'd8.bat')
ZIPALIGN = os.path.join(BUILD_TOOLS, 'zipalign.exe')
APKSIGNER = os.path.join(BUILD_TOOLS, 'apksigner.bat')
ADB = os.path.join(ANDROID_HOME, 'platform-tools', 'adb.exe')

# Debug keystore
KEYSTORE = os.path.join(os.path.expanduser('~'), '.android', 'debug.keystore')
KEYSTORE_PASS = 'android'
KEY_ALIAS = 'androiddebugkey'
KEY_PASS = 'android'

ECJ_JAR = r'C:\tmp\ecj.jar'
# Use Java 17 JRE to run ecj (ecj 3.33 needs Java 11+)
JAVA_EXE = r'C:\Users\Luozirui\.lunarclient\jre\4dcd188552ce8876d5e55e1f6d22505109bfa4cb\zulu17.34.19-ca-jre17.0.3-win_x64\bin\java.exe'

BUILD_DIR = os.path.join('C:', os.sep, 'tmp', 'apk-build')
COMPILED_RES = os.path.join(BUILD_DIR, 'compiled_res')
DEX_OUT = os.path.join(BUILD_DIR, 'classes.dex')
CLASSES_DIR = os.path.join(BUILD_DIR, 'classes')
APK_BASE = os.path.join(BUILD_DIR, 'apk_base')

os.makedirs(COMPILED_RES, exist_ok=True)
os.makedirs(CLASSES_DIR, exist_ok=True)
os.makedirs(APK_BASE, exist_ok=True)


def run(cmd, desc):
    print(f'  {desc}...')
    result = subprocess.run(cmd, capture_output=True, shell=True,
                            env={**os.environ, 'JAVA_HOME': JAVA_HOME})
    if result.returncode != 0:
        stderr = (result.stderr or b'').decode('utf-8', errors='replace')
        stdout = (result.stdout or b'').decode('utf-8', errors='replace')
        print(f'  ERROR: {stderr.strip()[:500]}')
        print(f'  stdout: {stdout.strip()[:200]}')
        sys.exit(1)
    out = (result.stdout or b'').decode('utf-8', errors='replace').strip()
    if out:
        print(f'    -> {out[:120]}')
    return result


def generate_keystore():
    """Generate debug keystore if not exists."""
    os.makedirs(os.path.dirname(KEYSTORE), exist_ok=True)
    if os.path.exists(KEYSTORE):
        print(f'  Keystore exists: {KEYSTORE}')
        return
    print('  Generating debug keystore...')
    # keytool is in JDK bin; use Java 8 JRE's keytool (JRE includes keytool)
    keytool = r'C:\Program Files\Java\jre1.8.0_441\bin\keytool.exe'
    cmd = (f'"{keytool}" -genkey -v -keystore "{KEYSTORE}" '
           f'-storepass {KEYSTORE_PASS} -keypass {KEY_PASS} '
           f'-alias {KEY_ALIAS} -keyalg RSA -keysize 2048 -validity 10000 '
           f'-dname "CN=Android Debug,O=Android,C=US"')
    subprocess.run(cmd, shell=True, capture_output=True)
    print('  Keystore generated.')


# ── Step 1: Generate keystore ──
print('[1/6] Generate keystore')
generate_keystore()

# ── Step 2: Compile resources with aapt2 ──
print('[2/6] Compile resources (aapt2)')
flat_res = os.path.join(BUILD_DIR, 'flat_res')
os.makedirs(flat_res, exist_ok=True)

# Compile each resource file
for root, dirs, files in os.walk(RES_DIR):
    for f in files:
        if f.endswith('.xml') or f.endswith('.png'):
            src = os.path.join(root, f)
            rel = os.path.splitext(os.path.relpath(src, RES_DIR))[0]
            dst = os.path.join(flat_res, rel + '.flat')
            run(f'"{AAPT2}" compile -o "{flat_res}" "{src}"', f'Compile {rel}')

# Link resources — output directly to APK file
linked_res_apk = os.path.join(BUILD_DIR, 'linked_res.apk')

flat_files = []
for root, dirs, files in os.walk(flat_res):
    for f in files:
        if f.endswith('.flat'):
            flat_files.append(os.path.join(root, f))

flat_args = ' '.join(f'"{x}"' for x in flat_files)
manifest_xml = os.path.join(BUILD_DIR, 'AndroidManifest.xml')
shutil.copy(MANIFEST, manifest_xml)

run(f'"{AAPT2}" link -o "{linked_res_apk}" -I "{ANDROID_JAR}" '
    f'--manifest "{manifest_xml}" {flat_args} '
    f'--auto-add-overlay',
    'Link resources')

print(f'  Linked APK size: {os.path.getsize(linked_res_apk):,} bytes')

# ── Step 3: Compile Java sources ──
print('[3/6] Compile Java (javac)')
java_files = []
for root, dirs, files in os.walk(JAVA_SRC):
    for f in files:
        if f.endswith('.java'):
            java_files.append(os.path.join(root, f))

java_args = ' '.join(f'"{x}"' for x in java_files)
# Use Eclipse Compiler for Java (ecj) — works with JRE, no JDK needed
run(f'"{JAVA_EXE}" -jar "{ECJ_JAR}" -d "{CLASSES_DIR}" '
    f'-classpath "{ANDROID_JAR}" -source 1.8 -target 1.8 '
    f'-warn:none {java_args}',
    f'Compile {len(java_files)} Java file(s)')

# ── Step 4: Convert to dex (d8) ──
# First jar up the classes, then pass the jar to d8
print('[4/6] Convert to dex (d8)')
d8_jar = os.path.join(BUILD_TOOLS, 'lib', 'd8.jar')
classes_jar = os.path.join(BUILD_DIR, 'classes.jar')

# Create a jar from compiled classes
import zipfile as zf_jar
with zf_jar.ZipFile(classes_jar, 'w') as zj:
    for root, dirs, files in os.walk(CLASSES_DIR):
        for f in files:
            if f.endswith('.class'):
                src = os.path.join(root, f)
                arc = os.path.relpath(src, CLASSES_DIR).replace('\\', '/')
                zj.write(src, arc)
print(f'  Created {classes_jar} with class files')

# d8 output to a directory containing classes.dex
dex_jar = os.path.join(BUILD_DIR, 'classes_dex.jar')
run(f'"{JAVA_EXE}" -Xmx1024M -cp "{d8_jar}" com.android.tools.r8.D8 '
    f'--output "{dex_jar}" --lib "{ANDROID_JAR}" --min-api 21 '
    f'"{classes_jar}"',
    'd8 dex conversion')

dex_dir_contents = os.listdir(DEX_OUT) if os.path.isdir(DEX_OUT) else []
print(f'  D8 output: {dex_dir_contents}')

# ── Step 5: Package APK ──
print('[5/6] Package APK')
# Prepare APK contents
apk_contents = os.path.join(BUILD_DIR, 'apk_contents')
if os.path.exists(apk_contents):
    shutil.rmtree(apk_contents)
os.makedirs(apk_contents, exist_ok=True)

# Unzip the linked resources into apk_contents
import zipfile
with zipfile.ZipFile(linked_res_apk, 'r') as z:
    z.extractall(apk_contents)

# Add dex from the d8 output jar
classes_dex_dst = os.path.join(apk_contents, 'classes.dex')
# The dex jar from d8 is at dex_jar (a zip). Extract classes.dex from it.
with zipfile.ZipFile(dex_jar, 'r') as dz:
    dz.extract('classes.dex', apk_contents)
print(f'  Extracted classes.dex from dex jar')

# Add assets (the quiz HTML/CSS/JS)
assets_dst = os.path.join(apk_contents, 'assets')
if os.path.exists(assets_dst):
    shutil.rmtree(assets_dst)
shutil.copytree(ASSETS_DIR, assets_dst)
print(f'  Copied assets: {os.path.basename(ASSETS_DIR)}')

# Create unsigned APK (zip)
import zipfile as zf2
if os.path.exists(OUTPUT_UNSIGNED):
    os.remove(OUTPUT_UNSIGNED)

with zf2.ZipFile(OUTPUT_UNSIGNED, 'w', zf2.ZIP_DEFLATED) as zout:
    for root, dirs, files in os.walk(apk_contents):
        for f in files:
            src = os.path.join(root, f)
            arc = os.path.relpath(src, apk_contents).replace('\\', '/')
            zout.write(src, arc)

print(f'  Created: {OUTPUT_UNSIGNED}')

# ── Step 6: Zipalign + Sign ──
print('[6/6] Zipalign and Sign')
run(f'"{ZIPALIGN}" -f 4 "{OUTPUT_UNSIGNED}" "{OUTPUT_ALIGNED}"', 'zipalign')

final_path = os.path.abspath(OUTPUT_FINAL)
run(f'"{APKSIGNER}" sign --ks "{KEYSTORE}" --ks-pass pass:{KEYSTORE_PASS} '
    f'--ks-key-alias {KEY_ALIAS} --key-pass pass:{KEY_PASS} '
    f'--out "{final_path}" "{OUTPUT_ALIGNED}"',
    'apksigner')

size = os.path.getsize(final_path)
print(f'\n[OK] APK built successfully!')
print(f'  Path: {final_path}')
print(f'  Size: {size:,} bytes ({size / 1024 / 1024:.1f} MB)')
print(f'\nInstall on device:')
print(f'  1. Copy the APK to your phone')
print(f'  2. Open the APK file on your phone')
print(f'  3. Allow "install from unknown sources" if prompted')
