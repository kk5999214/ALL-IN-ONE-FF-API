import base64
import binascii
import json
import time
import httpx
from fastapi import FastAPI, Query, Form, HTTPException
from fastapi.responses import JSONResponse
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

import info_data_pb2
import uid_generator_pb2
import nick_data_pb2
import PlayerStats_pb2
import PlayerCSStats_pb2
from google.protobuf.json_format import MessageToDict

from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

_sym_db = _symbol_database.Default()
BIO_PROTO = b'\n\nbio_.proto\"\xbb\x01\n\x04\x44\x61ta\x12\x0f\n\x07\x66ield_2\x18\x02 \x01(\x05\x12\x1e\n\x07\x66ield_5\x18\x05 \x01(\x0b\x32\r.EmptyMessage\x12\x1e\n\x07\x66ield_6\x18\x06 \x01(\x0b\x32\r.EmptyMessage\x12\x0f\n\x07\x66ield_8\x18\x08 \x01(\t\x12\x0f\n\x07\x66ield_9\x18\t \x01(\x05\x12\x1f\n\x08\x66ield_11\x18\x0b \x01(\x0b\x32\r.EmptyMessage\x12\x1f\n\x08\x66ield_12\x18\x0c \x01(\x0b\x32\r.EmptyMessage\"\x0e\n\x0c\x45mptyMessageb\x06proto3'
_builder.BuildMessageAndEnumDescriptors(_descriptor_pool.Default().AddSerializedFile(BIO_PROTO), globals())
_builder.BuildTopDescriptorsAndMessages(_descriptor_pool.Default().AddSerializedFile(BIO_PROTO), 'bio_pb2', globals())
BioData = _sym_db.GetSymbol('Data')
EmptyMessage = _sym_db.GetSymbol('EmptyMessage')

app = FastAPI(title="BITTU__DEV Master API", version="6.0")

SECRET_KEY = b'Yg&tc%DEuh6%Zc^8'
SECRET_IV = b'6oyZDr22E3ychjM%'
GAME_VERSION = "OB53"
UNITY_VERSION = "2018.4.11f1"
USER_AGENT = "Dalvik/2.1.0 (Linux; U; Android 15; I2404 Build/AP3A.240905.015.A2_V000L1)"
DEVELOPER = "@BITTU__DEV"

JWT_API_BASE = "https://jwt-generator-da4784782bce.herokuapp.com" 
TOKEN_CACHE = {}

async def Get_Cached_JWT(Region: str) -> str:
    Reg = Region.upper()
    Current_Time = time.time()
    
    if Reg in TOKEN_CACHE:
        if Current_Time < TOKEN_CACHE[Reg]["expires"]:
            return TOKEN_CACHE[Reg]["token"]
            
    async with httpx.AsyncClient(verify=False) as Client:
        Res = await Client.get(f"{JWT_API_BASE}/api/token?reg={Reg}", timeout=20.0)
        Res.raise_for_status()
        Data = Res.json()
        New_Jwt = Data.get("token")
        
        if not New_Jwt:
            raise HTTPException(status_code=500, detail=f"JWT Factory Failed To Provide Token For {Reg} 💀")
            
        TOKEN_CACHE[Reg] = {
            "token": New_Jwt,
            "expires": Current_Time + 7000
        }
        return New_Jwt

def Get_Server_Url(Region: str, Action: str) -> str:
    Reg = Region.upper()
    Bluefox_Regions = ["ME", "TH"]
    Blueshark_Regions = ["GHOST", "BD", "SG"]
    US_Regions = ["BR", "US", "SAC"]
    
    if Action == "Info" or Action == "Stats":
        if Reg == "IND": return "https://client.ind.freefiremobile.com"
        if Reg in Bluefox_Regions: return "https://clientbp.common.ggbluefox.com"
        if Reg in Blueshark_Regions: return "https://clientbp.ggblueshark.com"
        return "https://clientbp.ggpolarbear.com"
        
    if Action == "Bio":
        if Reg == "IND": return "https://client.ind.freefiremobile.com/UpdateSocialBasicInfo"
        if Reg in US_Regions: return "https://client.us.freefiremobile.com/UpdateSocialBasicInfo"
        if Reg in Blueshark_Regions: return "https://clientbp.ggblueshark.com/UpdateSocialBasicInfo"
        return "https://clientbp.ggpolarbear.com/UpdateSocialBasicInfo"
        
    if Action == "Nickname":
        return "https://loginbp.ggpolarbear.com/MajorModifyNickname"
        
    return "https://clientbp.ggpolarbear.com"

def Encrypt_Data(Hex_Data: str) -> str:
    Cipher = AES.new(SECRET_KEY, AES.MODE_CBC, SECRET_IV)
    Padded_Data = pad(bytes.fromhex(Hex_Data), AES.block_size)
    Encrypted = Cipher.encrypt(Padded_Data)
    return binascii.hexlify(Encrypted).decode()

@app.get("/")
async def Root_Status():
    return JSONResponse(content={
        "System": "BITTU__DEV Master API Online 💀🚀",
        "Modules_Active": ["Info", "Bio", "Nickname", "Stats"],
        "Architecture": "FastAPI Load Balancer With Smart Cache 👑"
    })

