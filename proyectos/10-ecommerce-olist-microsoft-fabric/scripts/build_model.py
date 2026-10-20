import json, uuid, sys, base64, subprocess, urllib.request, urllib.error
cols=json.load(open("cols.json"))
SERVER="a4mpytyfu7luhnj265gaddzry4-fkpst26sicqudgurp4t6reoqd4.datawarehouse.fabric.microsoft.com"
WH="01fd14b4-d8c4-4bf5-a7bb-e8f2506c6759"; WS="eb299f2a-40d2-41a1-9a91-7f27e891d01f"
T={"varchar":"string","int":"int64","float":"double","decimal":"decimal","bit":"boolean","date":"dateTime","datetime2":"dateTime"}
measures={
 "fact_ventas":[
  ("Ventas","SUM(fact_ventas[price])","#,0.00"),
  ("Flete","SUM(fact_ventas[freight_value])","#,0.00"),
  ("Pedidos","DISTINCTCOUNT(fact_ventas[order_id])","#,0"),
  ("Clientes unicos","COUNTROWS(SUMMARIZE(fact_ventas, dim_cliente[customer_unique_id]))","#,0"),
  ("Ticket Medio","DIVIDE([Ventas], [Pedidos])","#,0.00"),
  ("% Entrega a Tiempo","DIVIDE(CALCULATE(COUNTROWS(fact_ventas), fact_ventas[entrega_a_tiempo] = TRUE()), CALCULATE(COUNTROWS(fact_ventas), NOT ISBLANK(fact_ventas[entrega_a_tiempo])))","0.0%"),
  ("Dias Entrega Prom","AVERAGE(fact_ventas[dias_entrega])","0.0"),
  ("Ventas YTD","TOTALYTD([Ventas], dim_fecha[fecha])","#,0.00"),
  ("Ventas Anio Anterior","CALCULATE([Ventas], SAMEPERIODLASTYEAR(dim_fecha[fecha]))","#,0.00"),
  ("Crecimiento YoY","DIVIDE([Ventas] - [Ventas Anio Anterior], [Ventas Anio Anterior])","0.0%")],
 "fact_resenas":[("Score Promedio","AVERAGE(fact_resenas[puntuacion])","0.00"),("Resenas","COUNTROWS(fact_resenas)","#,0")],
 "fact_pagos":[("Valor Pagado","SUM(fact_pagos[valor_pago])","#,0.00")]}
tables=[]
for t,cs in cols.items():
    tb={"name":t,"columns":[],"partitions":[{"name":t,"mode":"directLake","source":{"type":"entity","entityName":t,"schemaName":"dwh","expressionSource":"DatabaseQuery"}}]}
    for c,dt in cs:
        col={"name":c,"dataType":T[dt],"sourceColumn":c,"summarizeBy":"none"}
        if dt=="date": col["formatString"]="Short Date"
        if t=="dim_fecha" and c=="fecha": col["isKey"]=True
        if t=="dim_fecha" and c=="nombre_mes": col["sortByColumn"]="mes"
        tb["columns"].append(col)
    if t=="dim_fecha": tb["dataCategory"]="Time"
    if t in measures: tb["measures"]=[{"name":n,"expression":e,"formatString":f} for n,e,f in measures[t]]
    tables.append(tb)
rel=lambda a,b,c,d:{"name":str(uuid.uuid4()),"fromTable":a,"fromColumn":b,"toTable":c,"toColumn":d}
model={"compatibilityLevel":1604,"model":{"culture":"en-US","defaultPowerBIDataSourceVersion":"powerBI_V3","discourageImplicitMeasures":True,
 "expressions":[{"name":"DatabaseQuery","kind":"m","expression":["let",f'    database = Sql.Database("{SERVER}", "{WH}")',"in","    database"]}],
 "tables":tables,
 "relationships":[rel("fact_ventas","fecha_key","dim_fecha","fecha_key"),rel("fact_ventas","customer_id","dim_cliente","customer_id"),
  rel("fact_ventas","product_id","dim_producto","product_id"),rel("fact_ventas","seller_id","dim_vendedor","seller_id"),
  rel("fact_ventas","order_id","dim_pedido","order_id"),rel("fact_pagos","order_id","dim_pedido","order_id"),rel("fact_resenas","order_id","dim_pedido","order_id")]}}
out=sys.argv[1]; json.dump(model,open(out+"/model.bim","w",encoding="utf-8"),ensure_ascii=False,indent=2)
json.dump({"version":"1.0","settings":{}},open(out+"/definition.pbism","w"))
print("tablas",len(tables),"relaciones",len(model["model"]["relationships"]))
