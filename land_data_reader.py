#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EndStone ARC Core 领地数据读取器

这是一个独立的工具文件，用于读取EndStone ARC Core插件的领地数据库中的所有领地信息。
可以直接复制到其他项目中使用。

使用方法：
    from land_data_reader import LandDataReader
    
    # 创建读取器实例（需要提供数据库文件路径）
    reader = LandDataReader("path/to/your/database.db")
    
    # 读取所有领地数据
    all_lands = reader.get_all_lands()
    
    # 读取特定玩家的领地
    player_lands = reader.get_player_lands("player_uuid")
    
    # 获取特定领地信息
    land_info = reader.get_land_info(land_id)

Author: DEVILENMO
"""

import sqlite3
import json
from typing import List, Dict, Optional, Any
from pathlib import Path


class LandDataReader:
    """领地数据读取器"""
    
    def __init__(self, db_path: str):
        """
        初始化领地数据读取器
        
        Args:
            db_path (str): 数据库文件路径，通常位于插件数据目录下
        """
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """检查数据库文件是否存在"""
        db_file = Path(self.db_path)
        if not db_file.exists():
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以像字典一样访问
        return conn
    
    def _execute_query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        执行查询SQL语句
        
        Args:
            sql (str): SQL查询语句
            params (tuple): SQL参数
            
        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"查询数据库时发生错误: {str(e)}")
            return []
    
    def _execute_query_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        执行查询SQL语句并返回单条记录
        
        Args:
            sql (str): SQL查询语句
            params (tuple): SQL参数
            
        Returns:
            Optional[Dict[str, Any]]: 查询结果或None
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"查询数据库时发生错误: {str(e)}")
            return None
    
    def get_all_lands(self) -> List[Dict[str, Any]]:
        """
        获取所有领地数据
        
        Returns:
            List[Dict[str, Any]]: 所有领地信息列表，每个元素包含领地的完整信息
        """
        try:
            results = self._execute_query("SELECT * FROM lands ORDER BY land_id")
            
            # 处理每个领地的数据
            processed_lands = []
            for land in results:
                processed_land = self._process_land_data(land)
                processed_lands.append(processed_land)
            
            return processed_lands
        except Exception as e:
            print(f"获取所有领地数据时发生错误: {str(e)}")
            return []
    
    def get_player_lands(self, player_xuid: str) -> List[Dict[str, Any]]:
        """
        获取特定玩家拥有的所有领地
        
        Args:
            player_xuid (str): 玩家XUID
            
        Returns:
            List[Dict[str, Any]]: 该玩家拥有的所有领地信息
        """
        try:
            results = self._execute_query(
                "SELECT * FROM lands WHERE owner_xuid = ? ORDER BY land_id",
                (player_xuid,)
            )
            
            processed_lands = []
            for land in results:
                processed_land = self._process_land_data(land)
                processed_lands.append(processed_land)
            
            return processed_lands
        except Exception as e:
            print(f"获取玩家领地数据时发生错误: {str(e)}")
            return []
    
    def get_land_info(self, land_id: int) -> Optional[Dict[str, Any]]:
        """
        根据领地ID获取领地信息
        
        Args:
            land_id (int): 领地ID
            
        Returns:
            Optional[Dict[str, Any]]: 领地信息或None
        """
        try:
            result = self._execute_query_one(
                "SELECT * FROM lands WHERE land_id = ?",
                (land_id,)
            )
            
            if result:
                return self._process_land_data(result)
            return None
        except Exception as e:
            print(f"获取领地信息时发生错误: {str(e)}")
            return None
    
    def get_lands_by_dimension(self, dimension: str) -> List[Dict[str, Any]]:
        """
        获取特定维度的所有领地
        
        Args:
            dimension (str): 维度名称（如：overworld, nether, the_end）
            
        Returns:
            List[Dict[str, Any]]: 该维度的所有领地信息
        """
        try:
            results = self._execute_query(
                "SELECT * FROM lands WHERE dimension = ? ORDER BY land_id",
                (dimension,)
            )
            
            processed_lands = []
            for land in results:
                processed_land = self._process_land_data(land)
                processed_lands.append(processed_land)
            
            return processed_lands
        except Exception as e:
            print(f"获取维度领地数据时发生错误: {str(e)}")
            return []
    
    def search_lands_by_name(self, name_pattern: str) -> List[Dict[str, Any]]:
        """
        根据名称模式搜索领地
        
        Args:
            name_pattern (str): 名称模式，支持SQL LIKE语法（%表示任意字符）
            
        Returns:
            List[Dict[str, Any]]: 匹配的领地信息列表
        """
        try:
            results = self._execute_query(
                "SELECT * FROM lands WHERE land_name LIKE ? ORDER BY land_id",
                (name_pattern,)
            )
            
            processed_lands = []
            for land in results:
                processed_land = self._process_land_data(land)
                processed_lands.append(processed_land)
            
            return processed_lands
        except Exception as e:
            print(f"搜索领地时发生错误: {str(e)}")
            return []
    
    def get_land_statistics(self) -> Dict[str, Any]:
        """
        获取领地统计信息
        
        Returns:
            Dict[str, Any]: 统计信息，包含总数、各维度数量等
        """
        try:
            # 总领地数
            total_result = self._execute_query_one("SELECT COUNT(*) as total FROM lands")
            total_lands = total_result['total'] if total_result else 0
            
            # 各维度领地数
            dimension_stats = self._execute_query(
                "SELECT dimension, COUNT(*) as count FROM lands GROUP BY dimension"
            )
            
            # 各玩家领地数排行
            player_stats = self._execute_query(
                "SELECT owner_xuid, COUNT(*) as count FROM lands GROUP BY owner_xuid ORDER BY count DESC LIMIT 10"
            )
            
            return {
                'total_lands': total_lands,
                'lands_by_dimension': {stat['dimension']: stat['count'] for stat in dimension_stats},
                'top_land_owners': player_stats
            }
        except Exception as e:
            print(f"获取统计信息时发生错误: {str(e)}")
            return {}
    
    def _process_land_data(self, land_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理原始领地数据，进行格式化和解析
        
        Args:
            land_data (Dict[str, Any]): 原始领地数据
            
        Returns:
            Dict[str, Any]: 处理后的领地数据
        """
        try:
            # 复制原数据
            processed = dict(land_data)
            
            # 解析JSON格式的共享用户列表
            if 'shared_users' in processed and processed['shared_users']:
                try:
                    processed['shared_users'] = json.loads(processed['shared_users'])
                except (json.JSONDecodeError, TypeError):
                    processed['shared_users'] = []
            else:
                processed['shared_users'] = []
            
            # 转换布尔值
            processed['allow_explosion'] = bool(processed.get('allow_explosion', 0))
            processed['allow_public_interact'] = bool(processed.get('allow_public_interact', 0))
            
            # 计算领地面积
            area = (processed['max_x'] - processed['min_x'] + 1) * (processed['max_z'] - processed['min_z'] + 1)
            processed['area'] = area
            
            # 添加领地中心点坐标
            center_x = (processed['min_x'] + processed['max_x']) / 2
            center_z = (processed['min_z'] + processed['max_z']) / 2
            processed['center_x'] = center_x
            processed['center_z'] = center_z
            
            return processed
        except Exception as e:
            print(f"处理领地数据时发生错误: {str(e)}")
            return dict(land_data)


