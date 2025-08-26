import amulet
from amulet.api.errors import ChunkLoadError, ChunkDoesNotExist
from amulet.api.chunk import Chunk
import time
from land_data_reader import LandDataReader

class ChunkAutoResetter:
    """
    区块自动重置器 - 保留领地覆盖的区块，重置其他区块
    支持与EndStone ARC Core领地插件集成
    """
    
    def __init__(self, world_path, land_db_path=None):
        """
        初始化区块重置器
        
        Args:
            world_path (str): Minecraft世界路径
            land_db_path (str): 领地数据库路径，如果不提供则不使用领地保护
        """
        self.world_path = world_path
        self.land_db_path = land_db_path
        self.level = None
        self.land_reader = None
        
        # 维度名称映射：领地数据库维度名 -> Minecraft维度名
        self.dimension_mapping = {
            'Overworld': 'minecraft:overworld',      # 首字母大写
            'Nether': 'minecraft:the_nether',        # 首字母大写
            'TheEnd': 'minecraft:the_end',           # 驼峰命名
            # 兼容小写格式（如果有的话）
            'overworld': 'minecraft:overworld',
            'nether': 'minecraft:the_nether',
            'the_end': 'minecraft:the_end'
        }
        
    def load_world(self):
        """加载Minecraft世界"""
        try:
            self.level = amulet.load_level(self.world_path)
            print(f"成功加载世界: {self.world_path}")
            
            # 如果提供了领地数据库路径，则初始化领地读取器
            if self.land_db_path:
                try:
                    self.land_reader = LandDataReader(self.land_db_path)
                    print(f"成功连接到领地数据库: {self.land_db_path}")
                except Exception as e:
                    print(f"警告: 无法连接到领地数据库 {self.land_db_path}: {e}")
                    print("将继续执行，但无法使用领地保护功能")
                    self.land_reader = None
            
            return True
        except Exception as e:
            print(f"加载世界失败: {e}")
            return False
    
    def close_world(self):
        """关闭世界"""
        if self.level:
            self.level.close()
            print("世界已关闭")
    
    def get_chunks_covered_by_lands(self, dimension="minecraft:overworld", extra_protection_distance=0):
        """
        获取被领地覆盖的所有区块坐标（包括额外保护距离）
        
        Args:
            dimension (str): Minecraft维度名称
            extra_protection_distance (int): 额外保护距离（区块单位），默认为0
            
        Returns:
            set: 被领地覆盖的区块坐标集合 {(cx1, cz1), (cx2, cz2), ...}
        """
        if not self.land_reader:
            print("警告: 领地数据读取器未初始化，无法获取领地覆盖的区块")
            return set()
        
        # 将Minecraft维度名转换为领地数据库维度名
        db_dimension = None
        for db_dim, mc_dim in self.dimension_mapping.items():
            if mc_dim == dimension:
                db_dimension = db_dim
                break
        
        if not db_dimension:
            print(f"警告: 不支持的维度 {dimension}")
            return set()
        
        try:
            # 获取指定维度的所有领地
            lands = self.land_reader.get_lands_by_dimension(db_dimension)
            covered_chunks = set()
            
            print(f"在维度 {db_dimension} 中找到 {len(lands)} 个领地")
            
            for land in lands:
                # 获取领地边界坐标
                min_x, min_z = land['min_x'], land['min_z']
                max_x, max_z = land['max_x'], land['max_z']
                
                # 计算覆盖的区块范围
                start_chunk_x = min_x // 16
                start_chunk_z = min_z // 16
                end_chunk_x = max_x // 16
                end_chunk_z = max_z // 16
                
                # 应用额外保护距离
                protected_start_x = start_chunk_x - extra_protection_distance
                protected_start_z = start_chunk_z - extra_protection_distance
                protected_end_x = end_chunk_x + extra_protection_distance
                protected_end_z = end_chunk_z + extra_protection_distance
                
                # 添加所有被覆盖的区块（包括额外保护范围）
                for cx in range(protected_start_x, protected_end_x + 1):
                    for cz in range(protected_start_z, protected_end_z + 1):
                        covered_chunks.add((cx, cz))
                
                if extra_protection_distance > 0:
                    print(f"领地 '{land['land_name']}' (ID: {land['land_id']}) 覆盖区块 "
                          f"({start_chunk_x}, {start_chunk_z}) 到 ({end_chunk_x}, {end_chunk_z})，"
                          f"额外保护后: ({protected_start_x}, {protected_start_z}) 到 ({protected_end_x}, {protected_end_z})")
                else:
                    print(f"领地 '{land['land_name']}' (ID: {land['land_id']}) 覆盖区块 "
                          f"({start_chunk_x}, {start_chunk_z}) 到 ({end_chunk_x}, {end_chunk_z})")
            
            print(f"总共有 {len(covered_chunks)} 个区块被领地覆盖")
            return covered_chunks
            
        except Exception as e:
            print(f"获取领地覆盖区块时发生错误: {e}")
            return set()
    
    def reset_chunks_except_lands(self, dimension="minecraft:overworld", search_range=50, 
                                 extra_protection_distance=0, dry_run=True, progress_callback=None):
        """
        重置除领地覆盖区块外的所有区块
        
        Args:
            dimension (str): 维度名称，默认为主世界
            search_range (int): 搜索范围（以区块为单位），默认50
            extra_protection_distance (int): 额外保护距离（区块单位），默认为0
            dry_run (bool): 是否为试运行模式，True时不会实际修改世界
            progress_callback: 可选的进度回调函数，格式为 callback(current, total, message)
        
        Returns:
            dict: 包含统计信息的字典
        """
        if not self.level:
            print("错误: 世界未加载")
            return None
        
        # 获取被领地覆盖的区块（包括额外保护距离）
        land_covered_chunks = self.get_chunks_covered_by_lands(dimension, extra_protection_distance)
        
        stats = {
            'total_checked': 0,
            'found_chunks': 0,
            'land_protected_chunks': len(land_covered_chunks),
            'preserved_chunks': 0,
            'reset_chunks': 0,
            'errors': 0
        }
        
        print(f"开始{'试运行' if dry_run else '实际'}重置区块...")
        print(f"领地保护的区块数量: {stats['land_protected_chunks']}")
        if extra_protection_distance > 0:
            print(f"额外保护距离: {extra_protection_distance} 区块")
        print(f"搜索范围: -{search_range} 到 {search_range}")
        print(f"维度: {dimension}")
        print("-" * 50)
        
        # 计算总的检查坐标数（用于进度显示）
        total_coords = (search_range * 2 + 1) ** 2
        
        # 遍历指定范围内的所有可能区块坐标
        for cx in range(-search_range, search_range + 1):
            for cz in range(-search_range, search_range + 1):
                stats['total_checked'] += 1
                
                # 显示进度
                if stats['total_checked'] % 1000 == 0:
                    print(f"已检查 {stats['total_checked']} 个坐标...")
                
                # 调用进度回调
                if progress_callback and stats['total_checked'] % 100 == 0:
                    progress_callback(stats['total_checked'], total_coords, 
                                    f"检查区块 {stats['total_checked']}/{total_coords}")
                
                try:
                    # 尝试获取区块
                    chunk = self.level.get_chunk(cx, cz, dimension)
                    stats['found_chunks'] += 1
                    # 检查是否被领地覆盖
                    if (cx, cz) in land_covered_chunks:
                        stats['preserved_chunks'] += 1
                        if stats['preserved_chunks'] <= 10:  # 只显示前10个保留的区块
                            print(f"保留区块 (领地保护): ({cx}, {cz})")
                        elif stats['preserved_chunks'] == 11:
                            print("... (更多保留区块)")
                    else:
                        # 重置区块
                        if not dry_run:
                            # 正确的区块重置方法：删除后注册空区块
                            try:
                                # 1. 删除现有区块
                                self.level.delete_chunk(cx, cz, dimension)
                                
                                # 2. 注册空区块到历史数据库（防止状态不一致）
                                key = (dimension, cx, cz)
                                if key not in self.level.chunks._history_database:
                                    self.level.chunks._register_original_entry(key, Chunk(cx, cz))
                                    
                            except Exception as e:
                                print(f"重置区块 ({cx}, {cz}) 时发生错误: {e}")
                                stats['errors'] += 1
                                continue
                        stats['reset_chunks'] += 1
                        if stats['reset_chunks'] <= 10:  # 只显示前10个重置的区块
                            print(f"{'将重置' if dry_run else '已重置'}区块: ({cx}, {cz})")
                        elif stats['reset_chunks'] == 11:
                            print("... (更多重置区块)")
                except ChunkDoesNotExist:
                    # 区块不存在，跳过
                    continue
                except ChunkLoadError as e:
                    stats['errors'] += 1
                    print(f"区块加载错误 ({cx}, {cz}): {e}")
                except Exception as e:
                    stats['errors'] += 1
                    print(f"未知错误 ({cx}, {cz}): {e}")
        
        print("-" * 50)
        print("操作完成统计:")
        print(f"检查的坐标总数: {stats['total_checked']}")
        print(f"找到的区块数量: {stats['found_chunks']}")
        print(f"领地保护的区块数量: {stats['land_protected_chunks']}")
        print(f"保留的区块数量: {stats['preserved_chunks']}")
        print(f"{'将重置' if dry_run else '已重置'}的区块数量: {stats['reset_chunks']}")
        print(f"错误数量: {stats['errors']}")
        
        return stats
    
    def reset_chunks_with_preserve(self, preserve_chunks, dimension="minecraft:overworld", 
                                 search_range=50, dry_run=True, progress_callback=None):
        """
        重置区块，保留指定的区块
        
        Args:
            preserve_chunks (list): 要保留的区块坐标列表 [(cx1, cz1), (cx2, cz2), ...]
            dimension (str): 维度名称，默认为主世界
            search_range (int): 搜索范围（以区块为单位），默认50（即-50到50的范围）
            dry_run (bool): 是否为试运行模式，True时不会实际修改世界
            progress_callback: 可选的进度回调函数，格式为 callback(current, total, message)
        
        Returns:
            dict: 包含统计信息的字典
        """
        if not self.level:
            print("错误: 世界未加载")
            return None
        
        preserve_set = set(preserve_chunks)
        stats = {
            'total_checked': 0,
            'found_chunks': 0,
            'preserved_chunks': 0,
            'reset_chunks': 0,
            'errors': 0
        }
        
        print(f"开始{'试运行' if dry_run else '实际'}重置区块...")
        print(f"保留区块: {preserve_chunks}")
        print(f"搜索范围: -{search_range} 到 {search_range}")
        print(f"维度: {dimension}")
        print("-" * 50)
        
        # 计算总的检查坐标数（用于进度显示）
        total_coords = (search_range * 2 + 1) ** 2
        
        # 遍历指定范围内的所有可能区块坐标
        for cx in range(-search_range, search_range + 1):
            for cz in range(-search_range, search_range + 1):
                stats['total_checked'] += 1
                
                # 显示进度
                if stats['total_checked'] % 1000 == 0:
                    print(f"已检查 {stats['total_checked']} 个坐标...")
                
                # 调用进度回调
                if progress_callback and stats['total_checked'] % 100 == 0:
                    progress_callback(stats['total_checked'], total_coords, 
                                    f"检查区块 {stats['total_checked']}/{total_coords}")
                
                try:
                    # 尝试获取区块
                    chunk = self.level.get_chunk(cx, cz, dimension)
                    stats['found_chunks'] += 1
                    
                    # 检查是否在保留列表中
                    if (cx, cz) in preserve_set:
                        stats['preserved_chunks'] += 1
                        print(f"保留区块: ({cx}, {cz})")
                    else:
                        # 重置区块
                        if not dry_run:
                            # 正确的区块重置方法：删除后注册空区块
                            try:
                                # 1. 删除现有区块
                                self.level.delete_chunk(cx, cz, dimension)
                                
                                # 2. 注册空区块到历史数据库（防止状态不一致）
                                key = (dimension, cx, cz)
                                if key not in self.level.chunks._history_database:
                                    self.level.chunks._register_original_entry(key, Chunk(cx, cz))
                                    
                            except Exception as e:
                                print(f"重置区块 ({cx}, {cz}) 时发生错误: {e}")
                                stats['errors'] += 1
                                continue
                        
                        stats['reset_chunks'] += 1
                        print(f"{'将重置' if dry_run else '已重置'}区块: ({cx}, {cz})")
                        
                except ChunkDoesNotExist:
                    # 区块不存在，跳过
                    continue
                except ChunkLoadError as e:
                    stats['errors'] += 1
                    print(f"区块加载错误 ({cx}, {cz}): {e}")
                except Exception as e:
                    stats['errors'] += 1
                    print(f"未知错误 ({cx}, {cz}): {e}")
        
        print("-" * 50)
        print("操作完成统计:")
        print(f"检查的坐标总数: {stats['total_checked']}")
        print(f"找到的区块数量: {stats['found_chunks']}")
        print(f"保留的区块数量: {stats['preserved_chunks']}")
        print(f"{'将重置' if dry_run else '已重置'}的区块数量: {stats['reset_chunks']}")
        print(f"错误数量: {stats['errors']}")
        
        return stats
    
    def save_world(self, progress_callback=None):
        """
        保存世界更改
        
        Args:
            progress_callback: 可选的进度回调函数，格式为 callback(current, total)
        """
        if self.level:
            try:
                print("正在保存世界...")
                
                # 在保存前执行预保存操作（重新计算高度图、光照等）
                print("正在重新计算世界元数据...")
                try:
                    for progress in self.level.pre_save_operation():
                        if progress is not None:
                            print(f"元数据计算进度: {progress*100:.1f}%")
                    print("元数据重新计算完成")
                except Exception as e:
                    print(f"警告: 元数据重新计算失败，但不影响保存: {e}")
                
                # 定义进度回调函数
                def default_progress_callback(chunk_index, chunk_count):
                    if chunk_count > 0:
                        progress = (chunk_index / chunk_count) * 100
                        print(f"保存进度: {chunk_index}/{chunk_count} ({progress:.1f}%)")
                
                # 使用提供的回调函数或默认的进度显示
                callback = progress_callback if progress_callback else default_progress_callback
                
                # 调用带进度回调的保存方法
                self.level.save(progress_callback=callback)
                print("世界保存成功!")
                return True
            except Exception as e:
                print(f"保存世界失败: {e}")
                return False
        return False
    
    def get_chunk_info(self, cx, cz, dimension="minecraft:overworld"):
        """
        获取指定区块的信息
        
        Args:
            cx (int): 区块X坐标
            cz (int): 区块Z坐标
            dimension (str): 维度名称
            
        Returns:
            dict: 区块信息
        """
        if not self.level:
            return None
        
        try:
            chunk = self.level.get_chunk(cx, cz, dimension)
            return {
                'coordinates': (cx, cz),
                'exists': True,
                'changed': chunk.changed,
                'entities_count': len(chunk.entities),
                'block_entities_count': len(chunk.block_entities)
            }
        except ChunkDoesNotExist:
            return {'coordinates': (cx, cz), 'exists': False}
        except Exception as e:
            return {'coordinates': (cx, cz), 'exists': False, 'error': str(e)}


