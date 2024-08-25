import json
from  website_data import const_items, const_traps, const_randomList, const_refinery, const_monsters, const_classes, const_seedInfo, const_bubResources, const_bubbleCosts
from datetime import datetime, timedelta
from functools import reduce
import re
import math


def parse_all(raw_json):
    if raw_json:
        try:
            # 首先解析顶层的 JSON
            raw_data_dict = json.loads(raw_json)
            # 递归解析嵌套的 JSON 字符串
            parsed_data = parse_nested_json(raw_data_dict)
            #print(json.dumps(parsed_data, indent=4))  # 格式化打印输出
        except json.JSONDecodeError as e:
            print(f"Failed to parse rawData: {e}")
    else:
        print("rawData not found in localStorage.")

    
    idleonData = parsed_data['data']
    charNames = parsed_data['charNames']

    storage_data = get_storage(idleonData,'storage')

    serialized_characters_data = get_characters(idleonData, charNames)

    traps_data = parse_traps(serialized_characters_data)
    eggs = get_eggs(idleonData)
    salts = get_salts(idleonData, storage_data)
    liquids = get_liquids(idleonData)
    charactersLevels = get_charactersLevels(serialized_characters_data)
    charactersData = get_charactersData(serialized_characters_data)
    plot = get_plot(idleonData)
    jade_coins = get_jade_coins(idleonData)

    charactersImportant = get_charactersImportant(serialized_characters_data)
    alchemyResource = get_alchemyResource(idleonData, jade_coins)

    account = {
        "alchemy": {
            "liquids":liquids
        },
        "breeding": {
            "eggs": eggs
        },
        "charactersLevels": charactersLevels,
        "farming": plot,
        "refinery": {
            "salts": salts
        },
        "sneaking": {
            "jadeCoins": jade_coins
        },
        "storage": storage_data,
        "traps": traps_data,
        
    }

    importantData = {
        "liquids": liquids,
        "charactersImportant": charactersImportant,
        "jadeCoins": jade_coins,
        "alchemyResource": alchemyResource
    }

    object_data = {
        "account": account,
        "characters": charactersData,
        "important": importantData,
    }

    return importantData



def parse_nested_json(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    # 尝试将字符串转换为字典或列表
                    parsed_value = json.loads(value)
                    # 递归解析嵌套结构
                    data[key] = parse_nested_json(parsed_value)
                except (json.JSONDecodeError, TypeError):
                    # 如果解析失败，则保留原字符串
                    data[key] = value
            elif isinstance(value, (dict, list)):
                # 递归处理字典或列表
                data[key] = parse_nested_json(value)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, str):
                try:
                    # 尝试将字符串转换为字典或列表
                    parsed_item = json.loads(item)
                    # 递归解析嵌套结构
                    data[index] = parse_nested_json(parsed_item)
                except (json.JSONDecodeError, TypeError):
                    # 如果解析失败，则保留原字符串
                    data[index] = item
            elif isinstance(item, (dict, list)):
                # 递归处理字典或列表
                data[index] = parse_nested_json(item)
    return data


def try_to_parse(s):
    try:
        return json.loads(s)
    except (ValueError, TypeError):
        return s
    
def get_storage(idleon_data, name):
    chest_order_raw = idleon_data.get('ChestOrder') or try_to_parse(idleon_data.get('ChestOrder'))
    chest_quantity_raw = idleon_data.get('ChestQuantity') or try_to_parse(idleon_data.get('ChestQuantity'))
    return get_inventory(chest_order_raw, chest_quantity_raw, name)

def get_inventory(inventory_arr, inventory_quantity_arr, owner):
    result = []
    for index, item_name in enumerate(inventory_arr):
        description = ''
        for num in range(1, 9):
            desc_line = const_items.get(item_name, {}).get(f'desc_line{num}')
            if desc_line:
                description += f'{desc_line} '
        
        it = const_items.get(item_name, {})


        if item_name not in ['LockedInvSpace', 'Blank']:
            result.append({
                **it,
                'owner': owner,
                'name': it.get('displayName'),
                'type': it.get('itemType'),
                'subType': it.get('Type'),
                'rawName': item_name,
                'amount': int(inventory_quantity_arr[index]) if inventory_quantity_arr else 0,
            })
    return result

