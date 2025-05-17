import os
import sys
import argparse
import pyzipper
from tqdm import tqdm

# 此函数用于合并分卷文件，支持可选的压缩密码。
# 参数:
# output_dir: 分卷文件所在的目录路径。
# base_name: 分卷文件的基础名称（不包含扩展名）。
# password: 压缩文件的加密密码，可选参数，默认为 None，表示不进行解密。

# 输入和输出文件名称说明:
# 输入文件: 分卷文件，格式为 <base_name>_part<X>.zip，其中 X 为分卷序号。
# 输出文件: 合并后的完整文件，格式为 <base_name>_merged.zip。
# 此函数会按照分卷序号顺序合并文件，并验证合并后的文件是否正确。
def merge_chunks(output_dir, base_name, password=None):
    """合并分卷文件"""
    merged_path = os.path.join(output_dir, f"{base_name}_merged.zip")
    try:
        # 先检查所有分卷文件
        part_files = []
        part_counter = 1
        while True:
            part_path = os.path.join(output_dir, f"{base_name}_part{part_counter}.zip")
            if not os.path.exists(part_path):
                break
            part_files.append(part_path)
            part_counter += 1

        if not part_files:
            print(f"错误: 未找到任何分卷文件: {base_name}_part*.zip")
            sys.exit(1)

        # 合并所有分卷文件
        with open(merged_path, 'wb') as merged_file:
            for part_path in part_files:
                with open(part_path, 'rb') as part_file:
                    merged_file.write(part_file.read())

        # 验证合并后的文件
        if password:
            with pyzipper.AESZipFile(merged_path) as zip_file:
                zip_file.setpassword(password.encode())
                zip_file.testzip()
        else:
            with pyzipper.ZipFile(merged_path) as zip_file:
                zip_file.testzip()

        print(f"合并完成，文件路径: {os.path.abspath(merged_path)}")
        return merged_path

    except Exception as e:
        if os.path.exists(merged_path):
            os.remove(merged_path)
        print(f"合并过程中出错: {str(e)}")
        sys.exit(1)


# 此函数用于压缩指定的文件夹，支持可选的分卷和加密功能。
# 参数:
# input_path: 要压缩的文件夹的路径。
# output_dir: 压缩文件的输出目录路径。
# chunk_size: 分卷大小（以字节为单位），可选参数，默认为 None，表示不进行分卷。
# password: 压缩文件的加密密码，可选参数，默认为 None，表示不进行加密。

# 这里的分卷是单纯的先压缩成一个文件再按照 size 切分

# 输出文件名称规则：
# 若不进行分卷，输出文件名为输入文件夹名称加上 .zip 后缀；
# 若进行分卷，输出文件名为输入文件夹名称加上 _partX.zip 后缀，其中 X 为分卷序号。
def compress_folder(input_path, output_dir, chunk_size=None, password=None):
    """压缩文件夹，可选分卷和加密"""
    if not os.path.exists(input_path):
        print(f"错误: 输入路径不存在: {input_path}")
        sys.exit(1)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    base_name = os.path.basename(input_path.rstrip(os.sep))
    temp_zip = os.path.join(output_dir, f"{base_name}_temp.zip")

    try:
        # 先压缩成单个临时文件
        with pyzipper.AESZipFile(temp_zip, 'w', compression=pyzipper.ZIP_DEFLATED) as zip_file:
            if password:
                zip_file.setpassword(password.encode())
                zip_file.setencryption(pyzipper.WZ_AES, nbits=256)
                # print(f"已设置AES-256加密密码: {password}")

            total_files = sum(len(files) for _, _, files in os.walk(input_path))
            with tqdm(total=total_files, desc="压缩进度") as pbar:
                for root, _, files in os.walk(input_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, input_path)
                        zip_file.write(file_path, rel_path)
                        pbar.update(1)

        if chunk_size:
            # 分割压缩文件
            zip_counter = 1
            with open(temp_zip, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    part_name = f"{base_name}_part{zip_counter}.zip"
                    part_path = os.path.join(output_dir, part_name)
                    with open(part_path, 'wb') as part_file:
                        part_file.write(chunk)
                    zip_counter += 1
            os.remove(temp_zip)  # 删除临时文件
            print(f"压缩完成，共生成 {zip_counter-1} 个分卷文件; 输出路径: {os.path.abspath(output_dir)}")

            # 合并分卷文件(这里用于测试)
            # merge_chunks(output_dir, base_name, password)
        else:
            # 重命名为最终文件名
            final_zip = os.path.join(output_dir, f"{base_name}.zip")
            os.rename(temp_zip, final_zip)
            print(f"压缩完成，生成单个压缩文件; 输出路径: {os.path.abspath(final_zip)}")

    except Exception as e:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)
        print(f"压缩过程中出错: {str(e)}")
        sys.exit(1)

