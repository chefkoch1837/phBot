import QtBind
from threading import Timer
from phBot import *
import os
import phBotChat
import time
import sqlite3
import glob

# ============================================================
# ============================================================
Plugin = 'BetterTraining'
PluginVersion = '0.9 Beta'

# ============================================================
# Globals
# ============================================================
enabled = False
solo = False
members = 8
levelOffset = 0
spots = []
use_monstername_as_name = False
use_mob_level = False

# Character specific settings
character_settings = {}
loading_character_settings = False
current_character = None
hometown_enabled = True
buy_items_enabled = False
buy_keep_town_gold_enabled = False
BUY_GOLD_THRESHOLD = 0

# Area change state
area_change_pending = False
pending_area = None
area_change_timer = None
area_change_stage = 0
# 1 = local STOP -> delay 1
# 2 = local CHANGE AREA/RANGE -> delay 2
# 3 = local START done -> chat STOP -> delay 1
# 4 = forced town return -> wait 10000 ms -> local START
# 5 = chat SETPOS/SETRADIUS -> delay 2
area_change_death_remaining = None
DEATH_WAIT_TIMEOUT = 30
RETURN_TO_TOWN_START_DELAY = 10  # seconds

# Chat Control integration
xcontrol_enabled = False
xcontrol_stop_command = 'STOP'
xcontrol_stop_delay_ms = 1000
xcontrol_setpos_command = 'SETPOS x% y% r% z%'
xcontrol_setrange_command = 'SETRADIUS %Range'
xcontrol_start_delay_ms = 1000
xcontrol_start_command = 'START'

CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    Plugin + '_Config.txt'
)

# ============================================================
# GUI Tab 1
# ============================================================
tab1 = QtBind.init(__name__, Plugin)

x = -1
y = 0

QtBind.createLabel(
    tab1,
    '<b>Enable Spot Changer</b>',
    x + 25,
    y + 6
)
checkEnable = QtBind.createCheckBox(
    tab1,
    'checkEnable_clicked',
    '',
    x - 2,
    y
)

checkSolo = QtBind.createCheckBox(
    tab1,
    'checkSolo_clicked',
    'Solo',
    x - 2,
    y + 20
)

# ============================================================
# Spot Editor
# ============================================================
y = 45

QtBind.createLabel(tab1, 'Race:', x + 3, y)
comboRace = QtBind.createCombobox(
    tab1,
    x + 45,
    y - 3,
    80,
    20
)
QtBind.append(tab1, comboRace, 'All')
QtBind.append(tab1, comboRace, 'Europe')
QtBind.append(tab1, comboRace, 'Chinese')

y += 21
QtBind.createLabel(tab1, 'Level:', x + 3, y)
editLevel = QtBind.createLineEdit(
    tab1,
    '1',
    x + 45,
    y - 3,
    80,
    20
)
checkMobLevel = QtBind.createCheckBox(
    tab1,
    'useMobLevel_clicked',
    'Use Mob Lvl',
    x + 122,
    y - 5
)

y += 21
QtBind.createLabel(tab1, 'Name:', x + 3, y)
editName = QtBind.createLineEdit(
    tab1,
    '',
    x + 45,
    y - 3,
    80,
    20
)
checkMonsterName = QtBind.createCheckBox(
    tab1,
    'useMonsterName_clicked',
    'Use Mobname',
    x + 122,
    y - 5
)

y += 21
QtBind.createLabel(tab1, 'Range:', x + 3, y)
editRange = QtBind.createLineEdit(
    tab1,
    '75',
    x + 45,
    y - 3,
    80,
    20
)

y += 21
buttonAdd = QtBind.createButton(
    tab1,
    'addSpot_clicked',
    'Add Current Position',
    x,
    y
)

buttonDelete = QtBind.createButton(
    tab1,
    'deleteSpot_clicked',
    'Delete Selected',
    x + 125,
    y
)

# ============================================================
# Spot List
# ============================================================
listX = 230
listY = 5

QtBind.createLabel(
    tab1,
    'Training Spots:',
    listX,
    listY
)

SPOT_HEADER = 'ID   Lvl  Race   Spot (Region,X,Y,Z)  Range  Name'
QtBind.createLabel(
    tab1,
    SPOT_HEADER,
    listX + 5,
    listY + 22
)

spotList = QtBind.createList(
    tab1,
    listX - 5,
    listY + 35,
    495,
    200
)

# ============================================================
# Action Buttons (Walk, Stop)
# ============================================================
settingsY = 155

btn_walk = QtBind.createButton(tab1, 'btn_walk_clicked', '   Walk to Position     ', 0, settingsY - 3)
btn_stop = QtBind.createButton(tab1, 'btn_stop_clicked', '        Stop         ', 125, settingsY - 3)

settingsY += 24
QtBind.createLabel(
    tab1,
    'Party Members:',
    3,
    settingsY
)

editMembers = QtBind.createLineEdit(
    tab1,
    '8',
    85,
    settingsY - 3,
    30,
    20
)

settingsY += 24
QtBind.createLabel(
    tab1,
    'Level Offset:',
    3,
    settingsY
)

editLevelOffset = QtBind.createLineEdit(
    tab1,
    '0',
    85,
    settingsY - 3,
    30,
    20
)

# ============================================================
# Chat Control Spot Change
# ============================================================
y += 122
QtBind.createLabel(tab1, 'Send spot change command via party chat.   Variables( Y= %y / X= %x / Z= %z / Region= %r / Range= %Range )', x + 25, y + 6)
checkXControl = QtBind.createCheckBox(
    tab1,
    'checkXControl_clicked',
    '',
    x - 2,
    y
)

QtBind.createLabel(tab1, 'Stop Bot Command', x + 8, y + 25)
editXControlStop = QtBind.createLineEdit(
    tab1,
    'STOP',
    x,
    y + 40,
    110,
    20
)

QtBind.createLabel(tab1, 'Delay (ms)', x + 115, y + 25)
editXControlDelay1 = QtBind.createLineEdit(
    tab1,
    '1000',
    x + 113,
    y + 40,
    60,
    20
)

QtBind.createLabel(tab1, 'Spot change Command', x + 205, y + 25)
editXControlSetPos = QtBind.createLineEdit(
    tab1,
    'SETPOS x% y% r% z%',
    x + 176,
    y + 40,
    185,
    20
)

QtBind.createLabel(tab1, 'Range change Command', x + 390, y + 25)
editXControlSetRange = QtBind.createLineEdit(
    tab1,
    'SETRADIUS %Range',
    x + 365,
    y + 40,
    185,
    20
)

QtBind.createLabel(tab1, 'Delay (ms)', x + 558, y + 25)
editXControlDelay2 = QtBind.createLineEdit(
    tab1,
    '1000',
    x + 555,
    y + 40,
    60,
    20
)

QtBind.createLabel(tab1, 'Start Bot Command', x + 622, y + 25)
editXControlStart = QtBind.createLineEdit(
    tab1,
    'START',
    x + 620,
    y + 40,
    98,
    20
)

buttonSaveXControl = QtBind.createButton(
    tab1,
    'saveXControl_clicked',
    'Save',
    x + 722,
    y + 38
)

# ============================================================
# Helper
# ============================================================
def get_character_name():
    try:
        data = get_character_data()
        if not data:
            return None
        if 'name' in data:
            return data['name']
    except:
        pass
    return None

def get_server_name():
    try:
        data = get_character_data() or {}
        for key in ('server', 'servername', 'server_name'):
            value = data.get(key)
            if value:
                return str(value).strip()
    except Exception:
        pass
    try:
        data = get_client() or {}
        for key in ('server', 'servername', 'server_name'):
            value = data.get(key)
            if value:
                return str(value).strip()
    except Exception:
        pass
    return 'UnknownServer'

def get_character_key(character=None, server=None):
    character = str(character or get_character_name() or '').strip()
    server = str(server or get_server_name() or 'UnknownServer').strip()
    if not character:
        return None
    return '%s_%s' % (server, character)

# ============================================================
# Default Character Settings
# ============================================================
def get_default_character_settings():
    return {
        'enabled': False,
        'solo': False,
        'members': 8,
        'levelOffset': 0,
        'xcontrol_enabled': False,
        'xcontrol_stop_command': 'STOP',
        'xcontrol_stop_delay_ms': 500,
        'xcontrol_setpos_command': 'SETPOS x% y% r% z%',
        'xcontrol_setrange_command': 'SETRADIUS %Range',
        'xcontrol_start_delay_ms': 500,
        'xcontrol_start_command': 'START',
        'hometown_enabled': False,
        'buy_items_enabled': False,
        'buy_gold_threshold': 0,
        'buy_keep_town_gold_enabled': False,
        'bought_items': [],
        'hometown_rules': _hometown_character_defaults() if 'hometown_rules' in globals() else [dict(r) for r in HOMETOWN_DEFAULTS]
    }

def finish_loading_character_settings():
    global loading_character_settings
    loading_character_settings = False

# ============================================================
# Load & Save Character Settings
# ============================================================
def load_character_settings():
    global loading_character_settings
    global enabled
    global solo
    global members
    global levelOffset
    global current_character
    global hometown_enabled
    global buy_items_enabled
    global BUY_GOLD_THRESHOLD
    global buy_keep_town_gold_enabled
    global xcontrol_enabled
    global xcontrol_stop_command
    global xcontrol_stop_delay_ms
    global xcontrol_setpos_command
    global xcontrol_setrange_command
    global xcontrol_start_delay_ms
    global xcontrol_start_command
    global auto_settings_signature

    character_name = get_character_name()
    if not character_name:
        return
    character = get_character_key(character_name)
    if not character:
        return

    legacy_name = character_name
    migrated_legacy_runtime = False
    if legacy_name in character_settings and legacy_name != character:
        legacy_settings = character_settings.pop(legacy_name)
        if character not in character_settings:
            character_settings[character] = legacy_settings
        elif isinstance(legacy_settings, dict):
            for key, value in legacy_settings.items():
                if key not in character_settings[character]:
                    character_settings[character][key] = value
        migrated_legacy_runtime = True

    current_character = character
    loading_character_settings = True

    if character not in character_settings:
        character_settings[character] = get_default_character_settings()

    settings = character_settings[character]
    enabled = settings['enabled']
    hometown_enabled = bool(settings.get('hometown_enabled', True))
    buy_items_enabled = bool(settings.get('buy_items_enabled', False))
    buy_keep_town_gold_enabled = bool(settings.get('buy_keep_town_gold_enabled', False))

    try:
        BUY_GOLD_THRESHOLD = max(0, int(settings.get('buy_gold_threshold', 0)))
    except Exception:
        BUY_GOLD_THRESHOLD = 0

    solo = settings['solo']
    members = settings['members']
    levelOffset = settings['levelOffset']

    xcontrol_enabled = settings.get('xcontrol_enabled', False)
    xcontrol_stop_command = settings.get('xcontrol_stop_command', 'STOP')
    xcontrol_stop_delay_ms = clamp_delay(settings.get('xcontrol_stop_delay_ms', 500))
    xcontrol_setpos_command = settings.get('xcontrol_setpos_command', 'SETPOS x% y% r% z%')
    xcontrol_setrange_command = settings.get('xcontrol_setrange_command', 'SETRADIUS %Range')
    xcontrol_start_delay_ms = clamp_delay(settings.get('xcontrol_start_delay_ms', 500))
    xcontrol_start_command = settings.get('xcontrol_start_command', 'START')

    QtBind.setChecked(tab1, checkEnable, enabled)
    QtBind.setChecked(tab1, checkSolo, solo)
    QtBind.setText(tab1, editMembers, str(members))
    QtBind.setText(tab1, editLevelOffset, str(levelOffset))
    QtBind.setChecked(tab1, checkXControl, xcontrol_enabled)

    if 'buy_items_check' in globals() and 'tab2' in globals():
        QtBind.setChecked(tab2, buy_items_check, buy_items_enabled)
    if 'buy_gold_threshold_edit' in globals() and 'tab2' in globals():
        QtBind.setText(tab2, buy_gold_threshold_edit, str(BUY_GOLD_THRESHOLD))
    if 'buy_keep_town_gold_check' in globals() and 'tab2' in globals():
        QtBind.setChecked(tab2, buy_keep_town_gold_check, buy_keep_town_gold_enabled)

    load_xcontrol_tab1()
    if 'tab2' in globals():
        _hometown_refresh_tab1()

    auto_settings_signature = None
    Timer(1.0, finish_loading_character_settings, []).start()
    if migrated_legacy_runtime:
        save_config()
    log('%s: Settings for [%s] loaded' % (Plugin, character))

def save_character_settings():
    global current_character
    global buy_items_enabled
    global BUY_GOLD_THRESHOLD
    global buy_keep_town_gold_enabled

    if not current_character:
        current_character = get_character_key()
    if not current_character:
        return

    settings = character_settings.get(
        current_character,
        get_default_character_settings()
    )

    settings['enabled'] = enabled
    settings['solo'] = solo
    settings['members'] = members
    settings['levelOffset'] = levelOffset
    settings['buy_items_enabled'] = bool(buy_items_enabled)
    settings['buy_keep_town_gold_enabled'] = bool(buy_keep_town_gold_enabled)

    try:
        BUY_GOLD_THRESHOLD = max(0, int(BUY_GOLD_THRESHOLD))
    except Exception:
        BUY_GOLD_THRESHOLD = 0
    settings['buy_gold_threshold'] = BUY_GOLD_THRESHOLD

    settings['xcontrol_enabled'] = xcontrol_enabled
    settings['xcontrol_stop_command'] = xcontrol_stop_command
    settings['xcontrol_stop_delay_ms'] = xcontrol_stop_delay_ms
    settings['xcontrol_setpos_command'] = xcontrol_setpos_command
    settings['xcontrol_setrange_command'] = xcontrol_setrange_command
    settings['xcontrol_start_delay_ms'] = xcontrol_start_delay_ms
    settings['xcontrol_start_command'] = xcontrol_start_command

    character_settings[current_character] = settings

# ============================================================
# Action Buttons Logic
# ============================================================
def btn_walk_clicked():
    index = QtBind.currentIndex(tab1, spotList)
    if index < 0 or index >= len(spots):
        log('%s: Please select a spot from the list first!' % Plugin)
        return

    spot = spots[index]
    log('%s: Generating path to [%s]...' % (Plugin, spot['name']))

    stop_script()
    stop_bot()
    stop_trace()
    stop_trade()

    try:
        lines = generate_script(spot['r'], spot['x'], spot['y'], spot['z'])
        if lines:
            script_str = '\n'.join([str(line).strip() for line in lines if str(line).strip()])
            start_script(script_str)
            log('%s: Walking to spot...' % Plugin)
        else:
            log('%s: Could not generate path! Maybe already there or unreachable.' % Plugin)
    except Exception as ex:
        log('%s: Walk error: %s' % (Plugin, ex))

def btn_stop_clicked():
    stop_script()
    stop_bot()
    stop_trace()
    stop_trade()
    log('%s: All actions stopped by user.' % Plugin)

# ============================================================
# Tab 1 Callbacks
# ============================================================
def checkEnable_clicked(checked):
    global enabled
    if loading_character_settings:
        return
    enabled = bool(checked)
    save_character_settings()
    save_config()
    if enabled:
        log('%s: Plugin enabled for [%s]' % (Plugin, current_character))
    else:
        log('%s: Plugin disabled for [%s]' % (Plugin, current_character))

def checkSolo_clicked(checked):
    global solo
    if loading_character_settings:
        return
    solo = bool(checked)
    save_character_settings()
    save_config()
    if solo:
        log('%s: Solo mode enabled for [%s]' % (Plugin, current_character))
    else:
        log('%s: Party mode enabled for [%s]' % (Plugin, current_character))

def saveMembers_clicked():
    global members
    value = QtBind.text(tab1, editMembers)
    try:
        value = int(value)
    except:
        log('%s: Invalid party member value!' % Plugin)
        QtBind.setText(tab1, editMembers, str(members))
        return
    value = max(1, min(8, value))
    members = value
    QtBind.setText(tab1, editMembers, str(members))
    save_character_settings()
    save_config()
    log('%s: Party members for [%s] = %d' % (Plugin, current_character, members))

def saveLevelOffset_clicked():
    global levelOffset
    value = QtBind.text(tab1, editLevelOffset)
    try:
        value = int(value)
    except:
        log('%s: Invalid level offset!' % Plugin)
        QtBind.setText(tab1, editLevelOffset, str(levelOffset))
        return
    value = max(-255, min(255, value))
    levelOffset = value
    QtBind.setText(tab1, editLevelOffset, str(levelOffset))
    save_character_settings()
    save_config()
    log('%s: Level offset for [%s] = %+d' % (Plugin, current_character, levelOffset))