def get_alchemyResource(idleon_data, jadeCoins):
    chest_order_raw =  idleon_data.get('ChestOrder') or try_to_parse(idleon_data.get('ChestOrder'))
    chest_quantity_raw = idleon_data.get('ChestQuantity') or try_to_parse(idleon_data.get('ChestQuantity'))
    return get_bubblecosts(chest_order_raw, chest_quantity_raw, jadeCoins)

def get_bubblecosts(inventory_arr, inventory_quantity_arr, jadeCoins):
    cost_result = {}
    click_down_page_times = 5
    click_up_page_times  = 0
    for index, item_name in enumerate(inventory_arr):
        it = const_items.get(item_name, {})
        displayName = it.get('displayName')
        if item_name not in ['LockedInvSpace', 'Blank']:
            if displayName in const_bubResources:
                amount = int(inventory_quantity_arr[index]) if inventory_quantity_arr else 0
                if amount >= 1e9:
                    resource_info = const_bubbleCosts.get(displayName)
                    bubble_name = resource_info.get("name")
                    bubble_color = resource_info.get("color")
                    cost_result[bubble_name] = {
                        "colour": bubble_color,
                        "click_down_page_times": click_down_page_times,
                        "click_up_page_times": click_up_page_times
                    }
                    #cost_result.append(f"{bubble_name}:{{colour: {bubble_color}, click_down_page_times:5, click_up_page_times:0}}")

    if jadeCoins >= 1e9:
        bubble_name = 'essence_chapter'
        bubble_color = 'purple'
        cost_result[bubble_name] = {
                        "colour": bubble_color,
                        "click_down_page_times": click_down_page_times,
                        "click_up_page_times": click_up_page_times
                    }
        
    return cost_result



def create_array_of_arrays(array):
    if array is None:
        return None
    return [
        list(obj.values()) if isinstance(obj, dict) else obj
        for obj in array
    ]

def create_indexed_array(obj):
    highest = max(map(int, obj.keys())) if obj else 0
    result = []
    for i in range(highest + 1):
        result.append(obj.get(str(i), {}))
    return result


def get_characters(idleonData, charNames):
    chars = charNames or list(range(9))
    characters = []

    for player_id, char_name in enumerate(chars):
        character_details = {}
        for key, details in idleonData.items():
            reg = f"_{player_id}"
            if reg in key:
                updated_key = key
                updated_details = try_to_parse(details)
                arr = []
                
                if "EquipOrder" in key:
                    updated_key = "EquipmentOrder"
                    updated_details = create_array_of_arrays(details)
                elif "EquipQTY" in key:
                    updated_key = "EquipmentQuantity"
                    updated_details = create_array_of_arrays(details)
                elif "AnvilPA_" in key:
                    updated_key = "AnvilPA"
                    updated_details = create_array_of_arrays(details)
                elif "EMm0" in key:
                    updated_key = "EquipmentMap"
                    arr = character_details.get(updated_key, [])
                    det = create_indexed_array(updated_details)
                    arr.insert(0, det)
                elif "IMm_" in key:
                    updated_key = "InventoryMap"
                elif "EMm1" in key:
                    updated_key = "EquipmentMap"
                    arr = character_details.get(updated_key, [])
                    det = create_indexed_array(updated_details)
                    arr.insert(1, det)
                elif "BuffsActive" in key:
                    updated_key = "BuffsActive"
                    arr = create_array_of_arrays(updated_details)
                elif "ItemQTY" in key:
                    updated_key = "ItemQuantity"
                elif "PVStatList" in key:
                    updated_key = "PersonalValuesMap"
                    updated_details = {**character_details.get(updated_key, {}), "StatList": try_to_parse(details)}
                elif "PVtStarSign" in key:
                    updated_key = "PersonalValuesMap"
                    updated_details = {**character_details.get(updated_key, {}), "StarSign": try_to_parse(details)}
                elif "ObolEqO0" in key:
                    updated_key = "ObolEquippedOrder"
                elif "ObolEqMAP" in key:
                    updated_key = "ObolEquippedMap"
                elif "SL_" in key:
                    updated_key = "SkillLevels"
                elif "SLpre_" in key:
                    updated_key = "SkillPreset"
                elif "SM_" in key:
                    updated_key = "SkillLevelsMAX"
                elif "KLA_" in key:
                    updated_key = "KillsLeft2Advance"
                elif "AtkCD_" in key:
                    updated_key = "AttackCooldowns"
                elif "POu_" in key:
                    updated_key = "PostOfficeInfo"
                elif "PTimeAway" in key:
                    updated_key = "PlayerAwayTime"
                    updated_details = updated_details * 1000
                else:
                    updated_key = key.split("_")[0]

                if arr:
                    character_details[updated_key] = arr
                else:
                    character_details[updated_key] = updated_details
        
        characters.append({
            "name": char_name,
            "playerId": player_id,
            **character_details
        })
    
    return characters

