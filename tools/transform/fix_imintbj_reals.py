# -*- coding: utf-8 -*-
p = 'src/war3map.j'
t = open(p, encoding='utf-8').read()
fixes = [
    ("GetPrdRandom(ZX7,'A19Q',IMinBJ(d*imbaMult,100))",
     "GetPrdRandom(ZX7,'A19Q',IMinBJ(R2I(d)*imbaMult,100))"),
    ("GetPrdRandom(ZX7 , 'I0TE' , IMinBJ(rate*imbaMult,100))",
     "GetPrdRandom(ZX7 , 'I0TE' , IMinBJ(R2I(rate)*imbaMult,100))"),
    ("GetPrdRandom(ZX7 , 'I0A3' , IMinBJ(rate*imbaMult,100))",
     "GetPrdRandom(ZX7 , 'I0A3' , IMinBJ(R2I(rate)*imbaMult,100))"),
]
for old, new in fixes:
    c = t.count(old)
    print(f'{c}x: {old[:70]}')
    assert c == 1, f'expected 1, got {c}'
    t = t.replace(old, new)
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('Fixed.')