@app.get("/api/info")
async def Get_Info(uid: str = Query(...), region: str = Query("IND"), jwt: str = Query(None)):
    Reg = region.upper()
    
    Active_JWT = jwt if jwt else await Get_Cached_JWT(Reg)
    
    Message = uid_generator_pb2.uid_generator()
    Message.saturn_ = int(uid)
    Message.garena = 1
    Encrypted_Hex = Encrypt_Data(binascii.hexlify(Message.SerializeToString()).decode())
    
    Headers = {
        'User-Agent': USER_AGENT,
        'Authorization': f'Bearer {Active_JWT}',
        'X-Unity-Version': UNITY_VERSION,
        'X-GA': 'v1 1',
        'ReleaseVersion': GAME_VERSION,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    Endpoint = f"{Get_Server_Url(Reg, 'Info')}/GetPlayerPersonalShow"
    
    try:
        async with httpx.AsyncClient(verify=False) as Client:
            Res = await Client.post(Endpoint, headers=Headers, content=bytes.fromhex(Encrypted_Hex))
            Res.raise_for_status() 
    except Exception as e:
        err_str = str(e).lower()
        if "401" in err_str or "unauthorized" in err_str:
            TOKEN_CACHE.pop(Reg, None) 
            raise HTTPException(status_code=401, detail="Token Expired Cache Flushed Try Again ♻️")
        raise HTTPException(status_code=500, detail=f"Garena Server Error {e}")
        
    Acc_Info = info_data_pb2.AccountPersonalShowInfo()
    Acc_Info.ParseFromString(Res.content)
    
    return JSONResponse(content={
        "Developer": DEVELOPER,
        "Status": "Success 🔥",
        "Data": MessageToDict(Acc_Info)
    })

@app.get("/api/stats")
async def Get_Stats(uid: str = Query(...), region: str = Query("IND"), jwt: str = Query(None)):
    Reg = region.upper()
    
    Active_JWT = jwt if jwt else await Get_Cached_JWT(Reg)
    
    Message = PlayerStats_pb2.request()
    Message.accountid = int(uid)
    Message.matchmode = 0
    Encrypted_Hex = Encrypt_Data(binascii.hexlify(Message.SerializeToString()).decode())
    
    Headers = {
        'User-Agent': USER_AGENT,
        'Authorization': f'Bearer {Active_JWT}',
        'X-Unity-Version': UNITY_VERSION,
        'X-GA': 'v1 1',
        'ReleaseVersion': GAME_VERSION,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    Endpoint = f"{Get_Server_Url(Reg, 'Stats')}/GetPlayerStatsShow"
    
    try:
        async with httpx.AsyncClient(verify=False) as Client:
            Res = await Client.post(Endpoint, headers=Headers, content=bytes.fromhex(Encrypted_Hex))
            Res.raise_for_status()
    except Exception as e:
        err_str = str(e).lower()
        if "401" in err_str or "unauthorized" in err_str:
            TOKEN_CACHE.pop(Reg, None)
            raise HTTPException(status_code=401, detail="Token Expired Cache Flushed Try Again ♻️")
        raise HTTPException(status_code=500, detail=f"Garena Server Error {e}")
        
    return JSONResponse(content={
        "Developer": DEVELOPER,
        "Status": "Stats Pulled 📊",
        "Http_Code": Res.status_code
    })

@app.post("/api/bio")
async def Update_Bio(bio: str = Form(...), region: str = Form("IND"), jwt: str = Form(...)):
    Reg = region.upper()
    
    try:
        Data = BioData()
        Data.field_2 = 17
        Data.field_5.CopyFrom(EmptyMessage())
        Data.field_6.CopyFrom(EmptyMessage())
        Data.field_8 = bio
        Data.field_9 = 1
        Data.field_11.CopyFrom(EmptyMessage())
        Data.field_12.CopyFrom(EmptyMessage())
        
        Encrypted_Payload = Encrypt_Data(binascii.hexlify(Data.SerializeToString()).decode())
        
        Headers = {
            'User-Agent': USER_AGENT,
            'Authorization': f'Bearer {jwt}',
            'X-Unity-Version': UNITY_VERSION,
            'X-GA': 'v1 1',
            'ReleaseVersion': GAME_VERSION,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        async with httpx.AsyncClient(verify=False) as Client:
            Res = await Client.post(Get_Server_Url(Reg, "Bio"), headers=Headers, content=bytes.fromhex(Encrypted_Payload))
            
        return JSONResponse(content={
            "Developer": DEVELOPER,
            "Status": "Bio Injected Successfully 💎",
            "Injected_Text": bio,
            "Http_Code": Res.status_code
        })
    except Exception as E:
        raise HTTPException(status_code=500, detail=str(E))

@app.post("/api/nickname")
async def Change_Nickname(new_name: str = Form(...), jwt: str = Form(...)):
    Message = nick_data_pb2.Message()
    Message.data = new_name.encode("utf-8")
    Message.timestamp = int(time.time() * 1000)
    
    Encrypted_Hex = Encrypt_Data(binascii.hexlify(Message.SerializeToString()).decode())
    
    Headers = {
        'User-Agent': USER_AGENT,
        'Authorization': f'Bearer {jwt}',
        'X-Unity-Version': UNITY_VERSION,
        'X-GA': 'v1 1',
        'ReleaseVersion': GAME_VERSION,
        'Content-Type': 'application/octet-stream'
    }
    
    async with httpx.AsyncClient(verify=False) as Client:
        Res = await Client.post(Get_Server_Url("IND", "Nickname"), headers=Headers, content=bytes.fromhex(Encrypted_Hex))
        
    return JSONResponse(content={
        "Developer": DEVELOPER,
        "Status": "Nickname Altered 🎭",
        "Target_Name": new_name,
        "Http_Code": Res.status_code
    })