def parse_traps(raw_characters_data):
    parsed_traps = []
    for char in raw_characters_data:
        traps = char.get("PldTraps", [])
        char_traps = []
        for critter_info in traps:
            # 只提取前 8 个元素，避免超出期望的数量
            if len(critter_info) >= 8:
                critter_id, _, time_elapsed, critter_name, critters_quantity, trap_type, trap_time, trap_exp = critter_info[:8]
            else:
                continue  # 如果元素不够，跳过这条记录
            
            if critter_id == -1 or critter_id == "-1":
                continue
            
            # 查找陷阱数据
            trap_data = next((trap for trap in const_traps[trap_type] if trap['trapTime'] == trap_time), None)
            time_left = trap_time - time_elapsed
            
            if critter_name:
                char_traps.append({
                    "name": const_items.get(critter_name, {}).get("displayName"),
                    "rawName": critter_name,
                    "crittersQuantity": critters_quantity,
                    "trapType": trap_type,
                    "trapExp": trap_exp,
                    "timeLeft": datetime.now() + timedelta(seconds=time_left),
                    "trapData": trap_data
                })
        
        parsed_traps.append(char_traps)
    return parsed_traps

def calculate_item_total_amount(array, item_name, exact, is_raw_name=False):
    if not array:
        return 0
    return reduce(lambda result, item: result + (
        item['amount'] if (
            (item_name == (item['rawName'] if is_raw_name else item['name'])) if exact else 
            ((item['rawName'] if is_raw_name else item['name']).find(item_name) != -1)
        ) else 0
    ), array, 0)

def get_power_cap(rank):
    power_cap = const_randomList[18].split(' ') if const_randomList[18] else []
    return float(max(float(power_cap[min(rank, len(power_cap) - 2)]), 25)) if power_cap else 25

def has_missing_mats(salt_index, rank, cost, account):
    return list(filter(lambda item: item['totalAmount'] < math.floor(math.pow(rank, 
        1.3 if 'Refinery' in item['rawName'] and salt_index <= account.get('refinery', {}).get('refinerySaltTaskLevel', 0) else 1.5)) * item['quantity'], cost))

def parse_refinery(refinery_raw, storage):
    refinery_storage_raw = refinery_raw[1] if refinery_raw and len(refinery_raw) > 1 else []
    refinery_storage_quantity_raw = refinery_raw[2] if refinery_raw and len(refinery_raw) > 2 else []
    
    refinery_storage = [
        {
            'rawName': salt_name,
            'name': const_items.get(salt_name, {}).get('displayName'),
            'amount': refinery_storage_quantity_raw[index],
            'owner': 'refinery'
        } for index, salt_name in enumerate(refinery_storage_raw) if salt_name != 'Blank'
    ]
    
    combined_storage = storage + refinery_storage
    salts = refinery_raw[3:3 + refinery_raw[0][0]] if refinery_raw and refinery_raw[0] else []
    salts_array = []
    for index, salt in enumerate(salts):
        name = f"Refinery{index + 1}"
        refined, rank, _, active, auto_refine_percentage = salt
        refinery_config = const_refinery.get(name, {})
        salt_name = refinery_config.get('saltName')
        cost = refinery_config.get('cost', [])
        
        components_with_total_amount = [
            {
                **item,
                'totalAmount': calculate_item_total_amount(combined_storage, item['name'], True)
            } for item in cost
        ]
        
        salts_array.append({
            'saltName': salt_name,
            'cost': components_with_total_amount,
            'rawName': name,
            'powerCap': get_power_cap(rank),
            'refined': refined,
            'rank': rank,
            'active': active,
            'autoRefinePercentage': auto_refine_percentage
        })
    
    return salts_array

