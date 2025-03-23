"""
Модели для кластеризации VPN серверов
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import logging
import random

from ..database import db
from ..exceptions import DatabaseError, VPNServerError


logger = logging.getLogger(__name__)


@dataclass
class VPNCluster:
    """Модель кластера VPN-серверов"""
    id: int
    name: str
    description: str
    is_active: bool = True
    max_load: int = 1000  # Максимальное количество пользователей
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def document(self) -> dict:
        """Преобразует объект в документ для MongoDB"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "max_load": self.max_load,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_document(cls, document: dict) -> 'VPNCluster':
        """Создает объект из документа MongoDB"""
        return cls(
            id=document["id"],
            name=document["name"],
            description=document["description"],
            is_active=document.get("is_active", True),
            max_load=document.get("max_load", 1000),
            created_at=document.get("created_at", datetime.now()),
            updated_at=document.get("updated_at", datetime.now())
        )
    
    @classmethod
    async def create(cls, name: str, description: str, max_load: int = 1000) -> 'VPNCluster':
        """Создает новый кластер VPN-серверов"""
        try:
            # Получение следующего ID
            next_id = await db.get_next_id("vpn_clusters")
            
            # Создание объекта кластера
            cluster = cls(
                id=next_id,
                name=name,
                description=description,
                max_load=max_load
            )
            
            # Сохранение в базу данных
            await db.vpn_clusters.insert_one(cluster.document)
            
            logger.info(f"Created new VPN cluster: {cluster.id} - {cluster.name}")
            return cluster
        except Exception as e:
            logger.error(f"Error creating VPN cluster: {str(e)}")
            raise DatabaseError(f"Failed to create VPN cluster: {str(e)}")
    
    @classmethod
    async def get_by_id(cls, cluster_id: int) -> Optional['VPNCluster']:
        """Получает кластер по ID"""
        try:
            document = await db.vpn_clusters.find_one({"id": cluster_id})
            if document:
                return cls.from_document(document)
            return None
        except Exception as e:
            logger.error(f"Error getting VPN cluster by ID {cluster_id}: {str(e)}")
            raise DatabaseError(f"Failed to get VPN cluster: {str(e)}")
    
    @classmethod
    async def get_by_name(cls, name: str) -> Optional['VPNCluster']:
        """Получает кластер по имени"""
        try:
            document = await db.vpn_clusters.find_one({"name": name})
            if document:
                return cls.from_document(document)
            return None
        except Exception as e:
            logger.error(f"Error getting VPN cluster by name {name}: {str(e)}")
            raise DatabaseError(f"Failed to get VPN cluster: {str(e)}")
    
    @classmethod
    async def get_all(cls) -> List['VPNCluster']:
        """Получает все кластеры"""
        try:
            cursor = db.vpn_clusters.find()
            clusters = []
            async for document in cursor:
                clusters.append(cls.from_document(document))
            return clusters
        except Exception as e:
            logger.error(f"Error getting all VPN clusters: {str(e)}")
            raise DatabaseError(f"Failed to get VPN clusters: {str(e)}")
    
    @classmethod
    async def get_all_active(cls) -> List['VPNCluster']:
        """Получает все активные кластеры"""
        try:
            cursor = db.vpn_clusters.find({"is_active": True})
            clusters = []
            async for document in cursor:
                clusters.append(cls.from_document(document))
            return clusters
        except Exception as e:
            logger.error(f"Error getting active VPN clusters: {str(e)}")
            raise DatabaseError(f"Failed to get active VPN clusters: {str(e)}")
    
    async def update(self, **kwargs) -> bool:
        """Обновляет данные кластера"""
        try:
            # Добавляем время обновления
            kwargs["updated_at"] = datetime.now()
            
            # Обновляем атрибуты объекта
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            # Выполняем обновление в базе данных
            result = await db.vpn_clusters.update_one(
                {"id": self.id},
                {"$set": kwargs}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Updated VPN cluster: {self.id}")
            else:
                logger.warning(f"VPN cluster not updated: {self.id}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating VPN cluster {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to update VPN cluster: {str(e)}")
    
    async def delete(self) -> bool:
        """Удаляет кластер"""
        try:
            # Проверяем, есть ли серверы в кластере
            servers_count = await db.vpn_servers.count_documents({"cluster_id": self.id})
            if servers_count > 0:
                logger.warning(f"Cannot delete cluster {self.id} with {servers_count} servers")
                return False
            
            # Удаляем кластер
            result = await db.vpn_clusters.delete_one({"id": self.id})
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted VPN cluster: {self.id}")
            else:
                logger.warning(f"VPN cluster not deleted: {self.id}")
            
            return success
        except Exception as e:
            logger.error(f"Error deleting VPN cluster {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to delete VPN cluster: {str(e)}")
    
    async def get_load(self) -> int:
        """Получает текущую нагрузку кластера (количество активных подписок)"""
        try:
            # Получаем все серверы в кластере
            cursor = db.vpn_servers.find({"cluster_id": self.id, "is_active": True})
            server_ids = []
            async for document in cursor:
                server_ids.append(document["id"])
            
            if not server_ids:
                return 0
            
            # Считаем активные подписки на этих серверах
            return await db.subscriptions.count_documents({
                "server_id": {"$in": server_ids},
                "is_active": True
            })
        except Exception as e:
            logger.error(f"Error getting cluster load {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to get cluster load: {str(e)}")


@dataclass
class VPNServer:
    """Модель VPN-сервера внутри кластера"""
    id: int
    cluster_id: int
    name: str
    country: str
    city: str
    ip_address: str
    api_url: str
    api_username: str
    api_password: str
    is_active: bool = True
    priority: int = 1  # Приоритет сервера в кластере
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def document(self) -> dict:
        """Преобразует объект в документ для MongoDB"""
        return {
            "id": self.id,
            "cluster_id": self.cluster_id,
            "name": self.name,
            "country": self.country,
            "city": self.city,
            "ip_address": self.ip_address,
            "api_url": self.api_url,
            "api_username": self.api_username,
            "api_password": self.api_password,
            "is_active": self.is_active,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_document(cls, document: dict) -> 'VPNServer':
        """Создает объект из документа MongoDB"""
        return cls(
            id=document["id"],
            cluster_id=document["cluster_id"],
            name=document["name"],
            country=document["country"],
            city=document["city"],
            ip_address=document["ip_address"],
            api_url=document["api_url"],
            api_username=document["api_username"],
            api_password=document["api_password"],
            is_active=document.get("is_active", True),
            priority=document.get("priority", 1),
            created_at=document.get("created_at", datetime.now()),
            updated_at=document.get("updated_at", datetime.now())
        )
    
    @classmethod
    async def create(cls, cluster_id: int, name: str, country: str, city: str,
                    ip_address: str, api_url: str, api_username: str, api_password: str,
                    priority: int = 1) -> 'VPNServer':
        """Создает новый VPN-сервер"""
        try:
            # Проверяем, существует ли кластер
            cluster = await VPNCluster.get_by_id(cluster_id)
            if not cluster:
                raise DatabaseError(f"Cluster with ID {cluster_id} not found")
            
            # Получение следующего ID
            next_id = await db.get_next_id("vpn_servers")
            
            # Создание объекта сервера
            server = cls(
                id=next_id,
                cluster_id=cluster_id,
                name=name,
                country=country,
                city=city,
                ip_address=ip_address,
                api_url=api_url,
                api_username=api_username,
                api_password=api_password,
                priority=priority
            )
            
            # Сохранение в базу данных
            await db.vpn_servers.insert_one(server.document)
            
            logger.info(f"Created new VPN server: {server.id} - {server.name} in cluster {cluster_id}")
            return server
        except Exception as e:
            logger.error(f"Error creating VPN server: {str(e)}")
            raise DatabaseError(f"Failed to create VPN server: {str(e)}")
    
    @classmethod
    async def get_by_id(cls, server_id: int) -> Optional['VPNServer']:
        """Получает сервер по ID"""
        try:
            document = await db.vpn_servers.find_one({"id": server_id})
            if document:
                return cls.from_document(document)
            return None
        except Exception as e:
            logger.error(f"Error getting VPN server by ID {server_id}: {str(e)}")
            raise DatabaseError(f"Failed to get VPN server: {str(e)}")
    
    @classmethod
    async def get_by_name(cls, name: str) -> Optional['VPNServer']:
        """Получает сервер по имени"""
        try:
            document = await db.vpn_servers.find_one({"name": name})
            if document:
                return cls.from_document(document)
            return None
        except Exception as e:
            logger.error(f"Error getting VPN server by name {name}: {str(e)}")
            raise DatabaseError(f"Failed to get VPN server: {str(e)}")
    
    @classmethod
    async def get_by_cluster(cls, cluster_id: int) -> List['VPNServer']:
        """Получает все сервера кластера"""
        try:
            cursor = db.vpn_servers.find({"cluster_id": cluster_id}).sort("priority", 1)
            servers = []
            async for document in cursor:
                servers.append(cls.from_document(document))
            return servers
        except Exception as e:
            logger.error(f"Error getting VPN servers by cluster {cluster_id}: {str(e)}")
            raise DatabaseError(f"Failed to get VPN servers: {str(e)}")
    
    @classmethod
    async def get_by_country(cls, country: str) -> List['VPNServer']:
        """Получает все сервера в указанной стране"""
        try:
            cursor = db.vpn_servers.find({"country": country, "is_active": True}).sort("priority", 1)
            servers = []
            async for document in cursor:
                servers.append(cls.from_document(document))
            return servers
        except Exception as e:
            logger.error(f"Error getting VPN servers by country {country}: {str(e)}")
            raise DatabaseError(f"Failed to get VPN servers: {str(e)}")
    
    @classmethod
    async def get_all(cls) -> List['VPNServer']:
        """Получает все сервера"""
        try:
            cursor = db.vpn_servers.find().sort("cluster_id", 1).sort("priority", 1)
            servers = []
            async for document in cursor:
                servers.append(cls.from_document(document))
            return servers
        except Exception as e:
            logger.error(f"Error getting all VPN servers: {str(e)}")
            raise DatabaseError(f"Failed to get VPN servers: {str(e)}")
    
    @classmethod
    async def get_all_active(cls) -> List['VPNServer']:
        """Получает все активные сервера"""
        try:
            cursor = db.vpn_servers.find({"is_active": True}).sort("cluster_id", 1).sort("priority", 1)
            servers = []
            async for document in cursor:
                servers.append(cls.from_document(document))
            return servers
        except Exception as e:
            logger.error(f"Error getting active VPN servers: {str(e)}")
            raise DatabaseError(f"Failed to get active VPN servers: {str(e)}")
    
    async def update(self, **kwargs) -> bool:
        """Обновляет данные сервера"""
        try:
            # Добавляем время обновления
            kwargs["updated_at"] = datetime.now()
            
            # Обновляем атрибуты объекта
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            # Выполняем обновление в базе данных
            result = await db.vpn_servers.update_one(
                {"id": self.id},
                {"$set": kwargs}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Updated VPN server: {self.id}")
            else:
                logger.warning(f"VPN server not updated: {self.id}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating VPN server {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to update VPN server: {str(e)}")
    
    async def delete(self) -> bool:
        """Удаляет сервер"""
        try:
            # Проверяем, есть ли подписки на этом сервере
            subscriptions_count = await db.subscriptions.count_documents({
                "server_id": self.id,
                "is_active": True
            })
            
            if subscriptions_count > 0:
                logger.warning(f"Cannot delete server {self.id} with {subscriptions_count} active subscriptions")
                return False
            
            # Удаляем сервер
            result = await db.vpn_servers.delete_one({"id": self.id})
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted VPN server: {self.id}")
            else:
                logger.warning(f"VPN server not deleted: {self.id}")
            
            return success
        except Exception as e:
            logger.error(f"Error deleting VPN server {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to delete VPN server: {str(e)}")
    
    async def get_load(self) -> int:
        """Получает текущую нагрузку сервера (количество активных подписок)"""
        try:
            # Считаем активные подписки на сервере
            return await db.subscriptions.count_documents({
                "server_id": self.id,
                "is_active": True
            })
        except Exception as e:
            logger.error(f"Error getting server load {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to get server load: {str(e)}")
    
    async def create_vpn_account(self, email: str, duration_days: int = 30) -> dict:
        """
        Создает аккаунт VPN на сервере через API X-UI
        
        Args:
            email: Email пользователя (используется как идентификатор)
            duration_days: Срок действия аккаунта в днях
            
        Returns:
            Словарь с информацией о созданном аккаунте
        """
        import aiohttp
        import uuid
        from datetime import datetime, timedelta
        
        try:
            # Генерируем UUID для нового аккаунта
            account_uuid = str(uuid.uuid4())
            
            # Рассчитываем время окончания
            expire_time = int((datetime.now() + timedelta(days=duration_days)).timestamp() * 1000)
            
            # Подготавливаем данные для API
            account_data = {
                "id": account_uuid,
                "flow": "",
                "email": email,
                "limitIp": 0,  # 0 = без ограничений
                "totalGB": 0,   # 0 = без ограничений
                "expiryTime": expire_time,
                "enable": True,
                "tgId": "",
                "subId": ""
            }
            
            # Отправляем запрос к API сервера
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.api_username, self.api_password)
                
                async with session.post(
                    f"{self.api_url}/api/inbounds/addClient",
                    auth=auth,
                    json=account_data,
                    timeout=10,
                    ssl=False
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API error: {response.status}, {error_text}")
                    
                    result = await response.json()
                    
                    # Возвращаем информацию о созданном аккаунте
                    return {
                        "uuid": account_uuid,
                        "email": email,
                        "expire_time": expire_time,
                        "server_id": self.id,
                        "result": result
                    }
                    
        except Exception as e:
            logger.error(f"Error creating VPN account on server {self.id}: {str(e)}")
            raise Exception(f"Failed to create VPN account: {str(e)}")


async def get_optimal_server() -> Optional[VPNServer]:
    """
    Выбирает оптимальный сервер для нового пользователя на основе нагрузки серверов.
    
    Алгоритм:
    1. Получаем все активные сервера
    2. Фильтруем сервера с высоким приоритетом
    3. Сортируем по текущей нагрузке (количеству активных подписок)
    4. Возвращаем сервер с наименьшей нагрузкой
    
    Returns:
        Объект сервера или None, если нет доступных серверов
    """
    try:
        # Получаем все активные сервера
        servers = await VPNServer.get_all_active()
        
        if not servers:
            logger.warning("No active VPN servers available")
            return None
        
        # Подготавливаем словарь с серверами и их нагрузкой
        server_loads = []
        
        for server in servers:
            # Получаем кластер, чтобы узнать максимальную нагрузку
            cluster = await VPNCluster.get_by_id(server.cluster_id)
            if not cluster or not cluster.is_active:
                continue
                
            # Получаем текущую нагрузку сервера
            load = await server.get_load()
            max_load = cluster.max_load
            
            # Вычисляем процент загрузки
            load_percentage = (load / max_load) * 100 if max_load > 0 else 100
            
            # Добавляем в список, если загрузка не критическая (< 90%)
            if load_percentage < 90:
                server_loads.append({
                    "server": server,
                    "load": load,
                    "load_percentage": load_percentage,
                    "priority": server.priority
                })
        
        if not server_loads:
            logger.warning("All VPN servers are overloaded")
            return None
        
        # Сортируем серверы сначала по приоритету (меньше = важнее), затем по загрузке
        server_loads.sort(key=lambda x: (x["priority"], x["load_percentage"]))
        
        # Берем несколько серверов с наименьшей загрузкой и высоким приоритетом
        best_servers = server_loads[:3] if len(server_loads) >= 3 else server_loads
        
        # Случайным образом выбираем один из лучших серверов для равномерного распределения
        selected = random.choice(best_servers)
        
        logger.info(f"Selected optimal server: {selected['server'].name} (ID: {selected['server'].id}) with load {selected['load_percentage']:.2f}%")
        return selected["server"]
        
    except Exception as e:
        logger.error(f"Error selecting optimal server: {str(e)}")
        raise VPNServerError(f"Failed to select optimal server: {str(e)}") 