def demo_usage():
    """演示如何使用LandDataReader"""
    print("=== EndStone ARC Core 领地数据读取器 演示 ===\n")
    
    # 注意：需要修改为你的实际数据库路径
    db_path = "plugins/ARCCore/database.db"
    
    try:
        # 创建读取器实例
        reader = LandDataReader(db_path)
        print(f"成功连接到数据库: {db_path}\n")
        
        # 1. 获取统计信息
        print("1. 领地统计信息:")
        stats = reader.get_land_statistics()
        print(f"   总领地数: {stats.get('total_lands', 0)}")
        print(f"   各维度领地数: {stats.get('lands_by_dimension', {})}")
        print(f"   拥有领地最多的前10位玩家:")
        for owner in stats.get('top_land_owners', [])[:5]:
            print(f"     XUID: {owner['owner_xuid'][:8]}... - 领地数: {owner['count']}")
        print()
        
        # 2. 获取所有领地（显示前5个）
        print("2. 所有领地信息（显示前5个）:")
        all_lands = reader.get_all_lands()
        for i, land in enumerate(all_lands[:5]):
            print(f"   领地 #{land['land_id']}: {land['land_name']}")
            print(f"     拥有者: {land['owner_xuid'][:8]}...")
            print(f"     维度: {land['dimension']}")
            print(f"     坐标: ({land['min_x']}, {land['min_z']}) 到 ({land['max_x']}, {land['max_z']})")
            print(f"     面积: {land['area']} 方块")
            print(f"     传送点: ({land['tp_x']}, {land['tp_y']}, {land['tp_z']})")
            print(f"     共享用户数: {len(land['shared_users'])}")
            print(f"     允许爆炸: {land['allow_explosion']}")
            print(f"     允许公共交互: {land['allow_public_interact']}")
            print()
        
        # 3. 搜索领地
        print("3. 搜索包含'家'的领地:")
        search_results = reader.search_lands_by_name("%家%")
        for land in search_results[:3]:
            print(f"   {land['land_name']} (ID: {land['land_id']})")
        print()
        
        # 4. 按维度查询
        print("4. 主世界的领地数量:")
        overworld_lands = reader.get_lands_by_dimension("overworld")
        print(f"   主世界共有 {len(overworld_lands)} 个领地")
        
    except FileNotFoundError:
        print(f"错误: 找不到数据库文件 {db_path}")
        print("请确保:")
        print("1. 数据库文件路径正确")
        print("2. 数据库文件存在且可读")
    except Exception as e:
        print(f"发生错误: {str(e)}")


if __name__ == "__main__":
    demo_usage()