# ============================================================
# Chat Control Settings
# ============================================================
def clamp_delay(value):
    try:
        value = int(value)
    except:
        return 500
    return max(0, min(60000, value))

def load_xcontrol_tab1():
    QtBind.setText(tab1, editXControlStop, xcontrol_stop_command)
    QtBind.setText(tab1, editXControlDelay1, str(xcontrol_stop_delay_ms))
    QtBind.setText(tab1, editXControlSetPos, xcontrol_setpos_command)
    QtBind.setText(tab1, editXControlSetRange, xcontrol_setrange_command)
    QtBind.setText(tab1, editXControlDelay2, str(xcontrol_start_delay_ms))
    QtBind.setText(tab1, editXControlStart, xcontrol_start_command)

def read_xcontrol_tab1():
    global xcontrol_stop_command
    global xcontrol_stop_delay_ms
    global xcontrol_setpos_command
    global xcontrol_setrange_command
    global xcontrol_start_delay_ms
    global xcontrol_start_command

    xcontrol_stop_command = QtBind.text(tab1, editXControlStop).strip()
    xcontrol_stop_delay_ms = clamp_delay(QtBind.text(tab1, editXControlDelay1))
    xcontrol_setpos_command = QtBind.text(tab1, editXControlSetPos).strip()
    xcontrol_setrange_command = QtBind.text(tab1, editXControlSetRange).strip()
    xcontrol_start_delay_ms = clamp_delay(QtBind.text(tab1, editXControlDelay2))
    xcontrol_start_command = QtBind.text(tab1, editXControlStart).strip()

def saveXControl_clicked():
    if not current_character:
        log('%s: No active character. Chat settings were not saved.' % Plugin)
        return
    read_xcontrol_tab1()
    save_character_settings()
    save_config()
    log('%s: Chat Control settings saved for [%s].' % (Plugin, current_character))

def checkXControl_clicked(checked):
    global xcontrol_enabled
    if loading_character_settings:
        return
    xcontrol_enabled = bool(checked)
    read_xcontrol_tab1()
    save_character_settings()
    save_config()
    log('%s: Spot change %s for [%s].' % (Plugin, 'enabled' if checked else 'disabled', current_character))

def send_xcontrol_party(message):
    if not xcontrol_enabled:
        return False
    if not message:
        return True
    try:
        result = phBotChat.Party(message)
        if result:
            log('%s: Party command sent: [%s]' % (Plugin, message))
            return True
        log('%s: Failed to send Party command: [%s]' % (Plugin, message))
    except Exception as ex:
        log('%s: Chat error: %s' % (Plugin, ex))
    return False

def format_xcontrol_command(template, spot):
    if not spot:
        return template
    values = {
        'x': str(spot.get('x', '')),
        'y': str(spot.get('y', '')),
        'r': str(spot.get('r', '')),
        'z': str(spot.get('z', '')),
        'region': str(spot.get('r', '')),
        'radius': str(spot.get('radius', '')),
        'range': str(spot.get('radius', '')),
        'Range': str(spot.get('radius', '')),
        'spot': str(spot.get('name', '')),
        'level': str(spot.get('level', '')),
        'race': str(spot.get('race', '')),
        'char': str(get_character_name() or '')
    }
    command = template
    replacements = [
        ('%Range%', values['Range']),
        ('%Range', values['Range']),
        ('%X%', values['x']),
        ('%Y%', values['y']),
        ('%R%', values['r']),
        ('%Z%', values['z']),
        ('x%', values['x']),
        ('y%', values['y']),
        ('r%', values['r']),
        ('z%', values['z']),
        ('{x}', values['x']),
        ('{y}', values['y']),
        ('{r}', values['r']),
        ('{z}', values['z']),
        ('{region}', values['region']),
        ('{radius}', values['radius']),
        ('{range}', values['range']),
        ('{Range}', values['Range']),
        ('{spot}', values['spot']),
        ('{level}', values['level']),
        ('{race}', values['race']),
        ('{char}', values['char'])
    ]
    for placeholder, value in replacements:
        command = command.replace(placeholder, value)
    return command

def send_xcontrol_stop(spot=None):
    if xcontrol_enabled:
        send_xcontrol_party(format_xcontrol_command(xcontrol_stop_command, spot))

def send_xcontrol_setpos(spot):
    if xcontrol_enabled and spot:
        send_xcontrol_party(format_xcontrol_command(xcontrol_setpos_command, spot))

def send_xcontrol_setrange(spot):
    if xcontrol_enabled and spot:
        send_xcontrol_party(format_xcontrol_command(xcontrol_setrange_command, spot))

def send_xcontrol_start(spot=None):
    if xcontrol_enabled:
        send_xcontrol_party(format_xcontrol_command(xcontrol_start_command, spot))

# ============================================================
# Spot Management
# ============================================================
def clamp_number(value, minimum, maximum):
    try:
        value = int(value)
    except:
        return None
    return max(minimum, min(maximum, value))

def useMonsterName_clicked(checked):
    global use_monstername_as_name
    use_monstername_as_name = bool(checked)
    save_config()

def useMobLevel_clicked(checked):
    global use_mob_level
    use_mob_level = bool(checked)
    save_config()

def _resolve_monster_info(monster, db_conn=None):
    if not isinstance(monster, dict):
        return None, None
    name = str(monster.get('name') or '').strip()
    servername = str(monster.get('servername') or '').strip()
    model_id = monster.get('model')
    level = monster.get('level')

    if model_id is not None:
        try:
            m_data = get_monster(int(model_id))
            if isinstance(m_data, dict):
                if not name:
                    name = str(m_data.get('name') or '').strip()
                if not servername:
                    servername = str(m_data.get('servername') or '').strip()
                if level is None:
                    level = m_data.get('level')
        except Exception:
            pass

    if (not name or level is None) and servername:
        try:
            m_data = get_monster_string(servername)
            if isinstance(m_data, dict):
                if not name:
                    name = str(m_data.get('name') or '').strip()
                if level is None:
                    level = m_data.get('level')
        except Exception:
            pass

    if (not name or level is None) and db_conn is not None:
        try:
            row = None
            if model_id is not None:
                row = db_conn.execute('SELECT name, servername, level FROM monsters WHERE id=? LIMIT 1', (int(model_id),)).fetchone()
            if not row and servername:
                row = db_conn.execute('SELECT name, servername, level FROM monsters WHERE servername=? LIMIT 1', (servername,)).fetchone()
            if row:
                if not name and row[0]:
                    name = str(row[0]).strip()
                if not servername and row[1]:
                    servername = str(row[1]).strip()
                if level is None and row[2] is not None:
                    level = int(row[2])
        except Exception:
            pass

    if not name and servername:
        name = servername

    try:
        level = int(level) if level is not None else None
        if level is not None and (level < 1 or level > 255):
            level = None
    except (TypeError, ValueError):
        level = None
    return (name or None), level

def get_most_common_monster_name():
    try:
        monsters = get_monsters()
    except Exception as ex:
        log('%s: get_monsters() error: %s' % (Plugin, ex))
        return None
    if not monsters:
        log('%s: get_monsters() returned 0 nearby monsters (stand next to live mobs).' % Plugin)
        return None
    values = monsters.values() if isinstance(monsters, dict) else monsters
    db_path = _buy_items_db_path((get_client() or {}).get('path', ''))
    db_conn = sqlite3.connect(db_path) if db_path and os.path.exists(db_path) else None
    counts = {}
    try:
        for monster in values:
            name, _ = _resolve_monster_info(monster, db_conn)
            if name:
                counts[name] = counts.get(name, 0) + 1
    finally:
        if db_conn:
            db_conn.close()
    if not counts:
        return None
    return max(counts, key=counts.get)

def get_most_common_monster_level():
    try:
        monsters = get_monsters()
    except Exception as ex:
        log('%s: get_monsters() error: %s' % (Plugin, ex))
        return None
    if not monsters:
        log('%s: get_monsters() returned 0 nearby monsters (stand next to live mobs).' % Plugin)
        return None
    values = monsters.values() if isinstance(monsters, dict) else monsters
    db_path = _buy_items_db_path((get_client() or {}).get('path', ''))
    db_conn = sqlite3.connect(db_path) if db_path and os.path.exists(db_path) else None
    records = []
    key_counts = {}
    try:
        for monster in values:
            if not isinstance(monster, dict):
                continue
            name, mob_level = _resolve_monster_info(monster, db_conn)
            if mob_level is None:
                continue
            group_key = name or str(monster.get('model') or monster.get('servername') or mob_level)
            records.append((group_key, mob_level))
            key_counts[group_key] = key_counts.get(group_key, 0) + 1
    finally:
        if db_conn:
            db_conn.close()
    if not records or not key_counts:
        return None
    most_common_key = max(key_counts, key=key_counts.get)
    level_counts = {}
    for group_key, mob_level in records:
        if group_key == most_common_key:
            level_counts[mob_level] = level_counts.get(mob_level, 0) + 1
    if not level_counts:
        return None
    return max(level_counts, key=level_counts.get)

def addSpot_clicked():
    race = QtBind.text(tab1, comboRace)
    if race not in ['Europe', 'Chinese', 'All']:
        log('%s: Invalid race!' % Plugin)
        return

    if bool(QtBind.isChecked(tab1, checkMobLevel)):
        mob_level = get_most_common_monster_level()
        if mob_level is None:
            log('%s: Use Mob Lvl is enabled, but no valid nearby monster levels were found.' % Plugin)
            return
        level = mob_level
        QtBind.setText(tab1, editLevel, str(level))
    else:
        level = clamp_number(QtBind.text(tab1, editLevel), 1, 255)
        if level is None:
            log('%s: Invalid level!' % Plugin)
            return

    if bool(QtBind.isChecked(tab1, checkMonsterName)):
        name = get_most_common_monster_name()
        if not name:
            log('%s: Use monstername as name is enabled, but no nearby monster names were found.' % Plugin)
            return
        QtBind.setText(tab1, editName, name)
    else:
        name = QtBind.text(tab1, editName).strip()
        if not name:
            log('%s: Please enter a spot name!' % Plugin)
            return

    radius = clamp_number(QtBind.text(tab1, editRange), 0, 255)
    if radius is None:
        log('%s: Invalid range!' % Plugin)
        return

    try:
        position = get_position()
        if not position:
            log('%s: Could not get current position!' % Plugin)
            return
        region = int(position['region'])
        pos_x = int(position['x'])
        pos_y = int(position['y'])
        pos_z = int(position['z'])
    except Exception as ex:
        log('%s: Error reading position: %s' % (Plugin, ex))
        return

    spot = {
        'race': race,
        'level': level,
        'name': name,
        'r': region,
        'x': pos_x,
        'y': pos_y,
        'z': pos_z,
        'radius': radius
    }
    spots.append(spot)
    spots.sort(key=lambda s: (s['level'], s['race']))
    save_config()
    refresh_spot_list()
    log('%s: Added spot [%s] Race=%s Level=%d Region=%d X=%d Y=%d Z=%d Range=%d' %
        (Plugin, name, race, level, region, pos_x, pos_y, pos_z, radius))
    QtBind.setText(tab1, editName, '')
    QtBind.setText(tab1, editLevel, '1')
    QtBind.setText(tab1, editRange, '50')

def deleteSpot_clicked():
    index = QtBind.currentIndex(tab1, spotList)
    if index < 0:
        log('%s: Please select a spot first!' % Plugin)
        return
    if index >= len(spots):
        return
    spot = spots[index]
    log('%s: Deleting spot [%s]' % (Plugin, spot['name']))
    del spots[index]
    save_config()
    refresh_spot_list()

def refresh_spot_list():
    QtBind.clear(tab1, spotList)
    nbsp = '\u00a0'
    rows = []
    for index, spot in enumerate(spots):
        rows.append({
            'id': str(index),
            'level': str(spot['level']),
            'race': str(spot['race']),
            'spot': 'Spot %d,%d,%d,%d' % (spot['r'], spot['x'], spot['y'], spot['z']),
            'range': str(spot['radius']),
            'name': str(spot['name'])
        })
    id_width = max((len(row['id']) for row in rows), default=2)
    level_width = max((len(row['level']) for row in rows), default=3)
    race_width = max((len(row['race']) for row in rows), default=len('Chinese'))
    spot_width = max((len(row['spot']) for row in rows), default=len('Spot (Region,X,Y,Z)'))
    range_width = max((len(row['range']) for row in rows), default=3)

    for row in rows:
        text = (
            row['id'] + nbsp * (id_width - len(row['id']) + 3) +
            'Lvl ' + row['level'] + nbsp * (level_width - len(row['level']) + 2) +
            'Race ' + row['race'] + nbsp * (race_width - len(row['race']) + 3) +
            row['spot'] + nbsp * (spot_width - len(row['spot']) + 2) +
            'Range ' + row['range'] + nbsp * (range_width - len(row['range']) + 2) +
            row['name']
        )
        QtBind.append(tab1, spotList, text)

# ============================================================
# Training Area & Party Handling
# ============================================================
def get_character_race():
    try:
        data = get_character_data()
        return 'Europe' if data.get('model', 0) > 10000 else 'Chinese'
    except Exception as ex:
        log('%s: Race detection error: %s' % (Plugin, ex))
        return None

def get_available_spots():
    race = get_character_race()
    available = []
    for spot in spots:
        if spot['race'] == race or spot['race'] == 'All':
            available.append(spot)
    return available

def is_character_alive():
    try:
        data = get_character_data()
    except:
        return False
    if not data:
        return False
    return not data.get('dead', False)

def cancel_area_change_timer():
    global area_change_timer
    if area_change_timer is not None:
        try:
            area_change_timer.cancel()
        except:
            pass
    area_change_timer = None

def reset_area_change_death_timer():
    global area_change_death_remaining
    area_change_death_remaining = None

def schedule_area_change(delay_seconds):
    global area_change_timer
    cancel_area_change_timer()
    area_change_timer = Timer(max(0.05, delay_seconds), continue_area_change, [])
    area_change_timer.start()

def return_to_town_after_death_timeout():
    global area_change_pending
    global area_change_stage
    global area_change_death_remaining

    cancel_area_change_timer()
    area_change_pending = True
    area_change_stage = 4
    area_change_death_remaining = None

    log(
        '%s: Character stayed dead for %d seconds. Returning to town. '
        'Local bot will start again after %d ms.'
        % (Plugin, DEATH_WAIT_TIMEOUT, int(RETURN_TO_TOWN_START_DELAY * 1000))
    )

    try:
        stop_bot()
    except:
        pass
    try:
        inject_joymax(0x3053, b'\x01', False)
    except Exception as ex:
        log('%s: Error returning character to town: %s' % (Plugin, ex))

    Timer(RETURN_TO_TOWN_START_DELAY, finish_forced_return, []).start()

def start_chat_area_change(area):
    global area_change_stage
    global area_change_pending

    if not xcontrol_enabled:
        area_change_pending = False
        return
    area_change_stage = 3
    send_xcontrol_stop(area)
    schedule_area_change(xcontrol_stop_delay_ms / 1000.0)

def continue_chat_area_change():
    global area_change_pending
    global pending_area
    global area_change_stage
    global area_change_timer

    area_change_timer = None
    if not area_change_pending or not pending_area:
        return
    area = pending_area
    if area_change_stage == 3:
        send_xcontrol_setpos(area)
        send_xcontrol_setrange(area)
        area_change_stage = 5
        schedule_area_change(xcontrol_start_delay_ms / 1000.0)
        return
    if area_change_stage == 5:
        send_xcontrol_start(area)
        log('%s: Local bot + Chat area change sequence completed for [%s].' % (Plugin, area['name']))
        area_change_pending = False
        pending_area = None
        area_change_stage = 0
        reset_area_change_death_timer()
        return

def finish_forced_return():
    global area_change_stage
    global area_change_pending
    global pending_area

    try:
        if _bot_is_running():
            started = True
        else:
            started = start_bot()
        if not started and not _bot_is_running():
            log('%s: Local bot did not start after forced return; retrying in 3 seconds.' % Plugin)
            Timer(3.0, finish_forced_return, []).start()
            return
        log('%s: Local bot started after forced return to town.' % Plugin)
    except Exception as ex:
        log('%s: Error starting local bot after forced return: %s. Retrying in 3 seconds.' % (Plugin, ex))
        Timer(3.0, finish_forced_return, []).start()
        return

    if enabled and xcontrol_enabled and area_change_pending and pending_area:
        start_chat_area_change(pending_area)
    else:
        area_change_pending = False
        pending_area = None
        area_change_stage = 0
        reset_area_change_death_timer()

