import aiohttp
import uuid
import logging
import json
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..settings import Settings


# Создаем экземпляр настроек
settings = Settings()


class XRayAPI:
    def __init__(
        self, 
        host: str = None, 
        username: str = None, 
        password: str = None
    ):
        self.host = host or settings.xui_api_url
        self.username = username or settings.xui_api_username
        self.password = password or settings.xui_api_password
        self.token = None
        self.cookie = None
        self._logger = logging.getLogger(__name__)

    async def _login(self) -> bool:
        """Авторизация в панели 3x-ui"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.host}/login"
                data = {
                    "username": self.username,
                    "password": self.password
                }
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        if response_data.get("success", False):
                            # Сохраняем cookie для последующих запросов
                            cookies = response.cookies
                            self.cookie = {cookie.key: cookie.value for cookie in cookies.values()}
                            return True
                    self._logger.error(f"Login failed: HTTP {response.status}")
                    return False
        except Exception as e:
            self._logger.error(f"Login error: {str(e)}")
            return False

    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict[str, Any]]:
        """Выполнение запроса к API панели 3x-ui"""
        if not self.cookie:
            if not await self._login():
                return None

        url = f"{self.host}{endpoint}"
        try:
            async with aiohttp.ClientSession(cookies=self.cookie) as session:
                if method.upper() == "GET":
                    async with session.get(url) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 401:
                            # Токен устарел, делаем повторный логин
                            if await self._login():
                                return await self._make_request(method, endpoint, data)
                        self._logger.error(f"Request failed: HTTP {response.status}")
                        return None
                elif method.upper() == "POST":
                    async with session.post(url, json=data) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 401:
                            # Токен устарел, делаем повторный логин
                            if await self._login():
                                return await self._make_request(method, endpoint, data)
                        self._logger.error(f"Request failed: HTTP {response.status}")
                        return None
                elif method.upper() == "PUT":
                    async with session.put(url, json=data) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 401:
                            # Токен устарел, делаем повторный логин
                            if await self._login():
                                return await self._make_request(method, endpoint, data)
                        self._logger.error(f"Request failed: HTTP {response.status}")
                        return None
                elif method.upper() == "DELETE":
                    async with session.delete(url) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 401:
                            # Токен устарел, делаем повторный логин
                            if await self._login():
                                return await self._make_request(method, endpoint, data)
                        self._logger.error(f"Request failed: HTTP {response.status}")
                        return None
        except Exception as e:
            self._logger.error(f"API request error: {str(e)}")
            return None

    async def get_inbounds(self) -> List[Dict[str, Any]]:
        """Получение списка всех inbounds"""
        response = await self._make_request("GET", "/panel/api/inbounds/list")
        if response and response.get("success", False):
            return response.get("obj", [])
        return []

    async def get_inbound(self, inbound_id: int) -> Optional[Dict[str, Any]]:
        """Получение конкретного inbound по ID"""
        response = await self._make_request("GET", f"/panel/api/inbounds/{inbound_id}")
        if response and response.get("success", False):
            return response.get("obj", {})
        return None

    async def create_client(
        self, 
        inbound_id: int, 
        email: str, 
        traffic_limit_gb: Optional[int] = None, 
        expire_days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Создание нового клиента VPN
        
        Args:
            inbound_id: ID inbound для добавления клиента
            email: Email клиента (используется как идентификатор)
            traffic_limit_gb: Лимит трафика в GB (None = безлимитный)
            expire_days: Срок действия в днях
            
        Returns:
            Dict с данными созданного клиента или None в случае ошибки
        """
        try:
            # Получаем инбаунд для добавления клиента
            inbound = await self.get_inbound(inbound_id)
            if not inbound:
                self._logger.error(f"Inbound {inbound_id} not found")
                return None
                
            # Генерируем UUID для клиента
            client_id = str(uuid.uuid4())
            
            # Рассчитываем дату истечения
            expiry_time = int((datetime.now() + timedelta(days=expire_days)).timestamp() * 1000)
            
            # Подготавливаем данные клиента
            client_data = {
                "id": client_id,
                "flow": "",
                "email": email,
                "limitIp": 0,
                "totalGB": traffic_limit_gb * 1024 * 1024 * 1024 if traffic_limit_gb else 0,  # Конвертируем GB в байты
                "expiryTime": expiry_time,
                "enable": True,
                "tgId": "",
                "subId": ""
            }
            
            # Получаем текущих клиентов
            settings = json.loads(inbound.get("settings", "{}"))
            clients = settings.get("clients", [])
            
            # Добавляем нового клиента
            clients.append(client_data)
            settings["clients"] = clients
            
            # Обновляем настройки инбаунда
            inbound["settings"] = json.dumps(settings)
            
            # Отправляем запрос на обновление
            response = await self._make_request(
                "POST", 
                f"/panel/api/inbounds/{inbound_id}", 
                data=inbound
            )
            
            if response and response.get("success", False):
                # Генерируем ссылку для подключения
                subscription_url = await self.generate_subscription_url(inbound_id, client_id)
                
                # Возвращаем данные клиента и ссылку подписки
                return {
                    "client_id": client_id,
                    "email": email,
                    "inbound_id": inbound_id,
                    "traffic_limit_gb": traffic_limit_gb,
                    "expire_date": datetime.fromtimestamp(expiry_time / 1000).isoformat(),
                    "subscription_url": subscription_url
                }
                
            self._logger.error(f"Failed to create client: {response}")
            return None
        except Exception as e:
            self._logger.error(f"Create client error: {str(e)}")
            return None

    async def remove_client(self, inbound_id: int, client_id: str) -> bool:
        """
        Удаление клиента
        
        Args:
            inbound_id: ID inbound
            client_id: ID клиента (UUID)
            
        Returns:
            bool: True в случае успеха, иначе False
        """
        try:
            # Получаем инбаунд
            inbound = await self.get_inbound(inbound_id)
            if not inbound:
                self._logger.error(f"Inbound {inbound_id} not found")
                return False
                
            # Получаем текущих клиентов
            settings = json.loads(inbound.get("settings", "{}"))
            clients = settings.get("clients", [])
            
            # Находим и удаляем клиента
            clients = [client for client in clients if client.get("id") != client_id]
            settings["clients"] = clients
            
            # Обновляем настройки инбаунда
            inbound["settings"] = json.dumps(settings)
            
            # Отправляем запрос на обновление
            response = await self._make_request(
                "POST", 
                f"/panel/api/inbounds/{inbound_id}", 
                data=inbound
            )
            
            if response and response.get("success", False):
                return True
                
            self._logger.error(f"Failed to remove client: {response}")
            return False
        except Exception as e:
            self._logger.error(f"Remove client error: {str(e)}")
            return False

    async def get_client_stats(self, inbound_id: int, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение статистики клиента
        
        Args:
            inbound_id: ID inbound
            client_id: ID клиента (UUID)
            
        Returns:
            Dict с данными о статистике клиента или None в случае ошибки
        """
        try:
            # Получаем инбаунд
            inbound = await self.get_inbound(inbound_id)
            if not inbound:
                self._logger.error(f"Inbound {inbound_id} not found")
                return None
                
            # Получаем текущих клиентов
            settings = json.loads(inbound.get("settings", "{}"))
            clients = settings.get("clients", [])
            
            # Находим клиента
            client = next((c for c in clients if c.get("id") == client_id), None)
            if not client:
                self._logger.error(f"Client {client_id} not found in inbound {inbound_id}")
                return None
            
            # Получаем статистику клиента
            stats_response = await self._make_request(
                "GET", 
                f"/panel/api/inbounds/getClientTraffic/{inbound_id}/{client_id}"
            )
            
            if stats_response and stats_response.get("success", False):
                stats = stats_response.get("obj", {})
                
                # Рассчитываем оставшийся трафик
                total_limit = client.get("totalGB", 0)
                used_traffic = stats.get("up", 0) + stats.get("down", 0)
                remaining_traffic = max(0, total_limit - used_traffic) if total_limit > 0 else -1
                
                # Проверяем срок действия
                expiry_time = client.get("expiryTime", 0)
                now = datetime.now().timestamp() * 1000
                is_expired = expiry_time > 0 and now > expiry_time
                
                return {
                    "client_id": client_id,
                    "email": client.get("email", ""),
                    "upload_traffic": stats.get("up", 0),
                    "download_traffic": stats.get("down", 0),
                    "total_traffic": used_traffic,
                    "remaining_traffic": remaining_traffic,
                    "total_limit": total_limit,
                    "expiry_time": datetime.fromtimestamp(expiry_time / 1000).isoformat() if expiry_time > 0 else None,
                    "is_expired": is_expired,
                    "is_active": client.get("enable", False) and not is_expired and (remaining_traffic > 0 or total_limit == 0)
                }
                
            self._logger.error(f"Failed to get client stats: {stats_response}")
            return None
        except Exception as e:
            self._logger.error(f"Get client stats error: {str(e)}")
            return None

    async def generate_subscription_url(self, inbound_id: int, client_id: str) -> Optional[str]:
        """
        Генерация URL для подключения клиента
        
        Args:
            inbound_id: ID inbound
            client_id: ID клиента (UUID)
            
        Returns:
            str: URL для подключения или None в случае ошибки
        """
        try:
            response = await self._make_request(
                "GET", 
                f"/panel/api/inbounds/getClientSubscribe/{inbound_id}/{client_id}"
            )
            
            if response and response.get("success", False):
                return response.get("obj", "")
                
            self._logger.error(f"Failed to generate subscription URL: {response}")
            return None
        except Exception as e:
            self._logger.error(f"Generate subscription URL error: {str(e)}")
            return None

    async def update_client_traffic_limit(
        self, inbound_id: int, client_id: str, traffic_limit_gb: int
    ) -> bool:
        """
        Обновление лимита трафика клиента
        
        Args:
            inbound_id: ID inbound
            client_id: ID клиента (UUID)
            traffic_limit_gb: Новый лимит трафика в GB
            
        Returns:
            bool: True в случае успеха, иначе False
        """
        try:
            # Получаем инбаунд
            inbound = await self.get_inbound(inbound_id)
            if not inbound:
                self._logger.error(f"Inbound {inbound_id} not found")
                return False
                
            # Получаем текущих клиентов
            settings = json.loads(inbound.get("settings", "{}"))
            clients = settings.get("clients", [])
            
            # Находим клиента и обновляем лимит трафика
            for client in clients:
                if client.get("id") == client_id:
                    client["totalGB"] = traffic_limit_gb * 1024 * 1024 * 1024  # Конвертируем GB в байты
                    break
            else:
                self._logger.error(f"Client {client_id} not found in inbound {inbound_id}")
                return False
            
            # Обновляем настройки инбаунда
            inbound["settings"] = json.dumps(settings)
            
            # Отправляем запрос на обновление
            response = await self._make_request(
                "POST", 
                f"/panel/api/inbounds/{inbound_id}", 
                data=inbound
            )
            
            if response and response.get("success", False):
                return True
                
            self._logger.error(f"Failed to update client traffic limit: {response}")
            return False
        except Exception as e:
            self._logger.error(f"Update client traffic limit error: {str(e)}")
            return False

    async def update_client_expiry(self, inbound_id: int, client_id: str, expire_days: int) -> bool:
        """
        Обновление срока действия клиента
        
        Args:
            inbound_id: ID inbound
            client_id: ID клиента (UUID)
            expire_days: Новый срок действия в днях (от текущей даты)
            
        Returns:
            bool: True в случае успеха, иначе False
        """
        try:
            # Получаем инбаунд
            inbound = await self.get_inbound(inbound_id)
            if not inbound:
                self._logger.error(f"Inbound {inbound_id} not found")
                return False
                
            # Получаем текущих клиентов
            settings = json.loads(inbound.get("settings", "{}"))
            clients = settings.get("clients", [])
            
            # Рассчитываем новую дату истечения
            expiry_time = int((datetime.now() + timedelta(days=expire_days)).timestamp() * 1000)
            
            # Находим клиента и обновляем срок действия
            for client in clients:
                if client.get("id") == client_id:
                    client["expiryTime"] = expiry_time
                    break
            else:
                self._logger.error(f"Client {client_id} not found in inbound {inbound_id}")
                return False
            
            # Обновляем настройки инбаунда
            inbound["settings"] = json.dumps(settings)
            
            # Отправляем запрос на обновление
            response = await self._make_request(
                "POST", 
                f"/panel/api/inbounds/{inbound_id}", 
                data=inbound
            )
            
            if response and response.get("success", False):
                return True
                
            self._logger.error(f"Failed to update client expiry: {response}")
            return False
        except Exception as e:
            self._logger.error(f"Update client expiry error: {str(e)}")
            return False 