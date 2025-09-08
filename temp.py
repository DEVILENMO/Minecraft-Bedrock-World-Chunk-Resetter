import os

def delete_duplicates_by_name(folder_a, folder_b):
    """
    删除文件夹 A 中与文件夹 B 同名的文件。
    
    :param folder_a: 文件夹 A 的路径
    :param folder_b: 文件夹 B 的路径
    """
    # 遍历文件夹 B 的所有文件
    for root_b, _, files_b in os.walk(folder_b):
        for file_name in files_b:
            # 文件夹 B 的文件完整路径
            file_b_path = os.path.join(root_b, file_name)
            
            # 构造文件夹 A 中的同名文件路径
            relative_path = os.path.relpath(file_b_path, folder_b)
            file_a_path = os.path.join(folder_a, relative_path)
            
            # 检查文件夹 A 是否有同名文件
            if os.path.exists(file_a_path):
                print(f"Deleting: {file_a_path}")
                os.remove(file_a_path)  # 删除文件夹 A 中的同名文件

    print("Finished deleting duplicates.")

# 设置文件夹 A 和 B 的路径
folder_a = r"C:\path\to\A"  # 替换为文件夹 A 的实际路径
folder_b = r"C:\path\to\B"  # 替换为文件夹 B 的实际路径

# 运行函数
delete_duplicates_by_name(r'C:\Users\DEVILENMO\AppData\Local\Packages\Microsoft.MinecraftUWP_8wekyb3d8bbwe\LocalState\games\com.mojang\resource_packs\现实主义2.0材质动画\textures\blocks', r'C:\Users\DEVILENMO\AppData\Local\Packages\Microsoft.MinecraftUWP_8wekyb3d8bbwe\LocalState\games\com.mojang\resource_packs\立方构想V40281\textures\blocks')