def check_level(level):
    global area_change_pending

    if globals().get('buy_items_state') is not None or globals().get('hometown_state') is not None:
        return

    if area_change_pending:
        return

    available_spots = get_available_spots()
    if not available_spots:
        log('%s: No valid training spots for this character!' % Plugin)
        return

    effective_level = max(1, min(255, level + levelOffset))
    eligible_spots = [spot for spot in available_spots if spot['level'] <= effective_level]
    if eligible_spots:
        newArea = max(eligible_spots, key=lambda spot: spot['level'])
    else:
        newArea = min(available_spots, key=lambda spot: spot['level'])

    currentArea = get_training_area() or {}
    if (
        currentArea.get('x') == newArea['x']
        and currentArea.get('y') == newArea['y']
        and currentArea.get('z') == newArea['z']
        and currentArea.get('region') == newArea['r']
    ):
        return

    log('%s: Changing training area to [%s] Spot Level %d' % (Plugin, newArea['name'], newArea['level']))
    start_area_change(newArea)

def start_area_change(newArea):
    global area_change_pending
    global pending_area
    global area_change_stage
    global area_change_death_remaining

    area_change_pending = True
    pending_area = newArea
    area_change_stage = 1
    area_change_death_remaining = None

    stop_bot()
    set_training_script('')
    schedule_area_change(xcontrol_stop_delay_ms / 1000.0)

def continue_area_change():
    global area_change_pending
    global pending_area
    global area_change_timer
    global area_change_stage
    global area_change_death_remaining

    area_change_timer = None
    if not area_change_pending or not pending_area:
        return
    if not enabled:
        area_change_pending = False
        pending_area = None
        area_change_stage = 0
        reset_area_change_death_timer()
        return

    if area_change_stage == 4:
        finish_forced_return()
        return

    if area_change_stage in (1, 2) and not is_character_alive():
        if area_change_death_remaining is None:
            area_change_death_remaining = DEATH_WAIT_TIMEOUT
            log('%s: Character died during area change. Waiting up to %d seconds for resurrection.' % (Plugin, DEATH_WAIT_TIMEOUT))
        area_change_death_remaining -= 1
        if area_change_death_remaining <= 0:
            return_to_town_after_death_timeout()
            return
        schedule_area_change(1.0)
        return

    area_change_death_remaining = None
    area = pending_area

    if area_change_stage == 1:
        try:
            set_training_position(area['r'], area['x'], area['y'], area['z'])
            set_training_radius(area['radius'])
        except Exception as ex:
            log('%s: Error applying training area: %s' % (Plugin, ex))
            schedule_area_change(1.0)
            return
        area_change_stage = 2
        schedule_area_change(xcontrol_start_delay_ms / 1000.0)
        return

    if area_change_stage == 2:
        try:
            start_bot()
        except Exception as ex:
            log('%s: Error starting local bot after area change: %s' % (Plugin, ex))
            schedule_area_change(1.0)
            return
        log('%s: Local bot started at training area [%s].' % (Plugin, str(area.get('name', 'Unknown'))))
        if xcontrol_enabled:
            start_chat_area_change(area)
        else:
            area_change_pending = False
            pending_area = None
            area_change_stage = 0
            reset_area_change_death_timer()
        return

    if area_change_stage in (3, 5):
        continue_chat_area_change()
        return

    area_change_pending = False
    pending_area = None
    area_change_stage = 0
    reset_area_change_death_timer()

def check_party():
    character = get_character_data()
    if not character or 'level' not in character:
        return
    level = character['level']
    if solo:
        check_level(level)
        return
    party = get_party()
    if not party or len(party) != members:
        return
    lowestLvl = level
    for key in party:
        try:
            member = party[key]
            if member['name'] == character['name']:
                continue
            memberLevel = member.get('level', 0)
            if 0 < memberLevel < lowestLvl:
                lowestLvl = memberLevel
        except:
            continue
    check_level(lowestLvl)

# ============================================================
# Save & Load Configuration File
# ============================================================
def save_config():
    try:
        if current_character:
            read_xcontrol_tab1()
            save_character_settings()

        directory = os.path.dirname(CONFIG_FILE)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write('[Settings]\n')
            f.write('use_monstername_as_name=%d\n' % (1 if use_monstername_as_name else 0))
            f.write('use_mob_level=%d\n' % (1 if use_mob_level else 0))
            f.write('\n')

            for character in list(character_settings):
                settings = character_settings[character]
                if not isinstance(settings, dict):
                    log('%s: Repairing invalid settings for [%s].' % (Plugin, character))
                    settings = get_default_character_settings()
                    character_settings[character] = settings
                f.write('[%s]\n' % character)
                f.write('enabled=%d\n' % (1 if settings['enabled'] else 0))
                f.write('hometown_enabled=%d\n' % (1 if settings.get('hometown_enabled', True) else 0))
                f.write('buy_items_enabled=%d\n' % (1 if settings.get('buy_items_enabled', False) else 0))
                f.write('buy_keep_town_gold_enabled=%d\n' % (1 if settings.get('buy_keep_town_gold_enabled', False) else 0))
                try:
                    threshold = max(0, int(settings.get('buy_gold_threshold', 0)))
                except Exception:
                    threshold = 0
                f.write('buy_gold_threshold=%d\n' % threshold)
                bought_names = []
                for item_name in settings.get('bought_items', []):
                    item_name = str(item_name or '').strip()
                    if item_name and not item_name.isdigit() and item_name not in bought_names:
                        bought_names.append(item_name)
                f.write('bought_items=%s\n' % ','.join(bought_names))
                f.write('solo=%d\n' % (1 if settings['solo'] else 0))
                f.write('members=%d\n' % settings['members'])
                f.write('levelOffset=%d\n' % settings['levelOffset'])
                f.write('xcontrol_enabled=%d\n' % (1 if settings.get('xcontrol_enabled', False) else 0))
                f.write('xcontrol_stop=%s\n' % str(settings.get('xcontrol_stop_command', 'STOP')).replace('\\n', ' '))
                f.write('xcontrol_stopDelayMs=%d\n' % clamp_delay(settings.get('xcontrol_stop_delay_ms', 500)))
                f.write('xcontrol_setpos=%s\n' % str(settings.get('xcontrol_setpos_command', 'SETPOS x% y% r% z%')).replace('\\n', ' '))
                f.write('xcontrol_setrange=%s\n' % str(settings.get('xcontrol_setrange_command', 'SETRADIUS %Range')).replace('\\n', ' '))
                f.write('xcontrol_startDelayMs=%d\n' % clamp_delay(settings.get('xcontrol_start_delay_ms', 500)))
                f.write('xcontrol_start=%s\n' % str(settings.get('xcontrol_start_command', 'START')).replace('\\n', ' '))

                rules = settings.get('hometown_rules')
                if not isinstance(rules, list) or len(rules) != len(HOMETOWN_DEFAULTS):
                    rules = _hometown_character_defaults()['hometown_rules']
                    settings['hometown_rules'] = rules
                for idx, rule in enumerate(rules):
                    if not isinstance(rule, dict):
                        rule = _hometown_character_defaults()['hometown_rules'][idx]
                        rules[idx] = rule
                    try:
                        enabled_value = 1 if bool(rule.get('enabled', False)) else 0
                        race_value = str(rule.get('race', HOMETOWN_DEFAULTS[idx]['race']))
                        if race_value not in ('Chinese', 'Europe', 'All'):
                            race_value = HOMETOWN_DEFAULTS[idx]['race']
                        level_value = max(0, min(255, int(rule.get('level', HOMETOWN_DEFAULTS[idx]['level']))))
                    except Exception:
                        base = HOMETOWN_DEFAULTS[idx]
                        enabled_value = 1 if bool(base.get('enabled', False)) else 0
                        race_value = base.get('race', 'All')
                        level_value = int(base.get('level', 0))
                    town_value = str(rule.get('town', HOMETOWN_DEFAULTS[idx]['town'])).replace('|', ' ')
                    f.write('%d|%d|%s|%d|%s\n' % (idx, enabled_value, race_value, level_value, town_value))
                f.write('\n')

            f.write('[Spots]\n')
            spots.sort(key=lambda s: (s['level'], s['race']))
            for spot in spots:
                safe_name = spot['name'].replace('|', '/')
                f.write('%s|%d|%s|%d|%d|%d|%d|%d\n' %
                    (spot['race'], spot['level'], safe_name, spot['r'], spot['x'], spot['y'], spot['z'], spot['radius']))
    except Exception as ex:
        log('%s: Error saving configuration: %s' % (Plugin, ex))

def load_config():
    global spots
    global character_settings
    global use_monstername_as_name
    global use_mob_level

    spots = []
    character_settings = {}
    use_monstername_as_name = False
    use_mob_level = False
    QtBind.setChecked(tab1, checkMonsterName, False)
    QtBind.setChecked(tab1, checkMobLevel, False)

    legacy_xcontrol = {
        'xcontrol_enabled': False,
        'xcontrol_stop_command': 'STOP',
        'xcontrol_stop_delay_ms': 500,
        'xcontrol_setpos_command': 'SETPOS x% y% r% z%',
        'xcontrol_setrange_command': 'SETRADIUS %Range',
        'xcontrol_start_delay_ms': 500,
        'xcontrol_start_command': 'START'
    }
    legacy_xcontrol_found = False
    character_xcontrol_explicit = set()
    loaded_hometown = {}
    legacy_character_sections = set()
    legacy_hometown_sections = set()
    separate_hometown_sections = set()

    if not os.path.exists(CONFIG_FILE):
        save_config()
        refresh_spot_list()
        return
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        section = ''
        character = None
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('[') and line.endswith(']'):
                section = line[1:-1]
                if section.startswith('Character:'):
                    legacy_name = section[len('Character:'):].strip()
                    legacy_character_sections.add(legacy_name)
                    character = get_character_key(legacy_name) if legacy_name == get_character_name() else legacy_name
                    if character not in character_settings:
                        character_settings[character] = get_default_character_settings()
                elif section not in ('Settings', 'Spots', 'XControl') and not section.startswith('Hometown:'):
                    if '_' not in section:
                        legacy_character_sections.add(section)
                    character = section
                    if character not in character_settings:
                        character_settings[character] = get_default_character_settings()
                else:
                    character = None
                continue

            if section == 'Settings':
                if '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip() == 'use_monstername_as_name':
                        use_monstername_as_name = value.strip() == '1'
                        QtBind.setChecked(tab1, checkMonsterName, use_monstername_as_name)
                    elif key.strip() == 'use_mob_level':
                        use_mob_level = value.strip() == '1'
                        QtBind.setChecked(tab1, checkMobLevel, use_mob_level)
                continue

            if character is not None and (section.startswith('Character:') or (section not in ('Settings', 'Spots', 'XControl') and not section.startswith('Hometown:'))):
                if '=' not in line:
                    if '|' in line:
                        rules = loaded_hometown.setdefault(character, _hometown_copy_defaults())
                        try:
                            parts = line.split('|')
                            if len(parts) >= 4:
                                idx = int(parts[0])
                                if 0 <= idx < len(HOMETOWN_DEFAULTS):
                                    rules[idx]['enabled'] = parts[1] == '1'
                                    rules[idx]['race'] = parts[2] if parts[2] in _hometown_race_options() else HOMETOWN_DEFAULTS[idx]['race']
                                    rules[idx]['level'] = max(0, min(255, int(parts[3])))
                                    if len(parts) >= 5 and rules[idx].get('custom_town') and parts[4] in _hometown_town_options():
                                        rules[idx]['town'] = parts[4]
                                        town_base = next((r for r in HOMETOWN_DEFAULTS if not r.get('custom_town') and r['town'] == parts[4]), HOMETOWN_DEFAULTS[0])
                                        rules[idx]['teleport'] = tuple(town_base['teleport'])
                                        rules[idx]['spawn'] = tuple(town_base['spawn'])
                        except Exception:
                            pass
                    continue
                key, value = line.split('=', 1)
                value = value.strip()
                if key == 'enabled':
                    character_settings[character]['enabled'] = (value == '1')
                elif key == 'hometown_enabled':
                    character_settings[character]['hometown_enabled'] = (value == '1')
                elif key == 'buy_items_enabled':
                    character_settings[character]['buy_items_enabled'] = (value == '1')
                elif key == 'buy_keep_town_gold_enabled':
                    character_settings[character]['buy_keep_town_gold_enabled'] = (value == '1')
                elif key == 'buy_gold_threshold':
                    try:
                        character_settings[character]['buy_gold_threshold'] = max(0, int(value))
                    except Exception:
                        character_settings[character]['buy_gold_threshold'] = 0
                elif key == 'bought_items':
                    names = []
                    for raw_name in value.split(','):
                        item_name = raw_name.strip()
                        if item_name and item_name not in names:
                            names.append(item_name)
                    character_settings[character]['bought_items'] = names
                elif key == 'solo':
                    character_settings[character]['solo'] = (value == '1')
                elif key == 'members':
                    try:
                        character_settings[character]['members'] = max(1, min(8, int(value)))
                    except:
                        character_settings[character]['members'] = 8
                elif key == 'levelOffset':
                    try:
                        character_settings[character]['levelOffset'] = max(-255, min(255, int(value)))
                    except:
                        character_settings[character]['levelOffset'] = 0
                elif key == 'xcontrol_enabled':
                    character_settings[character]['xcontrol_enabled'] = (value == '1')
                    character_xcontrol_explicit.add(character)
                elif key == 'xcontrol_stop':
                    character_settings[character]['xcontrol_stop_command'] = value
                    character_xcontrol_explicit.add(character)
                elif key == 'xcontrol_stopDelayMs':
                    character_settings[character]['xcontrol_stop_delay_ms'] = clamp_delay(value)
                    character_xcontrol_explicit.add(character)
                elif key == 'xcontrol_setpos':
                    character_settings[character]['xcontrol_setpos_command'] = value
                    character_xcontrol_explicit.add(character)
                elif key == 'xcontrol_setrange':
                    character_settings[character]['xcontrol_setrange_command'] = value
                    character_xcontrol_explicit.add(character)
                elif key == 'xcontrol_startDelayMs':
                    character_settings[character]['xcontrol_start_delay_ms'] = clamp_delay(value)
                    character_xcontrol_explicit.add(character)
                elif key == 'xcontrol_start':
                    character_settings[character]['xcontrol_start_command'] = value
                    character_xcontrol_explicit.add(character)
                continue

            if section == 'XControl':
                if '=' not in line:
                    continue
                key, value = line.split('=', 1)
                value = value.strip()
                legacy_xcontrol_found = True
                if key == 'enabled':
                    legacy_xcontrol['xcontrol_enabled'] = (value == '1')
                elif key == 'stop':
                    legacy_xcontrol['xcontrol_stop_command'] = value
                elif key == 'stopDelayMs':
                    legacy_xcontrol['xcontrol_stop_delay_ms'] = clamp_delay(value)
                elif key == 'setpos':
                    legacy_xcontrol['xcontrol_setpos_command'] = value
                elif key == 'setrange':
                    legacy_xcontrol['xcontrol_setrange_command'] = value
                elif key == 'startDelayMs':
                    legacy_xcontrol['xcontrol_start_delay_ms'] = clamp_delay(value)
                elif key == 'start':
                    legacy_xcontrol['xcontrol_start_command'] = value
                continue

            if section.startswith('Hometown:'):
                hometown_character = section.split(':', 1)[1]
                separate_hometown_sections.add(hometown_character)
                if '_' not in hometown_character:
                    legacy_hometown_sections.add(hometown_character)
                rules = loaded_hometown.setdefault(hometown_character, _hometown_copy_defaults())
                try:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        idx = int(parts[0])
                        if 0 <= idx < len(HOMETOWN_DEFAULTS):
                            rules[idx]['enabled'] = parts[1] == '1'
                            rules[idx]['race'] = parts[2] if parts[2] in _hometown_race_options() else HOMETOWN_DEFAULTS[idx]['race']
                            rules[idx]['level'] = max(0, min(255, int(parts[3])))
                            if len(parts) >= 5 and rules[idx].get('custom_town') and parts[4] in _hometown_town_options():
                                rules[idx]['town'] = parts[4]
                                town_base = next((r for r in HOMETOWN_DEFAULTS if not r.get('custom_town') and r['town'] == parts[4]), HOMETOWN_DEFAULTS[0])
                                rules[idx]['teleport'] = tuple(town_base['teleport'])
                                rules[idx]['spawn'] = tuple(town_base['spawn'])
                except Exception:
                    pass
                continue

            if section == 'Spots':
                parts = line.split('|')
                if len(parts) != 8:
                    continue
                try:
                    race = parts[0]
                    if race not in ['Europe', 'Chinese', 'All']:
                        continue
                    level = max(1, min(255, int(parts[1])))
                    name = parts[2] if parts[2] else 'Unnamed'
                    spots.append({
                        'race': race,
                        'level': level,
                        'name': name,
                        'r': int(parts[3]),
                        'x': int(parts[4]),
                        'y': int(parts[5]),
                        'z': int(parts[6]),
                        'radius': max(0, min(255, int(parts[7])))
                    })
                except:
                    log('%s: Invalid spot line: %s' % (Plugin, line))

        migrated_character_sections = False

        def _resolve_legacy_character_key(name):
            name = str(name or '').strip()
            if not name:
                return name
            live_name = get_character_name()
            if live_name and name == live_name:
                return get_character_key(live_name) or name
            suffix = '_' + name
            matches = [key for key in character_settings if key.endswith(suffix) and key != name]
            if len(matches) == 1:
                return matches[0]
            return name

        for legacy_name in list(legacy_character_sections):
            target_key = _resolve_legacy_character_key(legacy_name)
            if target_key == legacy_name:
                continue
            legacy_settings = character_settings.pop(legacy_name, {})
            target_existed = target_key in character_settings
            if not target_existed and isinstance(legacy_settings, dict):
                character_settings[target_key] = legacy_settings
            else:
                target_settings = character_settings.setdefault(target_key, get_default_character_settings())
                if isinstance(legacy_settings, dict):
                    for key, value in legacy_settings.items():
                        if key not in target_settings:
                            target_settings[key] = value
            if target_key != legacy_name:
                migrated_character_sections = True

        normalized_hometown = {}
        for hometown_name, rules in loaded_hometown.items():
            target_key = _resolve_legacy_character_key(hometown_name)
            if target_key not in normalized_hometown or '_' in hometown_name:
                normalized_hometown[target_key] = rules
        loaded_hometown = normalized_hometown
        if any(_resolve_legacy_character_key(name) != name for name in legacy_hometown_sections):
            migrated_character_sections = True
        if any('_' in name or _resolve_legacy_character_key(name) != name for name in separate_hometown_sections):
            migrated_character_sections = True

        for hometown_character, rules in loaded_hometown.items():
            if hometown_character not in character_settings:
                character_settings[hometown_character] = get_default_character_settings()
            character_settings[hometown_character]['hometown_rules'] = rules

        migrated_legacy_xcontrol = False
        if legacy_xcontrol_found:
            for character in character_settings:
                settings = character_settings[character]
                if character not in character_xcontrol_explicit:
                    settings.update(legacy_xcontrol)
                    migrated_legacy_xcontrol = True

        spots.sort(key=lambda s: (s['level'], s['race']))

        if migrated_legacy_xcontrol or migrated_character_sections:
            save_config()

        refresh_spot_list()
        log('%s: Loaded %d spots and %d character settings.' % (Plugin, len(spots), len(character_settings)))
    except Exception as ex:
        log('%s: Error loading configuration: %s' % (Plugin, ex))

