import json, urllib.request, datetime, time
from pathlib import Path

API="https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura"
ELEICAO="20322002026"
UFS=["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]
CARGOS={"1":"Presidente","2":"Vice-Presidente","3":"Governador","4":"Vice-Governador","5":"Senador","9":"1º Suplente de Senador","10":"2º Suplente de Senador","6":"Deputado Federal","7":"Deputado Estadual","8":"Deputado Distrital"}
OUT=Path("data"); OUT.mkdir(exist_ok=True)

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 PainelEleicoes2026/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=40) as r: return json.load(r)

def foto_detalhe(scope,id):
    try:
        d=get(f"{API}/buscar/2026/{scope}/{ELEICAO}/candidato/{id}")
        return d.get("fotoUrl") or d.get("urlFoto") or d.get("foto") or (d.get("candidato") or {}).get("fotoUrl")
    except Exception: return None

def gerar(scope,cargo):
    url=f"{API}/listar/2026/{scope}/{ELEICAO}/{cargo}/candidatos"
    try: raw=get(url)
    except Exception as e:
        print("ERRO",scope,cargo,e); return
    arr=[]
    for x in raw.get("candidatos",[]):
        p=x.get("partido") or {}; cg=x.get("cargo") or {}
        c={"id":x.get("id"),"nome":x.get("nomeUrna") or x.get("nomeCompleto") or "Sem nome","numero":str(x.get("numero","—")),"partido":p.get("sigla",""),"federacao":p.get("nome",""),"situacao":x.get("descricaoSituacao") or x.get("descricaoTotalizacao") or "","cargo":cg.get("nome") or CARGOS[cargo],"foto":x.get("fotoUrl")}
        # Detalhe só quando a listagem não trouxer a foto.
        if not c["foto"] and c["id"]:
            c["foto"]=foto_detalhe(scope,c["id"]); time.sleep(.03)
        arr.append(c)
    payload={"fonte":"TSE - DivulgaCandContas","atualizado":datetime.datetime.now(datetime.timezone.utc).isoformat(),"scope":scope,"cargo":cargo,"candidatos":arr}
    (OUT/f"{scope}_{cargo}.json").write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print(scope,cargo,len(arr))

# Nacional
for c in ("1","2"): gerar("BR",c)
# Estaduais
for u in UFS:
    for c in ("3","4","5","9","10","6","7"):
        gerar(u,c)
    if u=="DF": gerar(u,"8")
