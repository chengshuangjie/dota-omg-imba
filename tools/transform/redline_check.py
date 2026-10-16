# -*- coding: utf-8 -*-
t = open('src/war3map.j', encoding='utf-8').read()
lines = t.splitlines()
issues = []
for i in range(len(lines)):
    if ('imbaMult' in lines[i] or 'IMBA_POWER' in lines[i]) and ('CreateUnit' in lines[i] or 'UnitApplyTimedLife' in lines[i] or 'ShuangXiongTime' in lines[i]):
        issues.append((i+1, lines[i].strip()[:100]))
print('CreateUnit/TimedLife/ShuangXiongTime with imba:', len(issues))
for x in issues:
    print(' ', x)
print('Neutral drop 10%:', 'GetRandomInt(1, 10)!=1' in t or 'GetRandomInt(1,10)!=1' in t)
print('EXGetAbilityState(a,1):', 'EXGetAbilityState(a,1)' in t)
print('MANA_COST const:', 'ABILITY_LEVEL_DEF_DATA_MANA_COST' in t)
print('GOLD count:', t.count('PLAYER_STATE_RESOURCE_GOLD'))
print('CJ1 formula:', 'CJ1=5+CGDIFF*2' in t or 'CJ1 = 5+CGDIFF*2' in t)
print('IMBA_POWER const:', 'constant real IMBA_POWER=2.' in t)
print('BL7!=6 guard:', 'BL7!=6' in t)
print('CommonUnitAddStun 5s cap:', 'RMinBJ(dur*IMBA_POWER,5.)' in t)
# Check summon counts unchanged
print('familiarCount1052=2:', 'local integer familiarCount1052=2' in t)
print('familiarCount1052=3:', 'set familiarCount1052=3' in t)
# Check ATD ShuangXiongTime unchanged
print('ShuangXiongTime(AQD,DUR):', 'call ShuangXiongTime(AQD,DUR)' in t)
print('TimerStart(tt,DUR+4:', 'call TimerStart(tt,DUR+4,false,function ASD2)' in t)
