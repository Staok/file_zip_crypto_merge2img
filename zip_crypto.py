import argparse
import os
import sys
from compress_util import compress_folder, decompress_folder
from crypto_util import encrypt_file, decrypt_file

def parse_size(size_str):
    """将带单位的容量字符串转换为整数字节数"""
    units = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                size_value = float(size_str[:-len(unit)])
                if not size_value.is_integer():
                    print(f"错误: 分包大小必须是整数: {size_str}")
                    sys.exit(1)
                return int(size_value) * multiplier
            except ValueError:
                print(f"错误: 无效的分包大小: {size_str}")
                sys.exit(1)
    print("错误: 单位必须是KB、MB或GB")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="文件/文件夹(分卷)(加密)压缩并附图工具")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # 加密子命令
    zip_encrypt_parser = subparsers.add_parser('zip_encrypt', help='压缩并加密文件')
    zip_encrypt_parser.add_argument("-i", "--input", required=True, help="输入文件或文件夹路径")
    zip_encrypt_parser.add_argument("-s", "--size", type=parse_size, help="分包大小(如100MB, 1GB), 必须为整数")
    zip_encrypt_parser.add_argument("-p", "--password", help="压缩密码(可选)")
    zip_encrypt_parser.add_argument("-c", "--crypto", help="加密密码(可选)")
    zip_encrypt_parser.add_argument("-o", "--output", required=True, help="输出文件夹路径")

    # 解密子命令
    zip_decrypt_parser = subparsers.add_parser('zip_decrypt', help='解密并解压文件')
    zip_decrypt_parser.add_argument("-i", "--input", required=True, help="输入文件路径")
    zip_decrypt_parser.add_argument("-c", "--crypto", help="加密密码(可选)")
    zip_decrypt_parser.add_argument("-p", "--password", help="解压密码(可选)")
    zip_decrypt_parser.add_argument("-o", "--output", required=True, help="输出文件夹路径")

    try:
        args = parser.parse_args()
    except SystemExit:
        sys.exit(1)
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)

    print("输入路径:", args.input)
    # 修改为条件打印size参数
    if hasattr(args, 'size'):
        print("分包大小(字节):", args.size if args.size else "none")
    print("压缩/解压密码:", args.password if args.password else "none")
    print("加密/解密密码:", args.crypto if args.crypto else "none")
    print("输出文件夹:", args.output)

    if args.command == 'zip_encrypt':
         # 调用compress_util.py中的压缩函数
        compress_folder(
            input_path=args.input,
            output_dir=args.output,
            chunk_size=args.size,
            password=args.password
        )

        # 如果使用了加密参数
        # 调用encrypt_file加密函数，对上面压缩输出的文件进行加密
        # 注意检查是否使用了分卷功能，如果使用则要对每个输出文件进行加密
        if args.crypto:
            output_dir = args.output
            if args.size:
                # 对每个分卷文件进行加密
                for filename in os.listdir(output_dir):
                    if filename.endswith('.zip'):
                        input_path = os.path.join(output_dir, filename)
                        encrypt_file(input_path, output_dir, args.crypto)
                        # 删除原始压缩文件
                        os.remove(input_path)
            else:
                # 对单个压缩文件进行加密
                input_path = os.path.join(output_dir, os.path.basename(args.input) + '.zip')
                encrypt_file(input_path, output_dir, args.crypto)
                # 删除原始压缩文件
                os.remove(input_path)

        print("完成")
        sys.exit(0)

    elif args.command == 'zip_decrypt':
        # 如果使用了解密密码参数, 调用decrypt_file解密
        decompress_file_name = args.input
        if args.crypto:
            input_dir = args.input
            # 如果是文件直接解密
            if os.path.isfile(input_dir):
                decompress_file_name = decrypt_file(input_dir, os.path.dirname(input_dir), args.crypto)
            else:
                # 如果是文件夹则遍历解密
                for filename in os.listdir(input_dir):
                    if filename.endswith('.enc'):
                        input_path = os.path.join(input_dir, filename)
                        decompress_file_name = decrypt_file(input_path, input_dir, args.crypto)
                        # 保留原始加密文件

        # 如果 decompress_file_name 文件名 包含有 "part", 说明是分卷文件，则 decompress_file_name 改为使用 args.input
        if '_part' in decompress_file_name:
            decompress_file_name = args.input

        # 调用decompress_folder解压函数
        decompress_folder(
            decompress_file_name,
            output_dir=args.output,
            password=args.password
        )

        print("完成")
        sys.exit(0)

if __name__ == "__main__":
    main()

    # 功能说明:
    # 1. 压缩（可选使用压缩密码）文件或文件夹: 可以选择是否进行分卷和对压缩后的文件再进行加密处理。
    # 2. （解密并）解压缩文件（或一堆分卷文件），恢复如初。

    # 确保本地 python 环境已经安装了库
    # pip install argparse tqdm pyzipper pycryptodome

    # 一些使用例子:

    # 获取帮助信息: python zip_crypto -h
    # 加密解密的帮助信息: python zip_crypto zip_encrypt -h 或 python zip_crypto zip_decrypt -h

    # 压缩并加密给定文件夹，使用分卷 50KB，压缩加密密码为 aaa，在此基础上再加一层文件加密，密码为 abc
    # python zip_crypto zip_encrypt -i <input_dir> -o <output_dir> -s 50KB -p aaa -c abc

    # 上面的例子的解压
    # input_dir 为压缩加密产物的文件夹, 保持这个文件夹除了压缩产物之外没别的以保证分卷文件名称检查不出错
    # python.exe .\zip_crypto zip_decrypt -i <input_dir> -o <output_dir>  -p aaa -c abc

    # 注意:
    # 如果加密不使用分卷，则输出为一个文件，则解密的时候，指定 -i 为这个文件即可