def create_array_of_arrays(array):
    if not array:
        return None

    result = []
    for obj in array:
        if not isinstance(obj, list):
            obj.pop('length', None)  
        result.append(list(obj.values()) if isinstance(obj, dict) else obj)
    
    return result

def get_charactersLevels(serialized_characters_data):
    charactersLevels = []
    for char in serialized_characters_data:
        character_class = char.get('CharacterClass', None)
        if isinstance(character_class, int) and character_class < len(const_classes):
            class_name = const_classes[character_class]
        else:
            class_name = ''
        
        charactersLevels.append({
            'level': char.get('PersonalValuesMap', {}).get('StatList', [0]*5)[4],
            'class': class_name
        })
    return charactersLevels

def get_charactersImportant(serialized_characters_data):
    charactersImportant = {}
    number = 1
    for char in serialized_characters_data:
        character_class = char.get('CharacterClass', None)
        if isinstance(character_class, int) and character_class < len(const_classes):
            class_name = const_classes[character_class]
        else:
            class_name = ''
        charactersImportant[number] = class_name
        number = number + 1
    return charactersImportant

def get_characters(idleon_data, chars_names=None):
    if chars_names is None:
        chars_names = list(range(9))

    characters = []
    for player_id, char_name in enumerate(chars_names):
        character_details = {}

        for key, details in idleon_data.items():
            reg = re.compile(f'_{player_id}')
            if reg.search(key):
                updated_details = try_to_parse(details)
                updated_key = key
                arr = []

                if 'EquipOrder' in key:
                    updated_key = 'EquipmentOrder'
                    details = create_array_of_arrays(details)
                elif 'EquipQTY' in key:
                    updated_key = 'EquipmentQuantity'
                    details = create_array_of_arrays(details)
                elif 'AnvilPA_' in key:
                    updated_key = 'AnvilPA'
                    updated_details = create_array_of_arrays(details)
                elif 'EMm0' in key:
                    updated_key = 'EquipmentMap'
                    arr = character_details.get(updated_key, [])
                    det = create_indexed_array(updated_details)
                    arr.insert(0, det)
                elif 'IMm_' in key:
                    updated_key = 'InventoryMap'
                    updated_details = try_to_parse(details)
                elif 'EMm1' in key:
                    updated_key = 'EquipmentMap'
                    arr = character_details.get(updated_key, [])
                    det = create_indexed_array(updated_details)
                    arr.insert(1, det)
                elif 'BuffsActive' in key:
                    updated_key = 'BuffsActive'
                    arr = create_array_of_arrays(updated_details)
                elif 'ItemQTY' in key:
                    updated_key = 'ItemQuantity'
                elif 'PVStatList' in key:
                    updated_key = 'PersonalValuesMap'
                    updated_details = {**character_details.get(updated_key, {}), 'StatList': try_to_parse(details)}
                elif 'PVtStarSign' in key:
                    updated_key = 'PersonalValuesMap'
                    updated_details = {**character_details.get(updated_key, {}), 'StarSign': try_to_parse(details)}
                elif 'ObolEqO0' in key:
                    updated_key = 'ObolEquippedOrder'
                elif 'ObolEqMAP' in key:
                    updated_key = 'ObolEquippedMap'
                elif 'SL_' in key:
                    updated_key = 'SkillLevels'
                elif 'SLpre_' in key:
                    updated_key = 'SkillPreset'
                elif 'SM_' in key:
                    updated_key = 'SkillLevelsMAX'
                elif 'KLA_' in key:
                    updated_key = 'KillsLeft2Advance'
                elif 'AtkCD_' in key:
                    updated_key = 'AttackCooldowns'
                elif 'POu_' in key:
                    updated_key = 'PostOfficeInfo'
                elif 'PTimeAway' in key:
                    updated_key = 'PlayerAwayTime'
                    updated_details = updated_details * 1e3
                else:
                    updated_key = key.split('_')[0]

                character_details[updated_key] = arr if arr else updated_details

        characters.append({
            'name': char_name,
            'player_id': player_id,
            **character_details
        })

    return characters