# 此函数用于解压指定的文件夹，支持自动处理分卷文件（先合并）。
# 参数:
# input_path: 要解密的文件夹的路径。
# output_dir: 解密文件的输出目录路径。
# password: 解密文件的密码，可选参数，默认为 None，表示不进行解密。
def decompress_folder(input_path, output_dir, password=None):
    """解密文件夹，自动处理分卷文件"""
    if not os.path.exists(input_path):
        print(f"错误: 输入路径不存在: {input_path}")
        sys.exit(1)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    is_chunked = False
    base_name = None
    # 检查输入路径是否为文件夹
    if os.path.isdir(input_path):
        for filename in os.listdir(input_path):
            if filename.endswith('.zip') and '_part' in filename:
                is_chunked = True
                # 提取基础名称(去掉_partX.zip)
                base_name = filename.split('_part')[0]
                break

    try:
        if is_chunked:
            # 先合并分卷
            merged_path = merge_chunks(input_path, base_name, password)
            input_path = merged_path  # 更新输入路径为合并后的文件

        # 解压文件
        with pyzipper.AESZipFile(input_path) as zip_file:
            if password:
                zip_file.setpassword(password.encode())
            zip_file.extractall(output_dir)

        print(f"解压缩完成，输出路径: {os.path.abspath(output_dir)}")
        return output_dir

    except Exception as e:
        print(f"解压缩过程中出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="文件/文件夹的压缩(分卷)工具")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # 压缩子命令
    compress_parser = subparsers.add_parser('compress', help='压缩文件/文件夹')
    compress_parser.add_argument("-i", "--input", required=True, help="输入文件或文件夹路径")
    compress_parser.add_argument("-s", "--size", type=int, help="分卷大小(字节，可选)")
    compress_parser.add_argument("-o", "--output", required=True, help="输出目录路径")
    compress_parser.add_argument("-p", "--password", help="压缩密码(可选)")

    # 解压子命令
    decompress_parser = subparsers.add_parser('decompress', help='解压文件/文件夹')
    decompress_parser.add_argument("-i", "--input", required=True, help="输入文件路径")
    decompress_parser.add_argument("-o", "--output", required=True, help="输出目录路径")
    decompress_parser.add_argument("-p", "--password", help="解压密码(可选)")

    args = parser.parse_args()

    if args.command == 'compress':
        compress_folder(
            input_path=args.input,
            output_dir=args.output,
            chunk_size=args.size,
            password=args.password
        )
    elif args.command == 'decompress':
        decompress_folder(
            input_path=args.input,
            output_dir=args.output,
            password=args.password
        )

    # 使用例子:
    # 压缩:
    # 不进行分卷，不加密: python compress.py compress -i /path/to/input_folder -o /path/to/output_folder
    # 进行分卷，不加密: python compress.py compress -i /path/to/input_folder -o /path/to/output_folder -s 1048576  # 示例分卷大小为 1MB（1048576 字节）
    # 不进行分卷，加密: python compress.py compress -i /path/to/input_folder -o /path/to/output_folder -p mypassword
    # 进行分卷，加密: python compress.py compress -i /path/to/input_folder -o /path/to/output_folder -s 1048576 -p mypassword  # 示例分卷大小为 1MB（1048576 字节）

    # 不进行分卷，输出文件的名字: <input_folder>.zip
    # 进行分卷后，输出文件的名字: <input_folder>_part<X>.zip，其中 X 为分卷序号。

    # 解压:
    # 不进行分卷的，不加密的: python compress.py decompress -i /path/to/input_zip.zip -o /path/to/output_folder
    # 进行分卷的，不加密的: python compress.py decompress -i /path/to/input_dir -o /path/to/output_folder
    # 不进行分卷的，加密的: python compress.py decompress -i /path/to/input_zip.zip -o /path/to/output_folder -p mypassword
    # 进行分卷的，加密的: python compress.py decompress -i /path/to/input_dir -o /path/to/output_folder -p mypassword
