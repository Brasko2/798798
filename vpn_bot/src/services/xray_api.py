"""
Модуль для работы с API 3X-UI (XRay)
"""
import uuid
import json
import base64
import logging
import aiohttp
from typing import Dict, Any, List, Optional, Tuple

from ..exceptions import XRayAPIError
from ..settings import Settings


# Создаем экземпляр настроек
settings = Settings()


logger = logging.getLogger(__name__)


class XRayAPI:
    """Класс для работы с API 3X-UI"""
    
    def __init__(self,
                 host: str = None,
                 username: str = None,
                 password: str = None):
        self.host = host or settings.xui_api_url
        self.username = username or settings.xui_api_username
        self.password = password or settings.xui_api_password
        self._session = None
        self._token = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Возвращает сессию HTTP-клиента"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def _get_token(self) -> str:
        """Получает токен авторизации для API"""
        if self._token:
            return self._token
        
        session = await self._get_session()
        auth_url = f"{self.host}/login"
        
        try:
            async with session.post(
                auth_url,
                json={"username": self.username, "password": self.password}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Authentication failed: {error_text}")
                    raise XRayAPIError(
                        f"Authentication failed: {error_text}", 
                        status_code=response.status
                    )
                
                data = await response.json()
                self._token = data.get("token")
                if not self._token:
                    raise XRayAPIError("Authentication successful but token not found in response")
                
                return self._token
        except aiohttp.ClientError as e:
            logger.error(f"Connection error: {str(e)}")
            raise XRayAPIError(f"Connection error: {str(e)}")
    
    async def _make_request(self, method: str, endpoint: str, json_data: Dict = None) -> Dict:
        """Выполняет HTTP-запрос к API"""
        session = await self._get_session()
        url = f"{self.host}{endpoint}"
        token = await self._get_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with session.request(
                method,
                url,
                headers=headers,
                json=json_data
            ) as response:
                response_text = await response.text()
                
                if response.status != 200:
                    logger.error(f"API error: {response.status} - {response_text}")
                    raise XRayAPIError(
                        f"API error: {response_text}", 
                        status_code=response.status
                    )
                
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode JSON response: {response_text}")
                    return {"data": response_text}
        except aiohttp.ClientError as e:
            logger.error(f"Connection error: {str(e)}")
            raise XRayAPIError(f"Connection error: {str(e)}")
    
    async def get_inbounds(self) -> List[Dict[str, Any]]:
        """Получает список входящих соединений (inbounds)"""
        response = await self._make_request("GET", "/panel/api/inbounds/list")
        return response.get("obj", [])
    
    async def get_clients(self, inbound_id: int) -> List[Dict[str, Any]]:
        """Получает список клиентов для указанного inbound"""
        response = await self._make_request("GET", f"/panel/api/inbounds/{inbound_id}/get")
        inbound = response.get("obj", {})
        settings_data = inbound.get("settings", "{}")
        
        try:
            if isinstance(settings_data, str):
                settings = json.loads(settings_data)
            else:
                settings = settings_data
                
            clients = settings.get("clients", [])
            return clients
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse inbound settings: {e}")
            return []
    
    async def add_client(self, 
                        inbound_id: int, 
                        email: str, 
                        uuid_str: Optional[str] = None,
                        traffic_limit: Optional[int] = None) -> Dict[str, Any]:
        """Добавляет нового клиента к inbound"""
        # Если UUID не указан, генерируем новый
        if not uuid_str:
            uuid_str = str(uuid.uuid4())
        
        # Сначала получаем информацию о inbound
        response = await self._make_request("GET", f"/panel/api/inbounds/{inbound_id}/get")
        inbound = response.get("obj", {})
        
        # Получаем текущие настройки
        settings_data = inbound.get("settings", "{}")
        try:
            if isinstance(settings_data, str):
                settings = json.loads(settings_data)
            else:
                settings = settings_data
                
            # Создаем нового клиента
            new_client = {
                "id": uuid_str,
                "email": email
            }
            
            # Если указан лимит трафика, добавляем его
            if traffic_limit:
                new_client["totalGB"] = traffic_limit
            
            # Добавляем клиента в список
            if "clients" not in settings:
                settings["clients"] = []
                
            settings["clients"].append(new_client)
            
            # Обновляем inbound
            update_data = {
                "id": inbound_id,
                "settings": json.dumps(settings)
            }
            
            await self._make_request("POST", "/panel/api/inbounds/update", update_data)
            
            # Возвращаем данные клиента
            return {
                "id": uuid_str,
                "email": email,
                "inbound_id": inbound_id,
                "traffic_limit": traffic_limit
            }
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to update inbound settings: {e}")
            raise XRayAPIError(f"Failed to update inbound settings: {e}")
    
    async def remove_client(self, inbound_id: int, email: str) -> bool:
        """Удаляет клиента из inbound по email"""
        # Получаем информацию о inbound
        response = await self._make_request("GET", f"/panel/api/inbounds/{inbound_id}/get")
        inbound = response.get("obj", {})
        
        # Получаем текущие настройки
        settings_data = inbound.get("settings", "{}")
        try:
            if isinstance(settings_data, str):
                settings = json.loads(settings_data)
            else:
                settings = settings_data
                
            # Ищем клиента по email
            if "clients" not in settings:
                return False
                
            original_clients_count = len(settings["clients"])
            settings["clients"] = [c for c in settings["clients"] if c.get("email") != email]
            
            # Если количество клиентов не изменилось, значит клиент не найден
            if len(settings["clients"]) == original_clients_count:
                return False
                
            # Обновляем inbound
            update_data = {
                "id": inbound_id,
                "settings": json.dumps(settings)
            }
            
            await self._make_request("POST", "/panel/api/inbounds/update", update_data)
            return True
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to update inbound settings: {e}")
            raise XRayAPIError(f"Failed to update inbound settings: {e}")
    
    async def get_client_traffic(self, email: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о трафике клиента по email"""
        # Получаем все inbounds
        inbounds = await self.get_inbounds()
        
        # Ищем клиента по email во всех inbounds
        for inbound in inbounds:
            inbound_id = inbound.get("id")
            clients = await self.get_clients(inbound_id)
            
            for client in clients:
                if client.get("email") == email:
                    # Нашли клиента, возвращаем информацию о трафике
                    return {
                        "email": email,
                        "up": client.get("up", 0),
                        "down": client.get("down", 0),
                        "total": client.get("up", 0) + client.get("down", 0),
                        "limit": client.get("totalGB", 0)
                    }
        
        return None
    
    async def generate_subscription_link(self, inbound_id: int, client_id: str) -> str:
        """Генерирует ссылку для подписки на VPN"""
        # Получаем информацию о inbound
        response = await self._make_request("GET", f"/panel/api/inbounds/{inbound_id}/get")
        inbound = response.get("obj", {})
        
        protocol = inbound.get("protocol", "").lower()
        port = inbound.get("port", 443)
        
        # Базовая часть хоста (без протокола)
        host_parts = self.host.split("://")
        base_host = host_parts[-1].split(":")[0] if ":" in host_parts[-1] else host_parts[-1]
        
        # Формируем ссылку в зависимости от протокола
        if protocol == "vmess":
            config = {
                "v": "2",
                "ps": f"VPN Bot - {client_id[:8]}",
                "add": base_host,
                "port": port,
                "id": client_id,
                "aid": 0,
                "net": "ws",
                "type": "none",
                "host": base_host,
                "path": "/",
                "tls": "tls"
            }
            config_str = json.dumps(config)
            encoded = base64.b64encode(config_str.encode()).decode()
            return f"vmess://{encoded}"
            
        elif protocol == "vless":
            return f"vless://{client_id}@{base_host}:{port}?type=ws&security=tls&path=/#VPN%20Bot"
            
        else:
            raise XRayAPIError(f"Unsupported protocol: {protocol}")
    
    async def close(self):
        """Закрывает HTTP-сессию"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Создаем глобальный экземпляр для работы с API
xray_api = XRayAPI() 