import base64, json, subprocess, sys, urllib.request, urllib.error
WS="eb299f2a-40d2-41a1-9a91-7f27e891d01f"; MODEL="ca7988b3-bc2a-4d5d-859a-4700dab72fb1"
SC="https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"
files={}
def put(p,o): files[p]=json.dumps(o,ensure_ascii=False,indent=1)
put("definition.pbir",{"version":"4.0","datasetReference":{"byConnection":{"connectionString":None,"pbiServiceModelId":None,"pbiModelVirtualServerName":"sobe_wowvirtualserver","pbiModelDatabaseName":MODEL,"name":"EntityDataSource","connectionType":"pbiServiceXmlaStyleLive"}}})
put("definition/version.json",{"$schema":SC+"versionMetadata/1.0.0/schema.json","version":"2.0.0"})
put("definition/report.json",{"$schema":SC+"report/1.0.0/schema.json","themeCollection":{"baseTheme":{"name":"CY24SU10","reportVersionAtImport":"5.61","type":"SharedResources"}},"layoutOptimization":"None"})
put("definition/pages/pages.json",{"$schema":SC+"pagesMetadata/1.0.0/schema.json","pageOrder":["resumen"],"activePageName":"resumen"})
put("definition/pages/resumen/page.json",{"$schema":SC+"page/1.0.0/schema.json","name":"resumen","displayName":"Resumen ejecutivo","displayOption":"FitToPage","height":720,"width":1280})
def col(e,p): return {"Column":{"Expression":{"SourceRef":{"Entity":e}},"Property":p}}
def mea(e,p): return {"Measure":{"Expression":{"SourceRef":{"Entity":e}},"Property":p}}
def proj(f,e,p): return {"field":f,"queryRef":f"{e}.{p}","nativeQueryRef":p}
n=[0]
def visual(vtype,x,y,w,h,state,title=None,objects=None,sort=None):
    n[0]+=1; name=f"v{n[0]:02d}"
    v={"visualType":vtype,"query":{"queryState":state},"drillFilterOtherVisuals":True}
    if sort: v["query"]["sortDefinition"]={"sort":[{"field":sort,"direction":"Descending"}]}
    if objects: v["objects"]=objects
    if title: v["visualContainerObjects"]={"title":[{"properties":{"show":{"expr":{"Literal":{"Value":"true"}}},"text":{"expr":{"Literal":{"Value":f"'{title}'"}}}}}]}
    put(f"definition/pages/resumen/visuals/{name}/visual.json",{"$schema":SC+"visualContainer/1.0.0/schema.json","name":name,"position":{"x":x,"y":y,"z":n[0],"height":h,"width":w},"visual":v})
M=lambda p:("fact_ventas",p)
# fila de KPIs
kpis=[("fact_ventas","Ventas"),("fact_ventas","Pedidos"),("fact_ventas","Ticket Medio"),("fact_ventas","% Entrega a Tiempo"),("fact_resenas","Score Promedio")]
L=lambda v:{"expr":{"Literal":{"Value":v}}}
for i,(e,p) in enumerate(kpis):
    obj={"labels":[{"properties":{"fontSize":L("26D")}}]}
    if p=="Ventas": obj["labels"][0]["properties"].update({"labelDisplayUnits":L("1000000D"),"labelPrecision":L("1L")})
    if p=="Pedidos": obj["labels"][0]["properties"].update({"labelDisplayUnits":L("1000D"),"labelPrecision":L("1L")})
    visual("card",20+i*250,70,230,120,{"Values":{"projections":[proj(mea(e,p),e,p)]}},p,objects=obj)
# slicer de anio
visual("slicer",1280-20-190,10,190,50,{"Values":{"projections":[proj(col("dim_fecha","anio"),"dim_fecha","anio")]}})
# ventas por mes y anio
visual("lineChart",20,210,620,240,{"Category":{"projections":[proj(col("dim_fecha","nombre_mes"),"dim_fecha","nombre_mes")]},
  "Series":{"projections":[proj(col("dim_fecha","anio"),"dim_fecha","anio")]},"Y":{"projections":[proj(mea("fact_ventas","Ventas"),"fact_ventas","Ventas")]}},"Ventas por mes y año")
# ventas por categoria
visual("barChart",660,210,600,240,{"Category":{"projections":[proj(col("dim_producto","categoria"),"dim_producto","categoria")]},
  "Y":{"projections":[proj(mea("fact_ventas","Ventas"),"fact_ventas","Ventas")]}},"Ventas por categoría",sort=mea("fact_ventas","Ventas"))
# entrega a tiempo por estado
visual("columnChart",20,465,620,240,{"Category":{"projections":[proj(col("dim_cliente","estado"),"dim_cliente","estado")]},
  "Y":{"projections":[proj(mea("fact_ventas","% Entrega a Tiempo"),"fact_ventas","% Entrega a Tiempo")]}},"% de entregas a tiempo por estado")
# score por estado del pedido
visual("columnChart",660,465,600,240,{"Category":{"projections":[proj(col("dim_pedido","estado_pedido"),"dim_pedido","estado_pedido")]},
  "Y":{"projections":[proj(mea("fact_resenas","Score Promedio"),"fact_resenas","Score Promedio")]}},"Puntuación promedio por estado del pedido")
out=sys.argv[1]
import os
for p,c in files.items():
    fp=os.path.join(out,p); os.makedirs(os.path.dirname(fp),exist_ok=True); open(fp,"w",encoding="utf-8").write(c)
print("archivos",len(files))
tok=subprocess.run("az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv",shell=True,capture_output=True,text=True).stdout.strip()
parts=[{"path":p,"payload":base64.b64encode(c.encode("utf-8")).decode(),"payloadType":"InlineBase64"} for p,c in files.items()]
RID="4566bacc-6cac-4365-9a2c-4aa6f6f0542e"
body=json.dumps({"definition":{"parts":parts}}).encode()
r=urllib.request.Request(f"https://api.fabric.microsoft.com/v1/workspaces/{WS}/reports/{RID}/updateDefinition",data=body,method="POST",headers={"Authorization":"Bearer "+tok,"Content-Type":"application/json"})
try: x=urllib.request.urlopen(r); print(x.status,x.headers.get("Location"))
except urllib.error.HTTPError as e: print("ERR",e.code,e.read().decode()[:1200])