# ============================================================
# Auto Hometown & Auto Buy GUI (Tab 2)
# ============================================================
tab2 = QtBind.init(__name__, Plugin + '(+)')

buy_items_pending = False

buy_items_check = QtBind.createCheckBox(tab2, 'buy_items_clicked', '', 0, 0)
QtBind.createLabel(tab2, '<b>Enable Buy Newly Available NPC Items</b>', 25, 5)

buy_keep_town_gold_check = QtBind.createCheckBox(tab2, 'buy_keep_town_gold_clicked', '', 0, 20)
QtBind.createLabel(tab2, 'Keep enough Gold for Town Loop Items', 25, 25)

QtBind.createLabel(tab2, '*Must have at least 2 "Return Scrolls" set in (Town > Buy)', 5, 73)
QtBind.createLabel(tab2, '*Must enable "Equip better items" in (Training Area > Options)', 5, 90)

QtBind.createLabel(tab2, 'Dont buy items if that will result in Gold beeing lower then:', 5, 45)
buy_gold_threshold_edit = QtBind.createLineEdit(tab2, '0', 290, 43, 90, 20)

# ============================================================
# SP Gap Calculator GUI
# ============================================================
calc_y = 145

QtBind.createLabel(tab2, '<b>SP Gap Calculator</b>', 5, calc_y)

calc_live_btn = QtBind.createButton(tab2, 'calc_get_live_stats_clicked', 'Get Live Stats', 208, calc_y - 2)

QtBind.createLabel(tab2, 'Current Skill Points:', 5, calc_y + 25)
calc_cur_sp_edit = QtBind.createLineEdit(tab2, '0', 134, calc_y + 22, 70, 20)

QtBind.createLabel(tab2, 'Current Percent:', 5, calc_y + 45)
calc_cur_perc_edit = QtBind.createLineEdit(tab2, '0.00', 134, calc_y + 42, 70, 20)

QtBind.createLabel(tab2, 'Current Level:', 5, calc_y + 65)
calc_start_lvl_edit = QtBind.createLineEdit(tab2, '1', 134, calc_y + 62, 70, 20)

QtBind.createLabel(tab2, 'Current Mastery Level:', 5, calc_y + 85)
calc_mastery_lvl_edit = QtBind.createLineEdit(tab2, '1', 134, calc_y + 82, 70, 20)

QtBind.createLabel(tab2, 'Wanted Full Farmed Level:', 5, calc_y + 105)
calc_max_lvl_edit = QtBind.createLineEdit(tab2, '110', 134, calc_y + 102, 70, 20)

calc_btn = QtBind.createButton(tab2, 'calc_sp_clicked', 'Calculate SP and Gap', 208, calc_y + 102)

calc_result_label1 = QtBind.createLabel(tab2, 'Skills and Mastery will be taken from the Mastery Tab                                        ', 5, calc_y + 135)
calc_result_label2 = QtBind.createLabel(tab2, 'Results will be displayed here.                                                              ', 5, calc_y + 150)

buy_items_state = None

BUY_REGION_TOWN = {
    25000: 'Jangan', 26265: 'Donwhang', 23687: 'Hotan', 27244: 'Samarkand',
    26959: 'Constantinople', 23088: 'Alexandria (South)', 23089: 'Alexandria (South)',
    23602: 'Alexandria (North)', 23603: 'Alexandria (North)'
}

def buy_keep_town_gold_clicked(checked):
    global buy_keep_town_gold_enabled
    if globals().get('loading_character_settings', False):
        return
    buy_keep_town_gold_enabled = bool(checked)
    if current_character:
        save_config()
    log('%s: Keep Gold for Town Loop Items %s.' % (Plugin, 'enabled' if buy_keep_town_gold_enabled else 'disabled'))

def buy_items_clicked(checked):
    global buy_items_enabled
    if globals().get('loading_character_settings', False):
        return
    buy_items_enabled = bool(checked)
    if current_character:
        save_config()
    log('%s: Buy Newly Available NPC Items %s.' % (Plugin, 'enabled' if buy_items_enabled else 'disabled'))

# ============================================================
# SP Gap Calculator Logic & Live Stats
# ============================================================
def calc_get_live_stats_clicked():
    try:
        char_data = get_character_data()
        if not char_data:
            QtBind.setText(tab2, calc_result_label1, 'Error: Character not logged in or data unavailable.               ')
            QtBind.setText(tab2, calc_result_label2, '')
            return

        lvl = int(char_data.get('level', 1) or 1)
        QtBind.setText(tab2, calc_start_lvl_edit, str(lvl))

        sp = int(char_data.get('sp', 0) or 0)
        QtBind.setText(tab2, calc_cur_sp_edit, str(sp))

        # Berechne die exakten Prozente direkt aus den phBot-Daten (ohne DB-Abfrage!)
        perc = 0.0
        cur_exp = float(char_data.get('current_exp', char_data.get('exp', 0)) or 0)
        max_exp = float(char_data.get('max_exp', 0) or 0)
        
        if max_exp > 0:
            perc = (100.0 / max_exp) * cur_exp
            perc = max(0.0, min(perc, 99.99))
        else:
            # Fallback
            perc = float(char_data.get('percent', char_data.get('exp_percent', 0.0)) or 0.0)

        QtBind.setText(tab2, calc_cur_perc_edit, f"{perc:.2f}")

        masteries = get_mastery() or {}
        max_mastery = 1
        if masteries:
            levels = [int(m.get('level', 0)) for m in masteries.values() if m]
            if levels:
                max_mastery = max(levels)
        QtBind.setText(tab2, calc_mastery_lvl_edit, str(max_mastery))

        QtBind.setText(tab2, calc_result_label1, 'Live stats successfully loaded from client!                          ')
        QtBind.setText(tab2, calc_result_label2, f'Loaded: Lvl {lvl}, SP {sp}, Perc {perc:.2f}%, Mastery {max_mastery}')
        log('%s: SP Calculator loaded live stats for [%s].' % (Plugin, get_character_name() or 'Unknown'))
    except Exception as ex:
        QtBind.setText(tab2, calc_result_label1, 'Error reading live stats. Check logs.                                 ')
        QtBind.setText(tab2, calc_result_label2, '')
        log('%s: Error in calc_get_live_stats_clicked: %s' % (Plugin, ex))

