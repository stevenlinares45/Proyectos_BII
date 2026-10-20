import json, struct, subprocess, sys, urllib.request, pyodbc
WS="eb299f2a-40d2-41a1-9a91-7f27e891d01f"; WH="01fd14b4-d8c4-4bf5-a7bb-e8f2506c6759"
def az(res): return subprocess.run(f"az account get-access-token --resource {res} --query accessToken -o tsv",shell=True,capture_output=True,text=True).stdout.strip()
ftok=az("https://api.fabric.microsoft.com")
r=urllib.request.Request(f"https://api.fabric.microsoft.com/v1/workspaces/{WS}/warehouses/{WH}",headers={"Authorization":"Bearer "+ftok})
server=json.load(urllib.request.urlopen(r))["properties"]["connectionString"]
tok=az("https://database.windows.net/").encode("utf-16-le")
attrs={1256: struct.pack(f"<I{len(tok)}s",len(tok),tok)}
def connect():
    return pyodbc.connect(f"Driver={{ODBC Driver 17 for SQL Server}};Server={server};Database=wh_olist;Encrypt=yes",attrs_before=attrs,autocommit=True)
def run(batches, show=True):
    c=connect(); cur=c.cursor()
    for b in batches:
        b=b.strip()
        if not b: continue
        cur.execute(b)
        if cur.description:
            cols=[d[0] for d in cur.description]
            print(" | ".join(cols))
            for row in cur.fetchall(): print(" | ".join(str(x) for x in row))
        else: print("OK:", b.splitlines()[0][:80])
    c.close()
if __name__=="__main__":
    run(open(sys.argv[1],encoding="utf-8").read().split("\nGO\n"))
