import json, urllib.request, datetime, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

API="https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura"
ELEICAO="20322002026"
UFS=["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]
CARGOS={"1":"Presidente","2":"Vice-Presidente","3":"Governador","4":"Vice-Governador","5":"Senador","9":"1º Suplente de Senador","10":"2º Suplente de Senador","6":"Deputado Federal","7":"Deputado Estadual","8":"Deputado Distrital"}
OUT=Path("data"); OUT.mkdir(exist_ok=True)

def get(url, tentativas=2):
    last=None
    for n in range(tentativas):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 PainelEleicoes2026","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=18) as r: return json.load(r)
        except Exception as e:
            last=e; time.sleep(.4+n*.6)
    raise last

def foto_detalhe(scope, cid):
    try:
        d=get(f"{API}/buscar/2026/{scope}/{ELEICAO}/candidato/{cid}",1)
        return d.get("fotoUrl") or d.get("urlFoto") or d.get("foto")
    except Exception:
        return None

def gerar(scope,cargo):
    try: raw=get(f"{API}/listar/2026/{scope}/{ELEICAO}/{cargo}/candidatos")
    except Exception as e:
        print("AVISO",scope,cargo,e,flush=True); return False
    arr=[]
    for x in raw.get("candidatos",[]):
        p=x.get("partido") or {}; cg=x.get("cargo") or {}
        arr.append({"id":x.get("id"),"nome":x.get("nomeUrna") or x.get("nomeCompleto") or "Sem nome","numero":str(x.get("numero","—")),"partido":p.get("sigla",""),"federacao":p.get("nome",""),"situacao":x.get("descricaoSituacao") or x.get("descricaoTotalizacao") or "","cargo":cg.get("nome") or CARGOS[cargo],"foto":x.get("fotoUrl") or x.get("urlFoto") or x.get("foto")})
    faltam=[c for c in arr if not c["foto"] and c.get("id")]
    if faltam:
        print(f"  fotos: buscando {len(faltam)} em paralelo",flush=True)
        with ThreadPoolExecutor(max_workers=24) as ex:
            jobs={ex.submit(foto_detalhe,scope,c["id"]):c for c in faltam}
            for f in as_completed(jobs):
                foto=f.result()
                if foto: jobs[f]["foto"]=foto
    payload={"fonte":"TSE - DivulgaCandContas","atualizado":datetime.datetime.now(datetime.timezone.utc).isoformat(),"scope":scope,"cargo":cargo,"candidatos":arr}
    (OUT/f"{scope}_{cargo}.json").write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    fotos=sum(bool(c["foto"]) for c in arr)
    print("OK",scope,cargo,len(arr),"fotos",fotos,flush=True); return True

tarefas=[("BR","1"),("BR","2")]
for uf in UFS: tarefas += [(uf,c) for c in ("3","4","5","9","10","6","7")]
tarefas.append(("DF","8"))
ok=0
for i,(scope,cargo) in enumerate(tarefas,1):
    print(f"[{i}/{len(tarefas)}] {scope} {CARGOS[cargo]}",flush=True)
    ok += bool(gerar(scope,cargo))
print(f"FINAL {ok}/{len(tarefas)}",flush=True)