def calc_sp_clicked():
    import json

    try:
        cur_sp = int(QtBind.text(tab2, calc_cur_sp_edit))
        cur_perc_str = QtBind.text(tab2, calc_cur_perc_edit).replace(',', '.')
        cur_perc = float(cur_perc_str)
        cur_perc = max(0.0, min(cur_perc, 99.99))

        start_lvl = int(QtBind.text(tab2, calc_start_lvl_edit))
        start_mastery_lvl = int(QtBind.text(tab2, calc_mastery_lvl_edit))
        max_lvl = int(QtBind.text(tab2, calc_max_lvl_edit))
    except:
        QtBind.setText(tab2, calc_result_label1, 'Error: Please enter valid numbers.                                ')
        QtBind.setText(tab2, calc_result_label2, '')
        return

    char_name = get_character_name()
    server_name = get_server_name()
    if not char_name:
        QtBind.setText(tab2, calc_result_label1, 'Error: Character is not logged in.                              ')
        QtBind.setText(tab2, calc_result_label2, '')
        return

    profile_path = os.path.join(get_config_dir(), f"{server_name}_{char_name}.json")
    if not os.path.exists(profile_path):
        QtBind.setText(tab2, calc_result_label1, f'Error: Profile {server_name}_{char_name}.json missing.          ')
        QtBind.setText(tab2, calc_result_label2, '')
        return

    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
    except:
        QtBind.setText(tab2, calc_result_label1, 'Error: Failed to read JSON profile.                             ')
        QtBind.setText(tab2, calc_result_label2, '')
        return

    masteries = profile_data.get('Auto Mastery', {}).get('Mastery', [])
    skills = [s.strip() for s in profile_data.get('Auto Mastery', {}).get('Skill', [])]
    mastery_count = len(masteries)

    client = get_client()
    db_path = _buy_items_db_path(client.get('path', ''))
    if not db_path:
        QtBind.setText(tab2, calc_result_label1, 'Error: data.db3 not found.                                      ')
        QtBind.setText(tab2, calc_result_label2, '')
        return

    sp_needed = 0
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if skills:
            placeholders = ','.join('?' for _ in skills)
            query = f"SELECT SUM(sp) as total_sp FROM skills WHERE sp BETWEEN 0 AND 999999 AND mastery > 0 AND level BETWEEN ? AND ? AND name IN ({placeholders})"
            params = [start_mastery_lvl, max_lvl] + skills
            row = conn.execute(query, params).fetchone()
            if row and row['total_sp']:
                sp_needed += row['total_sp']

        query = "SELECT SUM(sp) as total_sp FROM leveldata WHERE level BETWEEN ? AND ?"
        row = conn.execute(query, (start_mastery_lvl, max_lvl)).fetchone()
        if row and row['total_sp']:
            sp_needed += (row['total_sp'] * mastery_count)
    finally:
        conn.close()

    sp_needed -= cur_sp
    if sp_needed < 0:
        sp_needed = 0

    SP_GAP_TABLE = {
        1: [1,2,0,0,0,0,0,0,0,0], 2: [3,3,4,0,0,0,0,0,0,0], 3: [4,5,6,7,0,0,0,0,0,0],
        4: [5,6,8,9,12,0,0,0,0,0], 5: [6,8,9,12,15,19,0,0,0,0], 6: [10,12,15,19,24,30,40,0,0,0],
        7: [14,17,21,26,32,41,55,78,0,0], 8: [17,21,26,32,41,52,70,99,157,0],
        9: [21,26,32,39,49,63,84,119,190,400], 10: [25,30,37,46,58,75,99,141,224,472],
        11: [34,41,51,63,79,101,135,191,304,642], 12: [43,52,64,80,100,128,171,243,385,813],
        13: [52,63,78,96,121,156,208,294,467,986], 14: [61,74,91,113,142,183,244,345,549,1158],
        15: [70,85,105,130,163,210,279,396,629,1328], 16: [86,105,129,160,201,259,345,489,776,1638],
        17: [102,125,153,190,239,307,409,579,920,1943], 18: [118,144,177,219,275,354,472,668,1061,2240],
        19: [133,163,200,247,310,399,532,754,1198,2528], 20: [148,181,222,274,345,443,591,837,1330,2807],
        21: [173,212,260,322,404,520,693,982,1559,3292], 22: [199,243,298,369,464,597,796,1127,1790,3779],
        23: [225,275,337,417,524,674,899,1273,2022,4269], 24: [251,306,376,466,585,752,1003,1421,2256,4763],
        25: [277,339,415,514,646,831,1108,1570,2493,5263], 26: [304,371,455,564,708,911,1215,1721,2733,5769],
        27: [331,404,496,614,772,992,1323,1874,2976,6283], 28: [358,438,537,665,836,1075,1433,2030,3224,6807],
        29: [386,472,579,717,901,1159,1545,2189,3477,7340], 30: [415,507,622,771,968,1245,1660,2351,3735,7884],
        31: [453,553,679,841,1056,1358,1810,2565,4073,8599], 32: [490,599,736,911,1144,1471,1961,2779,4413,9317],
        33: [528,646,793,981,1233,1585,2113,2994,4755,10039], 34: [567,693,850,1052,1322,1700,2266,3211,5099,10766],
        35: [605,740,908,1124,1412,1816,2421,3430,5447,11499], 36: [644,787,966,1197,1503,1933,2577,3651,5799,12242],
        37: [684,836,1026,1270,1596,2052,2736,3875,6155,12994], 38: [724,885,1086,1345,1690,2172,2896,4103,6517,13757],
        39: [765,935,1147,1421,1785,2295,3060,4335,6884,14534], 40: [807,986,1210,1498,1882,2420,3226,4571,7259,15325],
        41: [856,1046,1284,1590,1997,2568,3424,4851,7704,16264], 42: [905,1107,1358,1682,2113,2716,3622,5131,8149,17204],
        43: [955,1167,1433,1774,2229,2865,3821,5412,8596,18148], 44: [1005,1228,1508,1867,2345,3015,4020,5695,9045,19096],
        45: [1055,1290,1583,1960,2462,3166,4221,5980,9498,20052], 46: [1106,1352,1659,2054,2581,3318,4424,6268,9955,21016],
        47: [1158,1415,1736,2150,2701,3473,4630,6559,10418,21993], 48: [1210,1478,1814,2246,2822,3629,4838,6854,10886,22982],
        49: [1263,1543,1894,2345,2946,3788,5050,7154,11363,23988], 50: [1316,1609,1975,2445,3072,3949,5266,7460,11848,25012],
        51: [1384,1692,2077,2571,3230,4153,5538,7845,12459,26303], 52: [1453,1776,2179,2698,3390,4359,5812,8233,13077,27606],
        53: [1522,1861,2283,2827,3552,4567,6089,8626,13700,28923], 54: [1593,1946,2389,2958,3716,4778,6370,9024,14333,30258],
        55: [1664,2034,2496,3090,3882,4991,6655,9428,14974,31612], 56: [1736,2122,2605,3225,4051,5209,6945,9839,15627,32990],
        57: [1810,2213,2715,3362,4224,5431,7241,10258,16292,34395], 58: [1886,2305,2829,3502,4400,5657,7543,10686,16972,35830],
        59: [1963,2399,2945,3646,4580,5889,7852,11124,17667,37298], 60: [2042,2496,3063,3793,4765,6127,8169,11573,18380,38802],
        61: [2162,2643,3244,4016,5046,6487,8650,12254,19462,41086], 62: [2284,2792,3426,4242,5330,6853,9137,12944,20558,43399],
        63: [2408,2943,3612,4472,5618,7223,9631,13644,21670,45747], 64: [3040,3716,4560,5646,7094,9120,12160,17227,27361,57762],
        65: [3832,4684,5749,7117,8942,11497,15330,21717,34492,72817], 66: [4021,4914,6031,7467,9381,12062,16083,22784,36186,76392],
        67: [4213,5149,6320,7824,9830,12639,16852,23874,37917,80048], 68: [4410,5390,6615,8190,10290,13230,17640,24991,39691,83792],
        69: [4612,5637,6918,8566,10762,13837,18449,26136,41510,87632], 70: [4820,5891,7230,8951,11246,14459,19279,27312,43378,91577],
        71: [5037,6156,7555,9354,11752,15110,20147,28541,45330,95698], 72: [5264,6433,7895,9775,12281,15790,21053,29825,47370,100004],
        73: [5500,6723,8251,10215,12834,16500,22001,31168,49502,104505], 74: [5748,7025,8622,10674,13411,17243,22991,32570,51729,109207],
        75: [6007,7341,9010,11155,14015,18019,24025,34036,54057,114122], 76: [6277,7672,9415,11657,14645,18829,25106,35567,56489,119257],
        77: [6559,8017,9839,12181,15304,19677,26236,37168,59031,124624], 78: [6855,8378,10282,12729,15993,20562,27417,38840,61688,130232],
        79: [7163,8755,10744,13302,16713,21487,28650,40588,64464,136092], 80: [7485,9149,11228,13901,17465,22454,29940,42415,67365,142216],
        81: [7880,9631,11820,14634,18386,23638,31518,44651,70917,149715], 82: [8233,10062,12350,15289,19209,24697,32930,46651,74094,156422],
        83: [8590,10499,12885,15952,20042,25768,34358,48674,77306,163205], 84: [8950,10939,13425,16621,20882,26848,35798,50714,80546,170044],
        85: [9320,11391,13980,17308,21745,27958,37278,52811,83876,177074], 86: [9700,11855,14550,18013,22632,29098,38798,54964,87296,184294],
        87: [10090,12332,15135,18738,23542,30268,40358,57174,90806,191704], 88: [10490,10490,15735,19480,24475,31468,41958,59440,94406,199303],
        89: [10890,13310,16335,20223,25408,32668,43558,61707,98005,206903], 90: [11290,13799,16935,20966,26342,33868,45158,63974,101605,214503],
        91: [12901,15768,19352,23960,30103,38704,51605,73107,116111,245124], 92: [16059,19627,24008,29823,37470,48176,64235,90999,144528,305115],
        93: [14179,17330,21268,26332,33084,42536,56715,80346,127609,269396], 94: [22011,26902,33016,40877,51359,66032,88043,124728,198097,418205],
        95: [21294,26025,31940,39545,49685,63881,85174,120663,191642,404577], 96: [18991,23212,28487,35269,44313,56974,75965,107617,170921,360834],
        97: [24668,30150,37002,45812,57559,74004,98672,139785,222012,468691], 98: [27379,33463,41068,50846,63884,82137,109515,155147,246410,520198],
        99: [36473,44578,54710,67736,85104,109419,145892,206681,328258,692988], 100: [37643,46008,56464,69908,87833,112929,150571,213309,338786,715214],
        101: [43886,53639,65829,81503,102401,131659,178545,248689,394977,833840], 102: [50455,61667,75682,93702,117728,151364,201819,285910,454092,958639],
        103: [57456,90224,86184,106703,134063,172367,229823,325582,517101,1091658], 104: [64884,79303,97326,120499,151396,194653,259537,367677,583958,1232799],
        105: [67967,83071,101951,126225,158590,203902,271869,385147,611705,1291377], 106: [80468,98350,120703,149441,187760,241405,321874,455988,724216,1528901],
        107: [92392,112924,138588,171585,215582,277177,369569,523566,831530,1755452], 108: [105084,128437,157627,195157,245197,315253,420338,595478,945760,1996604],
        109: [118555,144901,177833,220174,276629,355666,474222,671814,1066999,2252553], 110: [130275,159226,195413,241940,303976,390826,521102,738227,1172479,2475233],
        111: [137238,167736,205857,254871,320222,411715,548953,777683,1235144,2607525], 112: [144215,176262,216322,267827,336501,432644,576859,817217,1297933,2740080],
        113: [151177,184771,226765,280756,352745,453530,604706,856667,1360589,2872354], 114: [158149,193293,237224,293706,369015,474447,632597,896178,1423342,3004834],
        115: [165114,201806,247672,306641,385267,495343,660458,935648,1486030,3137174], 116: [173588,212163,260382,322377,405038,520764,694351,983664,1562291,3298169],
        117: [182051,222507,273076,338094,424785,546152,728203,1031621,1638457,3458965], 118: [190519,232857,285779,353822,444545,571558,762078,1079610,1714675,3619869],
        119: [198987,243206,298480,369547,464302,596960,795947,1127591,1790880,3780748], 120: [207458,253560,311187,385279,484068,622373,829831,1175594,1867120,3941698],
        121: [218426,266965,327639,405648,509660,655277,873703,1237746,1965832,4150089], 122: [229396,280373,344094,426021,535257,688188,917584,1299910,2064564,4358523],
        123: [240361,293775,360542,446386,560843,721084,961446,1362048,2163253,4566868], 124: [251328,307179,376992,466753,586433,753985,1005313,1424194,2261955,4775238],
        125: [262290,320576,393434,487109,612009,786869,1049158,1486308,2360606,4983502], 126: [273265,333991,409898,507493,637619,819796,1093061,1548504,2459388,5192042],
        127: [284236,347399,426354,527866,663217,852707,1136943,1610670,2558122,5400480], 128: [295194,360793,442791,548218,688786,885583,1180777,1672767,2656748,5608690],
        129: [306162,374198,459243,568586,714377,918485,1224647,1734917,2755456,5817074], 130: [317133,387606,475699,588960,739976,951398,1268530,1797084,2854193,6025518],
        131: [333101,407123,499651,618615,777235,999302,1332402,1887570,2997905,6328911], 132: [349074,426647,523612,648281,814507,1047223,1396298,1978089,3141670,6632415],
        133: [365034,446153,547551,677920,851746,1095102,1460136,2068526,3285306,6935646], 134: [381003,465670,571504,707577,889007,1143009,1524011,2159016,3429026,7239054],
        135: [396976,485193,595464,737241,926278,1190928,1587905,2249531,3572785,7542547], 136: [437949,535271,656924,813335,1021882,1313848,1751798,2481713,3941544,8321038],
        137: [478917,585343,718376,889418,1117474,1436752,1915669,2713864,4310255,9099427], 138: [519873,635401,779810,965479,1213038,1559620,2079494,2945949,4678860,9877594],
        139: [560849,685482,841274,1041577,1308648,1682547,2243396,3178144,5047641,10656131], 140: [601822,735560,902733,1117670,1404252,1805467,2407289,3410326,5416400,11434622]
    }

    remaining_ratio = 1.0 - (cur_perc / 100.0)

    def get_sp_for_gap(target_gap):
        total = 0.0
        for lvl in range(start_lvl, max_lvl):
            eff_gap = max(0, min(lvl - start_mastery_lvl, 9))
            if eff_gap >= target_gap:
                eff_gap = target_gap
            if lvl in SP_GAP_TABLE:
                sp_for_this_lvl = SP_GAP_TABLE[lvl][eff_gap]
                if lvl == start_lvl:
                    sp_for_this_lvl *= remaining_ratio
                total += sp_for_this_lvl
        return total

    base_gap = -1
    for g in range(10):
        if get_sp_for_gap(g) >= sp_needed:
            base_gap = g
            break

    if base_gap == -1:
        sp_gainable = get_sp_for_gap(9)
        res1 = f"{sp_needed} SP Needed, {int(sp_gainable)} SP will be Gained till Lvl {max_lvl} with Gap 9."
        res2 = "Warning: Gap 9 is not enough to reach the required SP!"
    elif base_gap == 0:
        sp_gainable = get_sp_for_gap(0)
        res1 = f"{sp_needed} SP Needed, {int(sp_gainable)} SP will be Gained till Lvl {max_lvl} with Gap 0."
        res2 = "You can stay on Gap 0 the entire time."
    else:
        pre_gap = base_gap
        gap = base_gap - 1
        sp_gainable = get_sp_for_gap(gap)
        gap_change_lvl = start_lvl - 1

        while sp_needed > sp_gainable and gap_change_lvl < max_lvl:
            gap_change_lvl += 1
            eff_gap_lower = max(0, min(gap_change_lvl - start_mastery_lvl, 9))
            if eff_gap_lower >= gap:
                eff_gap_lower = gap
            eff_gap_higher = max(0, min(gap_change_lvl - start_mastery_lvl, 9))
            if eff_gap_higher >= pre_gap:
                eff_gap_higher = pre_gap

            if eff_gap_higher > eff_gap_lower and gap_change_lvl in SP_GAP_TABLE:
                diff = SP_GAP_TABLE[gap_change_lvl][eff_gap_higher] - SP_GAP_TABLE[gap_change_lvl][eff_gap_lower]
                if gap_change_lvl == start_lvl:
                    diff *= remaining_ratio
                sp_gainable += diff

        eff_gap_pre = max(0, min(gap_change_lvl - start_mastery_lvl, 9))
        if eff_gap_pre >= pre_gap:
            eff_gap_pre = pre_gap

        lvl_sp_full = SP_GAP_TABLE.get(gap_change_lvl, [0]*10)[eff_gap_pre]
        if gap_change_lvl == start_lvl:
            lvl_sp_remaining = lvl_sp_full * remaining_ratio
        else:
            lvl_sp_remaining = lvl_sp_full

        if lvl_sp_remaining > 0:
            percent_of_remaining = 100.0 - ((sp_gainable - sp_needed) / (lvl_sp_remaining / 100.0))
        else:
            percent_of_remaining = 0.0

        if gap_change_lvl == start_lvl:
            absolute_percent = cur_perc + (percent_of_remaining / 100.0 * (100.0 - cur_perc))
        else:
            absolute_percent = percent_of_remaining

        res1 = f"{sp_needed} SP Needed, {int(sp_gainable)} SP will be Gained till Lvl {max_lvl} with Gap {pre_gap}."
        res2 = f"On lvl {gap_change_lvl} with {absolute_percent:.2f} % change to Gap {gap}"

    QtBind.setText(tab2, calc_result_label1, res1.ljust(110))
    QtBind.setText(tab2, calc_result_label2, res2.ljust(110))

# ============================================================
# Auto Buy Items & Town Loop Gold Calculation
# ============================================================
cached_db_path = None

def _buy_items_db_path(client_path):
    global cached_db_path
    if cached_db_path and os.path.exists(cached_db_path):
        return cached_db_path
        
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.abspath(os.path.join(plugin_dir, '..', 'Data'))
    for candidate in glob.glob(os.path.join(data_dir, '*.db3')):
        try:
            conn = sqlite3.connect(candidate)
            row = conn.execute("SELECT v FROM data WHERE k='path' LIMIT 1").fetchone()
            conn.close()
            if row and str(row[0]).rstrip('\\/').lower() == str(client_path).rstrip('\\/').lower():
                cached_db_path = candidate
                return candidate
        except Exception:
            pass
    return None

def _buy_items_inventory_count(item_id=0, item_servername=''):
    """Count total quantity of an item across all inventory slots (including split stacks)."""
    total_count = 0
    target_id = int(item_id or 0)
    target_sn = str(item_servername or '').strip().upper()
    try:
        inventory = get_inventory() or {}
        for entry in inventory.get('items') or []:
            if not entry:
                continue
            matched = False
            if target_id > 0:
                for key in ('model', 'id', 'item_id'):
                    try:
                        if int(entry.get(key, -1)) == target_id:
                            matched = True
                            break
                    except Exception:
                        pass
            if not matched and target_sn:
                entry_sn = str(entry.get('servername') or '').strip().upper()
                if not entry_sn:
                    try:
                        model_id = int(entry.get('model', 0) or 0)
                        if model_id > 0:
                            item_data = get_item(model_id) or {}
                            entry_sn = str(item_data.get('servername') or '').strip().upper()
                    except Exception:
                        entry_sn = ''
                if entry_sn and entry_sn == target_sn:
                    matched = True
            if matched:
                total_count += max(1, int(entry.get('quantity', 1) or 1))
    except Exception:
        pass
    return total_count

def _get_town_loop_gold_needed(db_path_data):
    try:
        char_name = get_character_name()
        server_name = get_server_name()
        char_data = get_character_data()
        if not char_name or not server_name or not char_data:
            return 0

        char_level = int(char_data.get('level', 0))
        char_db_path = os.path.join(get_config_dir(), f"{server_name}_{char_name}.db3")
        if not os.path.exists(char_db_path):
            return 0

        conn_char = sqlite3.connect(char_db_path)
        conn_char.row_factory = sqlite3.Row
        town_items = conn_char.execute(
            "SELECT id, item_servername, quantity FROM town WHERE enabled = 1 AND quantity > 0 AND from_level IN (0, ?)",
            (char_level,)
        ).fetchall()
        conn_char.close()

        if not town_items:
            return 0

        total_gold_needed = 0
        conn_data = sqlite3.connect(db_path_data) if (db_path_data and os.path.exists(db_path_data)) else None
        try:
            for t_item in town_items:
                item_id = int(t_item['id'] or 0)
                item_sn = str(t_item['item_servername'] or '').strip()
                target_qty = int(t_item['quantity'] or 0)

                if item_id <= 0 and conn_data and item_sn:
                    row_id = conn_data.execute("SELECT id FROM items WHERE servername = ? LIMIT 1", (item_sn,)).fetchone()
                    if row_id and row_id[0]:
                        item_id = int(row_id[0])

                current_qty = _buy_items_inventory_count(item_id, item_sn)

                if target_qty > current_qty:
                    if item_sn in ('ITEM_ETC_SCROLL_RETURN_01', 'ITEM_ETC_SCROLL_RETURN_02', 'ITEM_ETC_SCROLL_RETURN_03'):
                        target_qty += 1
                    needed_qty = target_qty - current_qty

                    price = _buy_items_get_price(item_id)
                    if price <= 0 and conn_data and item_sn:
                        row_price = conn_data.execute("SELECT price FROM items WHERE servername = ? LIMIT 1", (item_sn,)).fetchone()
                        if row_price and row_price[0]:
                            price = int(row_price[0])

                    if price > 0:
                        total_gold_needed += (needed_qty * price)
        finally:
            if conn_data:
                conn_data.close()

        return total_gold_needed
    except Exception as ex:
        log('%s: Error calculating town loop gold: %s' % (Plugin, ex))
        return 0

def _buy_items_get_gold():
    try:
        data = get_character_data() or {}
        return int(data.get('gold', data.get('gold_amount', 0)) or 0)
    except Exception:
        return 0

def _buy_items_get_price(item_id):
    try:
        item_id = int(item_id or 0)
        if item_id <= 0:
            return 0
        item_data = get_item(item_id) or {}
        price = item_data.get('price', 0)
        return max(0, int(price or 0))
    except Exception:
        return 0

def _buy_items_inventory_has(item_id):
    return _buy_items_inventory_count(item_id=item_id) > 0

def _buy_items_category(servername):
    name = str(servername or '').upper()
    if '_SHIELD_' in name:
        return 'Shield'
    if any(token in name for token in ('_RING_', '_EARRING_', '_NECKLACE_')):
        return 'Accessory'
    if any(token in name for token in ('_HEAVY_', '_LIGHT_', '_CLOTHES_', '_ARMOR_', '_GARMENT_')):
        return 'Armor'
    if any(token in name for token in ('_SWORD_', '_BLADE_', '_SPEAR_', '_TWOHAND_', '_AXE_', '_BOW_', '_CROSSBOW_', '_DAGGER_', '_TSTAFF_', '_STAFF_', '_HARP_', '_TANK_', '_DARKSTAFF_')):
        return 'Weapon'
    return 'Other'

def _buy_items_item_gender(servername):
    name = str(servername or '').upper()
    if name.startswith(('ITEM_CH_M_', 'ITEM_EU_M_')):
        return 'Male'
    if name.startswith(('ITEM_CH_W_', 'ITEM_EU_W_')):
        return 'Female'
    return None

def _buy_items_character_gender(equipped_items):
    for _slot, item_data, entry in equipped_items:
        name = str(item_data.get('servername') or entry.get('servername') or '')
        gender = _buy_items_item_gender(name)
        if gender:
            return gender
    try:
        data = get_character_data() or {}
        for key in ('gender', 'sex', 'char_gender', 'character_gender'):
            value = str(data.get(key, '')).strip().lower()
            if value in ('m', 'male', '0', 'man'):
                return 'Male'
            if value in ('w', 'f', 'female', '1', 'woman'):
                return 'Female'
    except Exception:
        pass
    return None

