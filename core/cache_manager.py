"""
Gerenciamento de cache local
Implementa cache com TTL e persistência em arquivo
"""

import pickle
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import streamlit as st
from typing import Any, Optional, Dict
import hashlib

class CacheManager:
    """
    Gerenciador de cache para dados do sistema
    """
    
    def __init__(self, cache_dir: str = "cache", ttl: int = 300):
        """
        Inicializa gerenciador de cache
        
        Args:
            cache_dir: Diretório para arquivos de cache
            ttl: Time To Live em segundos (padrão: 5 minutos)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        self.memory_cache = {}
        self.cache_timestamps = {}
        
        # Criar diretório de cache se não existir
        self.cache_dir.mkdir(exist_ok=True)
    
    def get(self, key: str, use_memory: bool = True, 
            use_disk: bool = True) -> Optional[Any]:
        """
        Obtém item do cache
        
        Args:
            key: Chave do cache
            use_memory: Usar cache em memória
            use_disk: Usar cache em disco
            
        Returns:
            Item do cache ou None se expirado/não existir
        """
        # Tentar memória primeiro
        if use_memory and key in self.memory_cache:
            if self._is_valid(key):
                return self.memory_cache[key]
            else:
                # Remover do cache se expirado
                self.delete(key)
        
        # Tentar disco
        if use_disk:
            disk_data = self._get_from_disk(key)
            if disk_data is not None:
                # Atualizar cache em memória
                self.memory_cache[key] = disk_data
                self.cache_timestamps[key] = time.time()
                return disk_data
        
        return None
    
    def set(self, key: str, value: Any, 
            persist: bool = True, ttl: Optional[int] = None):
        """
        Armazena item no cache
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            persist: Persistir em disco
            ttl: TTL específico para este item
        """
        # Armazenar em memória
        self.memory_cache[key] = value
        self.cache_timestamps[key] = time.time()
        
        # Persistir em disco se necessário
        if persist:
            self._save_to_disk(key, value, ttl or self.ttl)
    
    def delete(self, key: str):
        """
        Remove item do cache
        
        Args:
            key: Chave do cache
        """
        # Remover da memória
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        if key in self.cache_timestamps:
            del self.cache_timestamps[key]
        
        # Remover do disco
        self._delete_from_disk(key)
    
    def invalidate_cache(self, pattern: Optional[str] = None):
        """
        Invalida cache com base em padrão
        
        Args:
            pattern: Padrão para invalidação seletiva
        """
        if pattern:
            # Invalidação seletiva
            keys_to_delete = []
            for key in list(self.memory_cache.keys()):
                if pattern in key:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                self.delete(key)
            
            # Invalidar no disco
            self._invalidate_disk_cache(pattern)
        else:
            # Invalidação total
            self.memory_cache.clear()
            self.cache_timestamps.clear()
            
            # Limpar diretório de cache
            for file in self.cache_dir.glob("*.pkl"):
                try:
                    file.unlink()
                except:
                    pass
    
    def cleanup_expired(self):
        """
        Remove itens expirados do cache
        """
        current_time = time.time()
        expired_keys = []
        
        for key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp > self.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            self.delete(key)
        
        # Limpar arquivos expirados no disco
        self._cleanup_disk_cache()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do cache
        
        Returns:
            Dicionário com estatísticas
        """
        current_time = time.time()
        
        # Contar itens válidos
        valid_items = 0
        expired_items = 0
        
        for key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp <= self.ttl:
                valid_items += 1
            else:
                expired_items += 1
        
        # Estatísticas de disco
        disk_files = list(self.cache_dir.glob("*.pkl"))
        
        return {
            'memory_items': len(self.memory_cache),
            'valid_items': valid_items,
            'expired_items': expired_items,
            'disk_files': len(disk_files),
            'ttl': self.ttl
        }
    
    def _is_valid(self, key: str) -> bool:
        """
        Verifica se item do cache ainda é válido
        
        Args:
            key: Chave do cache
            
        Returns:
            True se item ainda válido
        """
        if key not in self.cache_timestamps:
            return False
        
        current_time = time.time()
        return current_time - self.cache_timestamps[key] <= self.ttl
    
    def _get_from_disk(self, key: str) -> Optional[Any]:
        """
        Obtém item do cache em disco
        
        Args:
            key: Chave do cache
            
        Returns:
            Item do cache ou None
        """
        cache_file = self._get_cache_file(key)
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                # Verificar se não expirou
                if 'expires' in cache_data and cache_data['expires'] < time.time():
                    # Remover arquivo expirado
                    cache_file.unlink()
                    return None
                
                return cache_data.get('value')
            except:
                # Em caso de erro, remover arquivo corrompido
                try:
                    cache_file.unlink()
                except:
                    pass
        
        return None
    
    def _save_to_disk(self, key: str, value: Any, ttl: int):
        """
        Salva item no cache em disco
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            ttl: TTL em segundos
        """
        cache_file = self._get_cache_file(key)
        
        cache_data = {
            'key': key,
            'value': value,
            'created': time.time(),
            'expires': time.time() + ttl,
            'ttl': ttl
        }
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            print(f"Erro ao salvar cache em disco: {e}")
    
    def _delete_from_disk(self, key: str):
        """
        Remove item do cache em disco
        
        Args:
            key: Chave do cache
        """
        cache_file = self._get_cache_file(key)
        
        if cache_file.exists():
            try:
                cache_file.unlink()
            except:
                pass
    
    def _invalidate_disk_cache(self, pattern: str):
        """
        Invalida cache em disco com base em padrão
        
        Args:
            pattern: Padrão para busca
        """
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                if pattern in cache_data.get('key', ''):
                    cache_file.unlink()
            except:
                # Ignorar arquivos corrompidos
                pass
    
    def _cleanup_disk_cache(self):
        """
        Remove arquivos de cache expirados do disco
        """
        current_time = time.time()
        
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                if cache_data.get('expires', 0) < current_time:
                    cache_file.unlink()
            except:
                # Remover arquivos corrompidos
                try:
                    cache_file.unlink()
                except:
                    pass
    
    def _get_cache_file(self, key: str) -> Path:
        """
        Obtém caminho do arquivo de cache
        
        Args:
            key: Chave do cache
            
        Returns:
            Caminho do arquivo
        """
        # Criar hash da chave para nome de arquivo seguro
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.pkl"

# Instância global do gerenciador de cache
cache_manager = CacheManager()

def get_cached_data(key: str, generator_func, force_refresh: bool = False, 
                   ttl: Optional[int] = None) -> Any:
    """
    Função auxiliar para obter dados do cache ou gerar novos
    
    Args:
        key: Chave do cache
        generator_func: Função para gerar dados se não estiverem em cache
        force_refresh: Forçar geração de novos dados
        ttl: TTL específico para este cache
        
    Returns:
        Dados do cache ou gerados
    """
    if not force_refresh:
        cached = cache_manager.get(key)
        if cached is not None:
            return cached
    
    # Gerar novos dados
    data = generator_func()
    
    # Armazenar no cache
    cache_manager.set(key, data, ttl=ttl or cache_manager.ttl)
    
    return data

def update_session_cache():
    """
    Atualiza cache na sessão do Streamlit
    """
    # Esta função sincroniza o cache do CacheManager com o session state
    # para permitir acesso rápido entre diferentes componentes
    
    if 'cache_manager' not in st.session_state:
        st.session_state.cache_manager = cache_manager