def get_charactersData(serialized_characters_data):
    characters = {}
    for char in serialized_characters_data:
        char_name = char.get('name', f"Player{char.get('playerId', 'Unknown')}")
        characters[char_name] = {
            'afkTime': calculate_afk_time(char.get('PlayerAwayTime', 0)),
            'afkTarget': const_monsters.get(char.get('AFKtarget', {})).get('Name', ''),
            'afkType': const_monsters.get(char.get('AFKtarget', {})).get('AFKtype', '')
        }
    return characters

def calculate_afk_time(player_time):
    return float(player_time) * 1e3

def get_eggs(idleonData):
    breedingRaw = idleonData.get('Breeding') or try_to_parse(idleonData.get('Breeding'))
    eggs = breedingRaw[0] if breedingRaw is not None else None
    return eggs

def get_salts(idleonData, storage_data):
    refinery_raw = try_to_parse(idleonData.get('Refinery')) or idleonData.get('Refinery')
    salts=parse_refinery(refinery_raw, storage_data)
    return salts

def get_liquids(idleonData):
    alchemy_raw = create_array_of_arrays(idleonData.get('CauldronInfo')) or idleonData.get('CauldronInfo')
    liquidsList = alchemy_raw[6] if alchemy_raw and len(alchemy_raw) > 6 else None
    liquidName = ['water_droplets', 'liquid_nitrogen', 'trench_seawater', 'toxic_mercury']
    liquids = dict(zip(liquidName, liquidsList))
    return liquids

def get_plot(idleonData):
# raw_farming_plot 和 raw_farming_ranks 是解析后的数据
    raw_farming_plot = try_to_parse(idleonData.get('FarmPlot'))
    raw_farming_ranks = try_to_parse(idleonData.get('FarmRank'))
    farming_ranks, ranks_progress, upgrades_levels = raw_farming_ranks or ([], [], [])
    # 确保 raw_farming_plot 是一个列表，并且每个元素是一个包含7个元素的列表
    plot = []
    for index, item in enumerate(raw_farming_plot or []):
        if index < len(farming_ranks) and index < len(ranks_progress):
            seed_type, progress, crop_type, is_locked, crop_quantity, current_og, crop_progress = item
            rank = farming_ranks[index]
            rank_progress = ranks_progress[index]
            
            # 使用种子类型作为索引访问 const_seed_info 列表
            seed_info = const_seedInfo[seed_type] if seed_type < len(const_seedInfo) else {}
            type_value = round(seed_info.get('cropIdMin', 0) + crop_type)
            
            rank_requirement = (7 * rank + 25 * (rank // 5) + 10) * math.pow(1.11, rank)
            growth_req = 14400 * math.pow(1.5, seed_type)
            
            plot.append({
                'rank': rank,
                'rankProgress': rank_progress,
                'rankRequirement': rank_requirement,
                'seedType': seed_type,
                'cropType': type_value,
                'cropQuantity': crop_quantity,
                'cropProgress': crop_progress,
                'progress': progress,
                'growthReq': growth_req,
                'isLocked': is_locked,
                'currentOG': current_og,
                'cropRawName': f'FarmCrop{type_value}.png',
                'seedRawName': f'Seed_{seed_type}.png'
            })
    return plot

def get_jade_coins(idleonData):
    raw_sneaking = try_to_parse(idleonData.get('Ninja', None))
    if isinstance(raw_sneaking, list) and len(raw_sneaking) > 102:
        # 获取索引为 102 的元素
        ninja_data = raw_sneaking[102]
        # 获取索引为 1 的值（
        jade_coins = ninja_data[1]
    else:
        jade_coins = None
    return jade_coins