def _buy_items_find_upgrades(db_path, race, char_level, mastery_level=None, bought_item_ids=None):
    bought_values = [str(v).strip() for v in (bought_item_ids or []) if str(v).strip()]
    bought_names = {v.upper() for v in bought_values if not v.isdigit()}
    legacy_bought_ids = {int(v) for v in bought_values if v.isdigit() and int(v) > 0}
    inv = get_inventory() or {}
    items = inv.get('items') or []
    equipped = []
    for slot in range(min(13, len(items))):
        if slot == 8 or not items[slot]:
            continue
        entry = items[slot]
        try:
            item_data = get_item(int(entry.get('model', 0))) or {}
            if int(item_data.get('tid1', -1)) == 1:
                equipped.append((slot, item_data, entry))
        except Exception:
            continue
    if not equipped:
        return []
    character_gender = _buy_items_character_gender(equipped)

    bag_item_counts = {}
    for entry in items[13:]:
        if not entry:
            continue
        try:
            bag_data = get_item(int(entry.get('model', 0))) or {}
            bag_servername = str(bag_data.get('servername') or entry.get('servername') or '').strip().upper()
            if bag_servername:
                bag_item_counts[bag_servername] = bag_item_counts.get(bag_servername, 0) + max(1, int(entry.get('quantity', 1) or 1))
        except Exception:
            continue

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    upgrades = {}
    try:
        if legacy_bought_ids:
            placeholders = ','.join('?' for _ in legacy_bought_ids)
            try:
                legacy_rows = conn.execute('SELECT id, servername FROM items WHERE id IN (%s)' % placeholders,
                                           tuple(legacy_bought_ids)).fetchall()
                bought_names.update(str(r['servername'] or '').strip().upper() for r in legacy_rows if r['servername'])
            except Exception:
                pass
        for slot, current, equipped_entry in equipped:
            tid = (int(current.get('tid1', -1)), int(current.get('tid2', -1)), int(current.get('tid3', -1)))
            current_level = int(current.get('level', 0))
            race_pattern = '%_CH_%' if race == 'Chinese' else '%_EU_%'
            current_name = str(current.get('servername') or equipped_entry.get('servername') or '')
            slot_category = _buy_items_category(current_name)
            if race == 'Europe' and slot_category == 'Armor':
                slot_allowed_level = int(mastery_level if mastery_level is not None else 0)
            else:
                slot_allowed_level = int(char_level)
            rows = conn.execute("""
                SELECT DISTINCT a.id, a.servername, a.name, a.level, a.tid1, a.tid2, a.tid3
                FROM items a
                INNER JOIN npcgoods b ON a.id = b.item
                INNER JOIN monsters c ON b.model = c.id
                WHERE a.tid1=? AND a.tid2=? AND a.tid3=?
                  AND a.level<=? AND a.servername LIKE ?
                  AND (c.servername LIKE 'NPC_%_SMITH%'
                    OR c.servername LIKE 'NPC_%_ARMOR%'
                    OR c.servername LIKE 'NPC_%_ACCESSORY%')
                ORDER BY a.level DESC
            """, (tid[0], tid[1], tid[2], slot_allowed_level, race_pattern)).fetchall()

            best_item = None
            for row in rows:
                servername = str(row['servername'] or '')
                if servername.strip().upper() in bought_names:
                    continue
                if race == 'Chinese' and '_CH_' not in servername:
                    continue
                if race == 'Europe' and '_EU_' not in servername:
                    continue
                if slot_category == 'Armor':
                    required_gender = _buy_items_item_gender(current_name) or character_gender
                    candidate_gender = _buy_items_item_gender(servername)
                    if required_gender and candidate_gender != required_gender:
                        continue
                    if candidate_gender and not required_gender:
                        continue
                best_item = dict(row)
                break

            replace = bool(best_item and int(best_item.get('level', 0)) > current_level)
            if replace:
                candidate_key = str(best_item.get('servername') or '').strip().upper()
                if candidate_key and bag_item_counts.get(candidate_key, 0) > 0:
                    bag_item_counts[candidate_key] -= 1
                    log('%s: Buy items: %s is already in inventory; skipping purchase for slot %d.' % (Plugin, best_item.get('name') or best_item.get('servername'), slot))
                    continue
                current_label = '%s Lv.%d' % (current.get('name') or current.get('servername') or 'Unknown', current_level)
                best_label = '%s Lv.%s' % (best_item.get('name') or best_item.get('servername') or 'Unknown', best_item.get('level'))
                log('%s: Debug: Current=(%s) Buyable=(%s)' % (Plugin, current_label, best_label))
                best_item['slot'] = slot
                best_item['current_level'] = current_level
                upgrades[slot] = best_item

        available = {}
        for candidate in upgrades.values():
            rows = conn.execute("""
                SELECT DISTINCT z.name AS zone_name, p.region
                FROM npcgoods g
                JOIN monsters c ON c.id = g.model
                JOIN npcpos p ON p.id = c.id
                JOIN zones z ON z.id = p.region
                WHERE g.item = ?
                  AND (c.servername LIKE 'NPC_%_SMITH%'
                    OR c.servername LIKE 'NPC_%_ARMOR%'
                    OR c.servername LIKE 'NPC_%_ACCESSORY%')
            """, (int(candidate['id']),)).fetchall()
            towns = set()
            for row in rows:
                region = int(row['region'])
                town = BUY_REGION_TOWN.get(region)
                if not town:
                    zn = str(row['zone_name'] or '').lower()
                    if 'donwhang' in zn: town = 'Donwhang'
                    elif zn == 'jangan': town = 'Jangan'
                    elif 'hotan' in zn: town = 'Hotan'
                    elif 'samarkand' in zn: town = 'Samarkand'
                    elif 'constantinople' in zn: town = 'Constantinople'
                    elif 'alexandria' in zn: town = 'Alexandria (North)' if region == 23603 else 'Alexandria (South)'
                if town:
                    towns.add(town)
            available[int(candidate['id'])] = towns
        for slot, candidate in list(upgrades.items()):
            candidate['towns'] = available.get(int(candidate['id']), set())
            if not candidate['towns']:
                del upgrades[slot]
    finally:
        conn.close()
    return list(upgrades.values())

def _buy_items_make_script(upgrades, startpos):
    town_order = ['Jangan', 'Donwhang', 'Hotan', 'Samarkand', 'Constantinople',
                  'Alexandria (South)', 'Alexandria (North)']
    town_scores = {
        town: sum(1 for item in upgrades if town in item.get('towns', set()))
        for town in town_order
    }
    selected_town = max(town_order, key=lambda town: town_scores[town]) if town_order else None
    if not selected_town or town_scores.get(selected_town, 0) == 0:
        return []

    town_routes = {
        'Constantinople_1': [
            'path,26959,-10636,2598,80',
            'walk,26959,-10627,2583,80',
            'DoStorage',
            'walk,26959,-10631,2589,80',
            'walk,26959,-10641,2603,81',
            'walk,26959,-10651,2617,80',
            'walk,26959,-10662,2632,80',
            'walk,26959,-10667,2639,83',
            'DoBlacksmith',
            'walk,26959,-10673,2646,83',
        ],
        'Constantinople_2': [
            'walk,26959,-10680,2643,83',
            'walk,26959,-10695,2635,79',
            'walk,26959,-10714,2624,79',
            'walk,26959,-10730,2616,79',
            'walk,26959,-10739,2610,82',
            'walk,26959,-10749,2605,83',
        ],
        'Constantinople_3': [
            'walk,26959,-10747,2602,83',
            'walk,26959,-10737,2591,79',
            'walk,26959,-10727,2578,80',
            'walk,26959,-10717,2565,83',
            'walk,26959,-10705,2550,80',
            'walk,26959,-10695,2538,80',
            'walk,26959,-10687,2528,80',
            'walk,26959,-10683,2523,80',
        ],
        'Donwhang_1': [
            'path,26265,3567,1999,-106',
            'walk,26265,3574,1992,-106',
            'DoStorage',
            'walk,26265,3568,2001,-106',
            'walk,26265,3564,2021,-106',
            'walk,26265,3567,2033,-106',
            'DoBlacksmith',
            'walk,26265,3571,2040,-106',
        ],
        'Donwhang_2': [
            'walk,26265,3569,2033,-106',
            'walk,26265,3570,2023,-106',
            'walk,26265,3573,2011,-106',
        ],
        'Donwhang_3': [
            'walk,26265,3559,2007,-106',
            'walk,26265,3544,2003,-106',
            'walk,26265,3527,1998,-105',
            'walk,26265,3514,1995,-104',
        ],
        'Hotan_1': [
            'path,23687,96,53,244',
            'walk,23687,102,56,244',
            'DoStorage',
            'walk,23687,96,58,244',
            'walk,23687,87,63,244',
            'walk,23687,73,69,244',
            'walk,23687,62,73,243',
            'DoBlacksmith',
            'walk,23687,52,75,243',
        ],
        'Hotan_2': [
            'walk,23687,54,67,243',
            'walk,23687,56,54,250',
            'walk,23687,60,41,244',
            'walk,23687,62,28,243',
            'walk,23687,59,20,243',
        ],
        'Hotan_3': [
            'walk,23687,65,15,243',
            'walk,23687,72,8,243',
            'walk,23431,84,-1,243',
        ],
        'Jangan_1': [
            'path,25000,6433,1073,-32',
            'walk,25000,6432,1064,-32',
            'DoStorage',
            'walk,25000,6427,1067,-32',
            'walk,25000,6415,1076,-32',
            'walk,25000,6405,1083,-33',
            'walk,25000,6393,1093,-29',
            'walk,25000,6386,1097,0',
            'walk,25000,6383,1098,0',
            'DoBlacksmith',
            'walk,25000,6373,1099,0',
        ],
        'Jangan_2': [
            'walk,25000,6373,1090,0',
            'walk,25000,6372,1078,0',
            'walk,25000,6371,1069,0',
        ],
        'Jangan_3': [
            'walk,25000,6377,1068,0',
            'walk,25000,6386,1068,0',
            'walk,25000,6401,1068,-32',
            'walk,25000,6420,1068,-32',
            'walk,25000,6444,1068,-32',
            'walk,25000,6472,1067,-32',
            'walk,25000,6482,1068,0',
            'walk,25000,6499,1068,0',
        ],
        'Samarkand_1': [
            'path,27244,-5143,2817,180',
            'walk,27244,-5132,2805,180',
            'DoStorage',
            'walk,27244,-5134,2811,180',
            'walk,27244,-5145,2832,180',
            'walk,27244,-5155,2853,180',
            'walk,27244,-5163,2870,192',
            'walk,27500,-5173,2892,192',
            'walk,27500,-5180,2908,192',
            'walk,27499,-5189,2924,180',
            'walk,27499,-5195,2942,180',
            'walk,27499,-5196,2948,182',
            'DoBlacksmith',
            'walk,27500,-5198,2957,180',
        ],
        'Samarkand_2': [
            'walk,27500,-5202,2948,184',
            'walk,27500,-5210,2935,186',
            'walk,27500,-5219,2924,186',
            'walk,27500,-5230,2916,184',
            'walk,27500,-5243,2914,180',
        ],
        'Samarkand_3': [
            'walk,27500,-5241,2908,180',
            'walk,27500,-5237,2898,180',
            'walk,27243,-5229,2877,180',
            'walk,27243,-5224,2864,180',
            'walk,27243,-5217,2849,180',
            'walk,27243,-5212,2836,180',
        ],
    }


    selected_upgrades = [item for item in upgrades if selected_town in item.get('towns', set())]
    categories = {'WeaponShield': [], 'Armor': [], 'Accessory': []}
    for item in selected_upgrades:
        try:
            item_id = int(item.get('id', 0))
        except Exception:
            continue
        servername = str(item.get('servername') or '').strip()
        if item_id <= 0 or not servername:
            continue
        category = _buy_items_category(servername)
        if category in ('Weapon', 'Shield'):
            categories['WeaponShield'].append({'id': item_id, 'servername': servername})
        elif category == 'Armor':
            categories['Armor'].append({'id': item_id, 'servername': servername})
        elif category == 'Accessory':
            categories['Accessory'].append({'id': item_id, 'servername': servername})

    segment_keys = ['%s_%d' % (selected_town, n) for n in (1, 2, 3) if '%s_%d' % (selected_town, n) in town_routes]
    if not segment_keys:
        return []
    segments = []
    for key in segment_keys:
        route_lines = list(town_routes[key])
        endpoint = None
        for line in reversed(route_lines):
            if line.startswith('walk,'):
                parts = line.split(',')
                try:
                    endpoint = (int(parts[1]), float(parts[2]), float(parts[3]))
                except Exception:
                    endpoint = None
                break
        segments.append({'name': key, 'lines': route_lines, 'endpoint': endpoint})
    return {
            'town': selected_town,
            'segments': segments,
            'categories': categories,
            'candidate_items': [{'id': int(i['id']), 'servername': str(i.get('servername') or '')}
                                for i in selected_upgrades if i.get('id') is not None]
        }

def _buy_items_after_teleport():
    global buy_items_state
    if not buy_items_enabled or buy_items_state:
        return
    if not _bot_is_running():
        return
    try:
        char = get_character_data() or {}
        pos = get_position() or {}
        current_region = int(pos.get('region', char.get('region', 0)) or 0)
        if current_region not in BUY_REGION_TOWN:
            return

        client = get_client() or {}
        race = get_character_race()
        if race not in ('Chinese', 'Europe'):
            log('%s: Buy items: could not determine race.' % Plugin)
            return
        inventory = get_inventory() or {}
        equip = (inventory.get('items') or [])
        if not any(item for slot, item in enumerate(equip[:13]) if slot != 8):
            return
        char_level = int(char.get('level', 0))
        mastery_level = 0
        if race == 'Europe':
            masteries = get_mastery() or {}
            mastery_level = max([int(m.get('level', 0)) for m in masteries.values()] or [0])
        db_path = _buy_items_db_path(client.get('path', ''))
        if not db_path:
            return
        char_key = get_character_key(char.get('name'))
        char_settings = character_settings.get(char_key, get_default_character_settings())
        bought_item_ids = char_settings.get('bought_items', [])

        legacy_ids = []
        for value in bought_item_ids:
            text_value = str(value or '').strip()
            if text_value.isdigit() and int(text_value) > 0:
                legacy_ids.append(int(text_value))
        if legacy_ids:
            try:
                conn = sqlite3.connect(db_path)
                placeholders = ','.join('?' for _ in legacy_ids)
                rows = conn.execute('SELECT id, servername FROM items WHERE id IN (%s)' % placeholders,
                                    tuple(legacy_ids)).fetchall()
                conn.close()
                id_to_name = {int(row[0]): str(row[1] or '').strip() for row in rows}
                migrated_names = []
                for value in bought_item_ids:
                    text_value = str(value or '').strip()
                    if text_value.isdigit():
                        name = id_to_name.get(int(text_value), '')
                    else:
                        name = text_value
                    if name and name not in migrated_names:
                        migrated_names.append(name)
                char_settings['bought_items'] = migrated_names
                bought_item_ids = migrated_names
                save_config()
            except Exception as migration_error:
                log('%s: Buy items: could not migrate old bought_items IDs: %s' % (Plugin, migration_error))

        upgrades = _buy_items_find_upgrades(db_path, race, char_level, mastery_level, bought_item_ids)
        if not upgrades:
            log('%s: Buy items: no higher NPC equipment available within character/mastery level limits.' % Plugin)
            return
        startpos = (current_region, int(pos.get('x', char.get('x', 0))), int(pos.get('y', char.get('y', 0))), int(pos.get('z', 0)))
        plan = _buy_items_make_script(upgrades, startpos)
        if not plan:
            log('%s: Buy items: no suitable town/vendor route found.' % Plugin)
            return

        total = sum(len(items) for items in plan['categories'].values())
        buy_items_state = {
            'phase': 'stop_wait', 'started': time.time(), 'watchdog_started': time.time(),
            'last_stop_request': time.time(), 'plan': plan, 'segment_index': 0,
            'buy_index': 0, 'buy_waiting': False,
            'character_key': get_character_key(char.get('name')),
            'town': plan['town'],
        }
        log('%s: Buy items: %d upgrade item(s) found for %s; stopping bot.' % (Plugin, total, plan['town']))
        stop_bot()
    except Exception as ex:
        buy_items_state = None
        log('%s: Buy items: preparation failed: %s' % (Plugin, ex))

