from pathlib import Path
import re,csv
ROOT=Path(r'D:\dota\DOTA-OMG-IMBA-轻量化')
src=Path(r'D:\dota\runtime-map-full\units\campaignabilitystrings.txt')
out=ROOT/'src'/'data'/'Units'/'CampaignAbilityStrings.txt'
s=src.read_text(encoding='utf-8')
prob_ids={'A088','A0JJ','A081','A09E','A0WR','A061','A0C6','A2KU','A263','A264','A2QG','A03Y','A4L7','A2RA','A2PX','A00K','A1OY','ABcr','A03Q','A03N','A19Q','A2EY','A4HE'}
bounce_ids={'A004','A10D'}
changes=[]

def fmt(v):
    x=float(v)*2
    return str(int(x)) if x.is_integer() else ('%.2f'%x).rstrip('0').rstrip('.')

def transform_text(uid,text):
    old=text
    # Direct damage/healing values only; never touch distance/range/cooldown/mana labels.
    pats=[
      (r'(\d+(?:\.\d+)?)(点(?:的)?(?:额外)?伤害|点伤害)',lambda m:fmt(m.group(1))+m.group(2)),
      (r'(每秒)(\d+(?:\.\d+)?)(伤害)',lambda m:m.group(1)+fmt(m.group(2))+m.group(3)),
      (r'(治疗(?:量|效果)?(?:为|：)?)(\d+(?:\.\d+)?)',lambda m:m.group(1)+fmt(m.group(2))),
      (r'(恢复)(\d+(?:\.\d+)?)(点生命)',lambda m:m.group(1)+fmt(m.group(2))+m.group(3)),
    ]
    for pat,fn in pats:
        text=re.sub(pat,fn,text)
    if uid in prob_ids and uid!='A088':
        text=re.sub(r'(\d+(?:\.\d+)?)%((?:的)?概率)',lambda m:str(min(100,float(m.group(1))*2)).rstrip('0').rstrip('.')+'%'+m.group(2),text)
    if uid in bounce_ids:
        text=text.replace('弹射三次','弹射六次')
    # Exact reviewed multicast text: write each level's actual probability/count text explicitly.
    if uid=='A088':
        text=text.replace('40%(50%)概率施法两次','80%(100%)概率施法四次')
        text=text.replace('50%(60%)概率施法两次，25%(30%)概率施法三次','100%(100%)概率施法四次，50%(60%)概率施法六次')
        text=text.replace('60%(80%)概率施法两次，30%(40%)概率施法三次，15%(20%)概率施法四次','100%(100%)概率施法四次，60%(80%)概率施法六次，30%(40%)概率施法六次')
        text=text.replace('40%(50%)概率连续施法两次','80%(100%)概率连续施法四次')
        text=text.replace('50%(60%)概率连续施法两次；25%(30%)概率连续施法三次','100%(100%)概率连续施法四次；50%(60%)概率连续施法六次')
        text=text.replace('60%(80%)概率连续施法两次；30%(40%)概率连续施法三次；15%(20%)概率连续施法四次','100%(100%)概率连续施法四次；60%(80%)概率连续施法六次；30%(40%)概率连续施法六次')
        text=text.replace('有5%概率连续施法五次','有10%概率连续施法六次')
    if text!=old and '|cFF66CCFF[IMBA实际值]|r' not in text:
        text='|cFF66CCFF[IMBA实际值]|r '+text
    return text

parts=re.split(r'(?m)(?=^\[[^\r\n]+\]\r?$)',s)
out_parts=[]
for block in parts:
    m=re.match(r'^\[([^\]]+)\]',block)
    if not m:
        out_parts.append(block);continue
    uid=m.group(1)
    lines=block.splitlines(keepends=True)
    for i,line in enumerate(lines):
        stripped=line.rstrip('\r\n')
        eol=line[len(stripped):]
        if stripped.startswith('Researchubertip=') or stripped.startswith('Ubertip='):
            key,val=stripped.split('=',1)
            nv=transform_text(uid,val)
            if uid=='A0SK':
                nv=nv.replace('8秒内不能通行','16秒内不能通行')
                nv=nv.replace('造成110伤害，1秒眩晕','造成220伤害，2秒眩晕')
                nv=nv.replace('造成160伤害，1.25秒眩晕','造成320伤害，2.5秒眩晕')
                nv=nv.replace('造成210伤害，1.5秒眩晕','造成420伤害，3秒眩晕')
                nv=nv.replace('造成260伤害，1.75秒眩晕','造成520伤害，3.5秒眩晕')
                nv=nv.replace('晕眩1秒','晕眩2秒').replace('晕眩1.25秒','晕眩2.5秒').replace('晕眩1.5秒','晕眩3秒').replace('晕眩1.75秒','晕眩3.5秒')
                if nv!=val and '|cFF66CCFF[IMBA实际值]|r' not in nv:
                    nv='|cFF66CCFF[IMBA实际值]|r '+nv
            if nv!=val:
                changes.append((uid,key,val[:160],nv[:160]))
                lines[i]=key+'='+nv+eol
    out_parts.append(''.join(lines))
result=''.join(out_parts)
out.write_text(result,encoding='utf-8',newline='\r\n')
report=ROOT/'reports'/'IMBA-UI同步-v1.1.csv'
with report.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['rawcode','字段','原文本片段','新文本片段']);w.writerows(changes)
print('written',out,out.stat().st_size,'changed_fields',len(changes),'skills',len(set(x[0] for x in changes)))
print('report',report)
for uid in ['A0SK','A088','A004','A10D']:
 a=result.find('['+uid+']');b=result.find('\n[',a+1);block=result[a:b]
 print('\n###',uid)
 for ln in block.splitlines():
  if ln.startswith('Ubertip='): print(ln[:1200])