def main():
    """主函数示例"""
    # 使用示例
    world_path = "level"  # 替换为你的世界路径
    land_db_path = "plugins/ARCCore/database.db"  # 替换为你的领地数据库路径
    
    print("=== Minecraft 区块自动重置器 (集成领地保护) ===\n")
    
    # 询问用户是否使用领地保护
    use_land_protection = input("是否使用领地保护功能？(y/N): ").lower() in ['y', 'yes']
    
    if use_land_protection:
        # 创建重置器实例（带领地保护）
        resetter = ChunkAutoResetter(world_path, land_db_path)
    else:
        # 创建重置器实例（不使用领地保护）
        resetter = ChunkAutoResetter(world_path)
    
    # 加载世界
    if not resetter.load_world():
        return
    
    try:
        if use_land_protection and resetter.land_reader:
            # 使用领地保护功能
            print("=== 使用领地保护功能重置区块 ===")
            
            # 获取搜索范围
            try:
                search_range = int(input("请输入搜索范围（默认50）: ") or "50")
            except ValueError:
                search_range = 50
            
            # 首先进行试运行，查看将要进行的操作
            print("\n=== 试运行模式 ===")
            stats = resetter.reset_chunks_except_lands(
                dimension="minecraft:overworld",
                search_range=search_range,
                dry_run=True  # 试运行模式
            )
            
            if stats and stats['reset_chunks'] > 0:
                # 询问用户是否确认执行
                user_input = input(f"\n将要重置 {stats['reset_chunks']} 个区块，"
                                 f"保留 {stats['preserved_chunks']} 个领地保护区块。"
                                 f"是否确认执行？(y/N): ")
                
                if user_input.lower() in ['y', 'yes']:
                    print("\n=== 实际执行模式 ===")
                    # 实际执行重置
                    final_stats = resetter.reset_chunks_except_lands(
                        dimension="minecraft:overworld",
                        search_range=search_range,
                        dry_run=False  # 实际执行
                    )
                    
                    # 保存世界
                    if final_stats and final_stats['reset_chunks'] > 0:
                        print("\n开始保存世界...")
                        resetter.save_world()
                else:
                    print("操作已取消")
            else:
                print("没有需要重置的区块")
        else:
            # 使用手动指定保留区块的方式
            print("=== 手动指定保留区块 ===")
            
            # 定义要保留的区块坐标（玩家建筑所在的区块）
            print("请输入要保留的区块坐标（格式：x,z），每行一个，输入空行结束：")
            preserve_chunks = []
            
            while True:
                coord_input = input("区块坐标: ").strip()
                if not coord_input:
                    break
                try:
                    x, z = map(int, coord_input.split(','))
                    preserve_chunks.append((x, z))
                    print(f"已添加保留区块: ({x}, {z})")
                except ValueError:
                    print("输入格式错误，请使用 x,z 格式")

            # 获取搜索范围
            try:
                search_range = int(input("请输入搜索范围（默认20）: ") or "20")
            except ValueError:
                search_range = 20
            
            # 首先进行试运行，查看将要进行的操作
            print("\n=== 试运行模式 ===")
            stats = resetter.reset_chunks_with_preserve(
                preserve_chunks=preserve_chunks,
                dimension="minecraft:overworld",
                search_range=search_range,
                dry_run=True  # 试运行模式
            )
            
            if stats and stats['reset_chunks'] > 0:
                # 询问用户是否确认执行
                user_input = input(f"\n将要重置 {stats['reset_chunks']} 个区块，是否确认执行？(y/N): ")
                
                if user_input.lower() in ['y', 'yes']:
                    print("\n=== 实际执行模式 ===")
                    # 实际执行重置
                    final_stats = resetter.reset_chunks_with_preserve(
                        preserve_chunks=preserve_chunks,
                        dimension="minecraft:overworld",
                        search_range=search_range,
                        dry_run=False  # 实际执行
                    )
                    
                    # 保存世界
                    if final_stats and final_stats['reset_chunks'] > 0:
                        print("\n开始保存世界...")
                        resetter.save_world()
                else:
                    print("操作已取消")
            else:
                print("没有需要重置的区块")
            
    finally:
        # 关闭世界
        resetter.close_world()


if __name__ == "__main__":
    main()