def _buy_items_loop():
    global buy_items_state
    if not buy_items_state:
        return
    state = buy_items_state
    now = time.time()
    plan = state.get('plan') or {}

    if state.get('phase') not in ('restart_script', 'restart_wait_teleport', 'restart_final_wait') and now - state.get('watchdog_started', now) >= 120.0:
        log('%s: Buy items: 120-second timeout; jumping to Restartbot.' % Plugin)
        state['phase'] = 'restart_script'
        state['started'] = now

    def save_if_in_inventory(item, expected_quantity=1):
        item_id = int(item.get('id', 0) or 0)
        item_name = str(item.get('servername') or '').strip()
        if item_id <= 0 or not item_name:
            return False
            
        name_upper = item_name.upper()
        if '_RING_' in name_upper:
            target_count = 2
        else:
            target_count = 1
            
        bag_count = 0
        try:
            inventory = get_inventory() or {}
            items_list = inventory.get('items') or []
            for entry in items_list[13:]:
                if not entry:
                    continue
                matched = False
                for key in ('model', 'id', 'item_id'):
                    try:
                        if int(entry.get(key, -1)) == item_id:
                            matched = True
                            break
                    except Exception:
                        pass
                if not matched:
                    entry_sn = str(entry.get('servername') or '').strip().upper()
                    if entry_sn == name_upper:
                        matched = True
                if matched:
                    bag_count += max(1, int(entry.get('quantity', 1) or 1))
        except Exception:
            pass

        if bag_count >= target_count:
            key = state.get('character_key')
            settings = character_settings.get(key) if key else None
            if isinstance(settings, dict):
                bought = settings.setdefault('bought_items', [])
                normalized = []
                for value in bought:
                    value = str(value or '').strip()
                    if value and not value.isdigit() and value not in normalized:
                        normalized.append(value)
                if item_name not in normalized:
                    normalized.append(item_name)
                settings['bought_items'] = normalized
                save_config()
                log('%s: Buy items: confirmed %d of %s in inventory (target: %d); saved servername.' %
                    (Plugin, bag_count, item_name, target_count))
            return True
        return False

    phase = state.get('phase')
    if phase == 'stop_wait':
        if _bot_is_running():
            if now - state.get('last_stop_request', 0) >= 2.0:
                stop_bot()
                state['last_stop_request'] = now
            return
        if now - state.get('started', now) >= 1.0:
            state['phase'] = 'start_segment'

    elif phase == 'start_segment':
        segments = plan.get('segments', [])
        idx = state.get('segment_index', 0)
        if idx >= 3 or idx >= len(segments):
            state['phase'] = 'restart_delay'
            state['started'] = now
            return
        segment = segments[idx]
        try:
            start_script('\n'.join(segment.get('lines', [])))
            state['active_segment'] = segment
            state['phase'] = 'wait_endpoint'
            state['started'] = now
            state['last_position_check'] = 0.0
            log('%s: Buy items: started %s.' % (Plugin, segment.get('name', 'Town segment')))
        except Exception as ex:
            log('%s: Buy items: could not start %s: %s' % (Plugin, segment.get('name', 'Town segment'), ex))
            state['phase'] = 'restart_script'
            state['started'] = now

    elif phase == 'wait_endpoint':
        if now - state.get('last_position_check', 0.0) < 0.5:
            return
        state['last_position_check'] = now
        segment = state.get('active_segment') or {}
        endpoint = segment.get('endpoint')
        pos = get_position() or {}
        arrived = False
        if endpoint:
            try:
                arrived = (int(pos.get('region', 0)) == endpoint[0] and
                           abs(float(pos.get('x', 0)) - endpoint[1]) <= 3 and
                           abs(float(pos.get('y', 0)) - endpoint[2]) <= 3)
            except Exception:
                arrived = False

        if arrived:
            state['phase'] = 'endpoint_delay'
            state['started'] = now
            log('%s: Buy items: %s endpoint reached (X/Y tolerance +/-3); preparing to buy in 2 seconds.' %
                (Plugin, segment.get('name', 'Town segment')))
        elif now - state.get('started', now) > 120.0:
            # 120 Sekunden Timeout, falls der Punkt nicht erreicht wird
            log('%s: Buy items: %s timeout (120s) reached before endpoint; continuing.' % (Plugin, segment.get('name', 'Town segment')))
            state['phase'] = 'endpoint_delay'
            state['started'] = now

    elif phase == 'endpoint_delay':
        if now - state.get('started', now) < 2.0:
            return
        idx = state.get('segment_index', 0)
        category_by_segment = ['WeaponShield', 'Armor', 'Accessory']
        segment = state.get('active_segment') or {}
        endpoint = segment.get('endpoint') or (0, 0, 0)

        # Regionen-Check entfernt, da der phBot nun den Weg eigenständig findet

        try:
            db_path = _buy_items_db_path((get_client() or {}).get('path', ''))
            if globals().get('buy_keep_town_gold_enabled', False):
                town_gold_needed = _get_town_loop_gold_needed(db_path)
                actual_threshold = max(BUY_GOLD_THRESHOLD, town_gold_needed)
                log('%s: Buy items: Town Loop Gold needed: %d, Manual Threshold: %d -> Active: %d' %
                    (Plugin, town_gold_needed, BUY_GOLD_THRESHOLD, actual_threshold))
            else:
                actual_threshold = BUY_GOLD_THRESHOLD
        except Exception:
            actual_threshold = BUY_GOLD_THRESHOLD

        state['dynamic_threshold'] = actual_threshold
        state['category'] = category_by_segment[idx]
        state['buy_index'] = 0
        state['buy_waiting'] = False
        state['simulated_gold'] = _buy_items_get_gold()
        state['phase'] = 'buy_category'

    elif phase == 'buy_category':
        category = state.get('category')
        items = (plan.get('categories') or {}).get(category, [])
        idx = state.get('buy_index', 0)

        if idx >= len(items):
            state['phase'] = 'next_segment'
            return

        item = items[idx]
        price = _buy_items_get_price(item.get('id', 0))
        active_threshold = state.get('dynamic_threshold', BUY_GOLD_THRESHOLD)

        if state.get('buy_waiting'):
            if now - state.get('started', now) < 8.0:
                return
            state['simulated_gold'] -= price
            log('%s: Buy items: wait finished, simulated gold reduced. Moving to next item.' % Plugin)
            state['buy_index'] = idx + 1
            state['buy_waiting'] = False
            state['started'] = now
            return

        gold = state.get('simulated_gold', 0)
        if gold >= price + active_threshold:
            try:
                start_script('buy,%s,1' % item.get('servername', ''))
                log('%s: Buy items: started buy for %s (simulated gold=%d, price=%d, threshold=%d).' %
                    (Plugin, item.get('servername', ''), gold, price, active_threshold))
                state['buy_waiting'] = True
                state['started'] = now
            except Exception as ex:
                log('%s: Buy items: failed to start buy for %s: %s' % (Plugin, item.get('servername', ''), ex))
                state['buy_index'] = idx + 1
        else:
            log('%s: Buy items: insufficient gold for %s (needs %d + threshold %d).' %
                (Plugin, item.get('servername', ''), price, active_threshold))
            state['buy_index'] = idx + 1

    elif phase == 'next_segment':
        categories = plan.get('categories', {})
        category_by_segment = ['WeaponShield', 'Armor', 'Accessory']
        current_seg_idx = state.get('segment_index', 0)
        next_items_found = False

        for check_idx in range(current_seg_idx + 1, len(category_by_segment)):
            cat_name = category_by_segment[check_idx]
            if categories.get(cat_name):
                next_items_found = True
                break

        if next_items_found:
            state['segment_index'] = current_seg_idx + 1
            if state['segment_index'] < 3:
                state['phase'] = 'start_segment'
            else:
                state['phase'] = 'restart_delay'
                state['started'] = now
        else:
            log('%s: Buy items: No more items in remaining categories; skipping unused route segments.' % Plugin)
            state['phase'] = 'restart_delay'
            state['started'] = now

    elif phase == 'restart_delay':
        if now - state.get('started', now) >= 1.0:
            state['phase'] = 'restart_script'
            state['started'] = now

    elif phase == 'restart_script':
        pos = get_position() or {}
        char = get_character_data() or {}
        state['return_start'] = (float(char.get('x', pos.get('x', 0))),
                                 float(char.get('y', pos.get('y', 0))))
        try:
            start_script('use,returnscroll')
            state['phase'] = 'restart_wait_teleport'
            state['started'] = now
            state['last_teleport_check'] = now
            log('%s: Buy items: started returnscroll. Waiting for teleport.' % Plugin)
        except Exception as ex:
            log('%s: Buy items: returnscroll failed: %s' % (Plugin, ex))
            state['phase'] = 'restart_delay'
            state['started'] = now

    elif phase == 'restart_wait_teleport':
        if now - state.get('last_teleport_check', 0) >= 2.0:
            state['last_teleport_check'] = now
            char = get_character_data() or {}
            current = (float(char.get('x', 0)), float(char.get('y', 0)))
            original = state.get('return_start', current)

            teleported = abs(current[0] - original[0]) > 1.0 or abs(current[1] - original[1]) > 1.0
            timeout = now - state.get('started', now) >= 120.0

            if teleported or timeout:
                if timeout:
                    log('%s: Buy items: Teleport timeout reached (120s).' % Plugin)
                else:
                    log('%s: Buy items: Teleport detected.' % Plugin)
                state['phase'] = 'restart_final_wait'
                state['started'] = now

    elif phase == 'restart_final_wait':
        if now - state.get('started', now) >= 5.0:
            log('%s: Buy items: Sequence finished. Checking inventory for all bought items.' % Plugin)
            plan = state.get('plan', {})
            categories = plan.get('categories', {})
            for cat_name, items in categories.items():
                for item in items:
                    save_if_in_inventory(item, 1)
            log('%s: Buy items: Starting bot.' % Plugin)
            _ensure_bot_started('Buy items')
            buy_items_state = None

# ============================================================
# Auto Hometown Logic
# ============================================================
HOMETOWN_MAX_ATTEMPTS = 2
HOMETOWN_STOP_DELAY = 4.0
HOMETOWN_TELEPORT_DELAY = 2.0
HOMETOWN_SPAWN_DELAY = 1.0
HOMETOWN_TARGET_TOLERANCE = 3.0
HOMETOWN_RETRY_WAIT = 3.0

HOMETOWN_DEFAULTS = [
    {'enabled': False, 'race': 'Chinese', 'town': 'Jangan', 'level': 0, 'teleport': (25000, 6446, 1088, -32), 'spawn': (25000, 6433, 1099, -32)},
    {'enabled': True,  'race': 'Chinese', 'town': 'Donwhang', 'level': 28, 'teleport': (26265, 3552, 2088, -106), 'spawn': (26265, 3554, 2070, -106)},
    {'enabled': True,  'race': 'All',     'town': 'Hotan', 'level': 41, 'teleport': (23687, 113, 32, 244), 'spawn': (23687, 116, 15, 244)},
    {'enabled': True,  'race': 'Europe',  'town': 'Samarkand', 'level': 32, 'teleport': (27244, -5176, 2870, 192), 'spawn': (27244, -5157, 2830, 180)},
    {'enabled': False, 'race': 'Europe',  'town': 'Constantinople', 'level': 0, 'teleport': (26959, -10660, 2598, 83), 'spawn': (26959, -10654, 2601, 83)},
    {'enabled': False, 'race': 'All',     'town': 'Alexandria S', 'level': 101, 'teleport': (23088, -16643, -294, 863), 'spawn': (23088, -16635, -331, 863)},
    {'enabled': False, 'race': 'All',     'town': 'Alexandria N', 'level': 101, 'teleport': (23602, -16137, 61, 1525), 'spawn': (23603, -16117, 52, 1537)},
    {'enabled': False, 'race': 'All',     'town': 'Baghdad', 'level': 130, 'teleport': (22618,-8534,-718,-236), 'spawn': (22618,-8533,-736,-236)},
    {'enabled': False, 'race': 'All',     'town': 'Jangan', 'level': 0, 'teleport': (25000, 6446, 1088, -32), 'spawn': (25000, 6433, 1099, -32), 'custom_town': True},
]

hometown_rules = []
hometown_state = None
hometown_last_character = None
hometown_last_tab1_signature = None
hometown_last_check = 0.0
auto_settings_signature = None

def _hometown_copy_defaults():
    return [dict(r, teleport=tuple(r['teleport']), spawn=tuple(r['spawn'])) for r in HOMETOWN_DEFAULTS]

def _hometown_race_options():
    return ['Chinese', 'Europe', 'All']

def _hometown_town_options():
    return ['Jangan', 'Donwhang', 'Hotan', 'Samarkand', 'Constantinople', 'Alexandria S', 'Alexandria N', 'Baghdad']

def _hometown_build_tab1():
    global hometown_master_check
    x = 450
    hometown_master_check = QtBind.createCheckBox(tab2, 'hometown_master_clicked', '', x - 3, 5)
    QtBind.createLabel(tab2, '<b>Enable Auto Hometown</b>', x + 22, 10)
    QtBind.createLabel(tab2, 'Set Hometown at a given Level per Race', x + 0, 33)
    y = 55
    QtBind.createLabel(tab2, 'Enable', x + 0, y)
    QtBind.createLabel(tab2, 'Race', x + 45, y)
    QtBind.createLabel(tab2, 'Town', x + 120, y)
    QtBind.createLabel(tab2, 'At Lvl', x + 212, y)
    for i, rule in enumerate(HOMETOWN_DEFAULTS):
        yy = y + 23 + i * 27
        rule['check'] = QtBind.createCheckBox(tab2, 'hometown_enable_clicked', '', x - 3, yy - 4)
        if rule.get('custom_town'):
            rule['race_label'] = QtBind.createLabel(tab2, 'All', x + 38, yy + 2)
            rule['combo'] = QtBind.createCombobox(tab2, x + 95, yy - 3, 115, 21)
            for town_name in _hometown_town_options():
                QtBind.append(tab2, rule['combo'], town_name)
        else:
            rule['combo'] = QtBind.createCombobox(tab2, x + 30, yy - 3, 80, 21)
            for race in _hometown_race_options():
                QtBind.append(tab2, rule['combo'], race)
            QtBind.createLabel(tab2, rule['town'], x + 120, yy + 2)
        rule['level_edit'] = QtBind.createLineEdit(tab2, str(rule['level']), x + 210, yy - 3, 45, 21)

_hometown_build_tab1()

def _hometown_character_defaults():
    return {'hometown_rules': [dict(r, teleport=tuple(r['teleport']), spawn=tuple(r['spawn'])) for r in HOMETOWN_DEFAULTS]}

def _hometown_ensure_character():
    global current_character
    global hometown_rules
    char = get_character_key()
    if not char:
        return False
    current_character = char
    settings = character_settings.setdefault(char, get_default_character_settings())
    rules = settings.get('hometown_rules') if isinstance(settings, dict) else None
    if not isinstance(rules, list) or len(rules) != len(HOMETOWN_DEFAULTS) or any(not isinstance(r, dict) for r in rules):
        rules = _hometown_character_defaults()['hometown_rules']
        settings['hometown_rules'] = rules
    hometown_rules = rules
    return True

def _hometown_refresh_tab1():
    if not _hometown_ensure_character():
        return
    settings = character_settings.get(current_character, {})
    QtBind.setChecked(tab2, hometown_master_check, bool(settings.get('hometown_enabled', True)))
    for i, rule in enumerate(hometown_rules):
        base = HOMETOWN_DEFAULTS[i]
        QtBind.setChecked(tab2, base['check'], bool(rule.get('enabled', False)))
        QtBind.setText(tab2, base['level_edit'], str(int(rule.get('level', base['level']))))
        try:
            QtBind.setText(tab2, base['combo'], rule.get('town', base['town']) if base.get('custom_town') else rule.get('race', base['race']))
        except Exception:
            pass

def _hometown_read_tab1(save=True):
    global hometown_rules
    if not _hometown_ensure_character():
        return False
    changed = False
    for i, base in enumerate(HOMETOWN_DEFAULTS):
        rule = hometown_rules[i]
        enabled_now = bool(QtBind.isChecked(tab2, base['check']))
        if base.get('custom_town'):
            town_now = QtBind.text(tab2, base['combo']).strip()
            if town_now not in _hometown_town_options():
                town_now = str(rule.get('town', 'Jangan'))
            race_now = 'All'
            town_base = next((r for r in HOMETOWN_DEFAULTS if not r.get('custom_town') and r['town'] == town_now), HOMETOWN_DEFAULTS[0])
        else:
            race_now = QtBind.text(tab2, base['combo']).strip()
            if race_now not in _hometown_race_options():
                race_now = base['race']
            town_now = rule.get('town', base['town'])
            town_base = None
        try:
            level_now = int(QtBind.text(tab2, base['level_edit']).strip())
        except Exception:
            level_now = int(rule.get('level', base['level']))
        level_now = max(0, min(255, level_now))
        if (rule.get('enabled') != enabled_now or rule.get('race') != race_now or int(rule.get('level', 0)) != level_now or (base.get('custom_town') and rule.get('town') != town_now)):
            rule['enabled'] = enabled_now
            rule['race'] = race_now
            rule['level'] = level_now
            if base.get('custom_town'):
                rule['town'] = town_now
                rule['teleport'] = tuple(town_base['teleport'])
                rule['spawn'] = tuple(town_base['spawn'])
            changed = True
        QtBind.setText(tab2, base['level_edit'], str(level_now))
    if changed and save:
        character_settings[current_character]['hometown_rules'] = hometown_rules
        if not any(bool(rule.get('enabled', False)) for rule in hometown_rules):
            character_settings[current_character]['hometown_enabled'] = False
            QtBind.setChecked(tab2, hometown_master_check, False)
        save_config()
    return changed

def hometown_master_clicked(checked):
    if not _hometown_ensure_character():
        return
    character_settings[current_character]['hometown_enabled'] = bool(checked)
    save_config()
    log('%s: Auto Hometown manually %s for [%s].' % (Plugin, 'enabled' if checked else 'disabled', current_character))

def hometown_enable_clicked(checked):
    _hometown_read_tab1(save=True)

def _hometown_signature():
    sig = []
    try:
        master = bool(QtBind.isChecked(tab2, hometown_master_check))
    except Exception:
        master = True
    sig.append(('master', master))
    for base in HOMETOWN_DEFAULTS:
        try: level = QtBind.text(tab2, base['level_edit']).strip()
        except Exception: level = ''
        try: race = QtBind.text(tab2, base['combo']).strip()
        except Exception: race = ''
        try: enabled_now = bool(QtBind.isChecked(tab2, base['check']))
        except Exception: enabled_now = False
        sig.append((enabled_now, race, level))
    return tuple(sig)

def _hometown_current_region():
    try:
        p = get_position()
        return int(p.get('region', 0)) if p else 0
    except Exception:
        return 0

def _hometown_current_town():
    region = _hometown_current_region()
    for rule in HOMETOWN_DEFAULTS:
        if int(rule['spawn'][0]) == region or int(rule['teleport'][0]) == region:
            return rule['town']
    return None

def _hometown_rule_matches(rule, race, level):
    return bool(rule.get('enabled')) and int(rule.get('level', 0)) <= level and rule.get('race') in ('All', race)

def _hometown_select_rule(race, level):
    candidates = [r for r in hometown_rules if _hometown_rule_matches(r, race, level)]
    if not candidates:
        return None
    return max(candidates, key=lambda r: int(r.get('level', 0)))

def _hometown_generate_and_start(target, label):
    region, x, y, z = target
    try:
        lines = generate_script(region, x, y, z)
    except Exception as ex:
        log('%s: Auto Hometown: generate_script failed [%s]: %s' % (Plugin, label, ex))
        return False
    if not lines:
        log('%s: Auto Hometown: generate_script returned no route [%s].' % (Plugin, label))
        return False
    lines = [str(line).strip() for line in lines if str(line).strip()]
    try:
        start_script('\n'.join(lines))
    except Exception as ex:
        log('%s: Auto Hometown: start_script failed [%s]: %s' % (Plugin, label, ex))
        return False
    log('%s: Auto Hometown: Walk to [%s].' % (Plugin, label))
    return True

def _hometown_disable_through_level(level):
    changed = False
    for i, rule in enumerate(hometown_rules):
        if int(rule.get('level', 0)) <= level and rule.get('enabled'):
            rule['enabled'] = False
            changed = True
    if changed:
        character_settings[current_character]['hometown_rules'] = hometown_rules
        if not any(bool(item.get('enabled', False)) for item in hometown_rules):
            character_settings[current_character]['hometown_enabled'] = False
        _hometown_refresh_tab1()
        save_config()

def _hometown_finish(rule):
    level = int(rule.get('level', 0))
    _hometown_disable_through_level(level)

HOMETOWN_REGION_NAMES = {
    25000: 'Jangan',
    26265: 'Donwhang',
    23687: 'Hotan',
    27244: 'Samarkand',
    26959: 'Constantinople',
    23602: 'alexandria',
    23603: 'alexandria',
    23088: 'alexandria',
    22618: 'Baghdad',
}

def _hometown_find_recall_npc(rule):
    target_region = int(rule['spawn'][0])
    expected_name = HOMETOWN_REGION_NAMES.get(target_region, rule.get('town', ''))
    npcs = get_npcs() or {}
    for uid, npc in npcs.items():
        npc_name = str(npc.get('name', ''))
        if expected_name.strip().lower() in npc_name.strip().lower():
            return uid, npc_name
    return 0, expected_name

def _hometown_set_recall(rule):
    try:
        uid, npc_name = _hometown_find_recall_npc(rule)
        if not uid:
            return False
        import struct
        inject_joymax(0x7059, struct.pack('<I', int(uid)), False)
        log('%s: New Hometown [%s] is set.' % (Plugin, rule.get('town', npc_name)))
        return True
    except Exception as ex:
        log('%s: Auto Hometown: recall failed for [%s]: %s' % (Plugin, rule.get('town', '?'), ex))
        return False

def _hometown_start_change(rule):
    global hometown_state
    hometown_state = {
        'rule': rule,
        'attempt': 1,
        'phase': 'stop_wait',
        'started': time.time(),
        'target_kind': 'teleport'
    }
    log('%s: Auto Hometown: starting change to %s (attempt %d/%d).' % (Plugin, rule['town'], hometown_state['attempt'], HOMETOWN_MAX_ATTEMPTS))
    try:
        stop_bot()
    except Exception:
        pass

def _hometown_retry_or_disable():
    global hometown_state
    if not hometown_state:
        return
    rule = hometown_state['rule']
    attempt = hometown_state['attempt']
    if attempt >= HOMETOWN_MAX_ATTEMPTS:
        log('%s: Auto Hometown: %d/%d attempts failed. Rule [%s] disabled.' % (Plugin, attempt, HOMETOWN_MAX_ATTEMPTS, rule['town']))
        rule['enabled'] = False
        if not any(bool(item.get('enabled', False)) for item in hometown_rules):
            character_settings[current_character]['hometown_enabled'] = False
        _hometown_refresh_tab1()
        save_config()
        hometown_state = None
        _ensure_bot_started('Auto Hometown')
        return
    hometown_state['attempt'] = attempt + 1
    hometown_state['phase'] = 'retry_wait'
    hometown_state['started'] = time.time()
    log('%s: Auto Hometown: retrying [%s] attempt %d/%d.' % (Plugin, rule['town'], hometown_state['attempt'], HOMETOWN_MAX_ATTEMPTS))

def _auto_save_tab1_settings():
    global auto_settings_signature
    global BUY_GOLD_THRESHOLD
    global buy_keep_town_gold_enabled

    if loading_character_settings or not current_character:
        return
    try:
        sig = (
            bool(QtBind.isChecked(tab1, checkEnable)),
            bool(QtBind.isChecked(tab1, checkSolo)),
            QtBind.text(tab1, editMembers).strip(),
            QtBind.text(tab1, editLevelOffset).strip(),
            bool(QtBind.isChecked(tab1, checkXControl)),
            QtBind.text(tab1, editXControlStop),
            QtBind.text(tab1, editXControlDelay1),
            QtBind.text(tab1, editXControlSetPos),
            QtBind.text(tab1, editXControlSetRange),
            QtBind.text(tab1, editXControlDelay2),
            QtBind.text(tab1, editXControlStart),
            QtBind.text(tab2, buy_gold_threshold_edit).strip() if 'buy_gold_threshold_edit' in globals() else '0',
            bool(QtBind.isChecked(tab2, buy_keep_town_gold_check)) if 'buy_keep_town_gold_check' in globals() else False
        )
    except Exception:
        return
    if auto_settings_signature is None:
        auto_settings_signature = sig
        return
    if sig == auto_settings_signature:
        return
    auto_settings_signature = sig
    try:
        checkEnable_clicked(sig[0])
        checkSolo_clicked(sig[1])
        saveMembers_clicked()
        saveLevelOffset_clicked()
        read_xcontrol_tab1()
        try:
            threshold_text = QtBind.text(tab2, buy_gold_threshold_edit).strip()
            threshold_value = max(0, int(threshold_text)) if threshold_text else 0
        except Exception:
            threshold_value = 0
        BUY_GOLD_THRESHOLD = threshold_value
        QtBind.setText(tab2, buy_gold_threshold_edit, str(threshold_value))
        buy_keep_town_gold_enabled = sig[12]

        save_character_settings()
        save_config()
    except Exception as ex:
        log('%s: Automatic GUI save error: %s' % (Plugin, ex))

def _bot_is_running():
    try:
        data = get_character_data()
    except Exception:
        return False
    return bool(data.get('botting', False)) if isinstance(data, dict) else False

def _ensure_bot_started(context):
    if _bot_is_running():
        return True
    try:
        started = start_bot()
        if started:
            return True
        log('%s: %s: start_bot() did not confirm that the bot started.' % (Plugin, context))
    except Exception as ex:
        log('%s: %s: start_bot failed: %s' % (Plugin, context, ex))
    return False

def _hometown_loop():
    global hometown_state
    global hometown_last_check
    global hometown_last_character
    global hometown_last_tab1_signature

    char = get_character_key()
    if not char:
        return
    if char != hometown_last_character:
        hometown_last_character = char
        _hometown_ensure_character()
        _hometown_refresh_tab1()
        hometown_last_tab1_signature = _hometown_signature()
        hometown_state = None
        hometown_last_check = 0.0
        return

    sig = _hometown_signature()
    if sig != hometown_last_tab1_signature:
        master_now = bool(sig[0][1]) if sig and sig[0][0] == 'master' else True
        if master_now:
            _hometown_read_tab1(save=True)
        else:
            character_settings[current_character]['hometown_enabled'] = False
            save_config()
        hometown_last_tab1_signature = sig

    now = time.time()

    if hometown_state:
        phase = hometown_state['phase']
        rule = hometown_state['rule']

        if phase == 'retry_wait':
            if now - hometown_state['started'] >= HOMETOWN_RETRY_WAIT:
                hometown_state['phase'] = 'stop_wait'
                hometown_state['started'] = now
                try:
                    stop_bot()
                except Exception:
                    pass
            return

        if phase == 'stop_wait':
            if now - hometown_state['started'] >= HOMETOWN_STOP_DELAY:
                hometown_state['phase'] = 'route_to_destination'
                hometown_state['started'] = now
                if not _hometown_generate_and_start(rule['teleport'], 'TELEPORT %s' % rule['town']):
                    _hometown_retry_or_disable()
            return

        if phase == 'route_to_destination':
            try:
                pos = get_position() or {}
                px = float(pos.get('x', 0))
                py = float(pos.get('y', 0))
                pregion = int(pos.get('region', 0))
                target_region = int(rule['teleport'][0])
                target_x = float(rule['teleport'][1])
                target_y = float(rule['teleport'][2])
                close_xy = (abs(px - target_x) <= HOMETOWN_TARGET_TOLERANCE and
                            abs(py - target_y) <= HOMETOWN_TARGET_TOLERANCE)
                if pregion == target_region and close_xy:
                    hometown_state['phase'] = 'before_recall'
                    hometown_state['started'] = now
                    log('%s: Auto Hometown: teleport point [%s] reached. Waiting %.1fs before recall.' % (Plugin, rule['town'], HOMETOWN_TELEPORT_DELAY))
                elif now - hometown_state['started'] > 120:
                    log('%s: Auto Hometown: teleport point [%s] not reached after 120s.' % (Plugin, rule['town']))
                    _hometown_retry_or_disable()
            except Exception as ex:
                log('%s: Auto Hometown: destination position check error: %s' % (Plugin, ex))
            return

        if phase == 'before_recall':
            if now - hometown_state['started'] >= HOMETOWN_TELEPORT_DELAY:
                if _hometown_set_recall(rule):
                    hometown_state['phase'] = 'after_recall_wait'
                    hometown_state['started'] = now
                else:
                    _hometown_retry_or_disable()
            return

        if phase == 'after_recall_wait':
            if now - hometown_state['started'] >= HOMETOWN_SPAWN_DELAY:
                hometown_state['phase'] = 'route_to_spawn'
                hometown_state['started'] = now
                if not _hometown_generate_and_start(rule['spawn'], 'SPAWN %s' % rule['town']):
                    _hometown_retry_or_disable()
            return

        if phase == 'route_to_spawn':
            try:
                pos = get_position() or {}
                px = float(pos.get('x', 0))
                py = float(pos.get('y', 0))
                pregion = int(pos.get('region', 0))
                target_region = int(rule['spawn'][0])
                target_x = float(rule['spawn'][1])
                target_y = float(rule['spawn'][2])
                close_xy = (abs(px - target_x) <= HOMETOWN_TARGET_TOLERANCE and
                            abs(py - target_y) <= HOMETOWN_TARGET_TOLERANCE)
                if pregion == target_region and close_xy:
                    hometown_state['phase'] = 'before_start'
                    hometown_state['started'] = now
                    log('%s: Auto Hometown: spawn [%s] reached. Waiting %.1fs before bot start.' % (Plugin, rule['town'], HOMETOWN_SPAWN_DELAY))
                elif now - hometown_state['started'] > 120:
                    log('%s: Auto Hometown: spawn [%s] not reached after 120s.' % (Plugin, rule['town']))
                    _hometown_retry_or_disable()
            except Exception as ex:
                log('%s: Auto Hometown: spawn position check error: %s' % (Plugin, ex))
            return

        if phase == 'before_start':
            if now - hometown_state['started'] >= HOMETOWN_SPAWN_DELAY:
                _hometown_finish(rule)
                hometown_state = None
                _ensure_bot_started('Auto Hometown')
            return
        return

    settings = character_settings.get(current_character, {})
    if not bool(settings.get('hometown_enabled', True)):
        return

    try:
        char_data = get_character_data()
    except Exception:
        return
    if not isinstance(char_data, dict) or not bool(char_data.get('botting', False)):
        return

    current_region = _hometown_current_region()
    town_regions = {int(r['teleport'][0]) for r in HOMETOWN_DEFAULTS} | {int(r['spawn'][0]) for r in HOMETOWN_DEFAULTS}
    if current_region not in town_regions:
        return

    if now - hometown_last_check < 2.0:
        return
    hometown_last_check = now

    level = int(char_data.get('level', 0))
    race = get_character_race()
    if race not in ('Chinese', 'Europe'):
        return

    _hometown_ensure_character()
    rule = _hometown_select_rule(race, level)
    if not rule:
        return

    current_town = _hometown_current_town() or ('Region %d' % current_region)
    log('%s: Auto Hometown: Change town from %s to %s' % (Plugin, current_town, rule['town']))
    log('%s: Auto Hometown: Generate script from Region %d X %d Y %d Z %d to' % (Plugin, current_region, int(get_position().get('x', 0)), int(get_position().get('y', 0)), int(get_position().get('z', 0))))
    log('%s: Auto Hometown: %s Region %d X %d Y %d Z %d' % (Plugin, rule['town'], int(rule['spawn'][0]), int(rule['spawn'][1]), int(rule['spawn'][2]), int(rule['spawn'][3])))
    _hometown_start_change(rule)

# ============================================================
# Game & phBot Events
# ============================================================
def load_character_settings_when_ready():
    character = get_character_name()
    if character:
        load_character_settings()
        return
    Timer(2.0, load_character_settings_when_ready, []).start()

def joined_game():
    global area_change_pending
    global pending_area
    global area_change_stage

    cancel_area_change_timer()
    area_change_pending = False
    pending_area = None
    area_change_stage = 0
    reset_area_change_death_timer()

    log('%s: Character joined game.' % Plugin)
    Timer(1.0, load_character_settings_when_ready, []).start()

def teleported():
    global buy_items_pending
    try:
        if buy_items_state:
            log('%s: Buy items: teleport ignored; AutoBuy is already running.' % Plugin)
            return
        if buy_items_pending:
            return
        buy_items_pending = True
    except Exception as ex:
        log('%s: Buy items: teleport trigger failed: %s' % (Plugin, ex))

def handle_joymax(opcode, data):
    if enabled and opcode == 0x3056:
        check_party()
    return True

def handle_event(t, data):
    global area_change_pending
    global area_change_death_remaining

    if t == 7 and area_change_pending and area_change_stage in (1, 2):
        area_change_death_remaining = DEATH_WAIT_TIMEOUT
        log('%s: Character died during area change. Maximum recovery wait is %d seconds.' % (Plugin, DEATH_WAIT_TIMEOUT))
        schedule_area_change(1.0)

def event_loop():
    global buy_items_pending
    try:
        _auto_save_tab1_settings()
        _hometown_loop()
        _buy_items_loop()
        if buy_items_pending and not hometown_state and not buy_items_state:
            buy_items_pending = False
            Timer(1.0, _buy_items_after_teleport, []).start()
    except Exception as ex:
        log('%s: BetterTraining loop error: %s' % (Plugin, ex))

# ============================================================
# Startup
# ============================================================
load_config()
Timer(2.0, load_character_settings_when_ready, []).start()

log('Plugin: %s by Chefkoch, Inspired by Bine11 AutoTraining' % Plugin)
log('Plugin: %s v%s successfully loaded!' % (Plugin, PluginVersion))