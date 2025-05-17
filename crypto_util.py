import os
import sys
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
import argparse

def encrypt_file(input_path, output_dir, password):
    """加密文件到指定目录"""
    try:
        # 输入文件验证
        if not os.path.exists(input_path):
            print(f"错误: 输入文件不存在: {input_path}")
            return ""
        if not os.path.isfile(input_path):
            print(f"错误: 输入路径不是文件: {input_path}")
            return ""

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 获取输入文件名并生成输出路径
        filename = os.path.basename(input_path)
        output_path = os.path.join(output_dir, f"{filename}.enc")

        # 生成随机盐值
        salt = get_random_bytes(16)
        # 从密码派生密钥
        key = PBKDF2(password, salt, dkLen=32, count=100000)

        # 生成随机初始化向量
        iv = get_random_bytes(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)

        with open(input_path, 'rb') as f_in:
            plaintext = f_in.read()

            # 填充数据到块大小的倍数
            padding_length = AES.block_size - (len(plaintext) % AES.block_size)
            plaintext += bytes([padding_length]) * padding_length

            ciphertext = cipher.encrypt(plaintext)

        with open(output_path, 'wb') as f_out:
            f_out.write(salt)
            f_out.write(iv)
            f_out.write(ciphertext)

        print(f"加密成功，输出文件: {os.path.abspath(output_path)}")
        return output_path

    except Exception as e:
        print(f"加密过程中出错: {str(e)}")
        return ""

def decrypt_file(input_path, output_dir, password):
    """解密文件到指定目录"""
    try:
        # 输入文件验证
        if not os.path.exists(input_path):
            print(f"错误: 输入文件不存在: {input_path}")
            return ""
        if not os.path.isfile(input_path):
            print(f"错误: 输入路径不是文件: {input_path}")
            return ""

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 获取输入文件名并生成输出路径
        filename = os.path.basename(input_path)
        if filename.endswith('.enc'):
            filename = filename[:-4]
        output_path = os.path.join(output_dir, filename)

        with open(input_path, 'rb') as f_in:
            salt = f_in.read(16)
            iv = f_in.read(16)
            ciphertext = f_in.read()

        # 从密码派生密钥
        key = PBKDF2(password, salt, dkLen=32, count=100000)
        cipher = AES.new(key, AES.MODE_CBC, iv)

        plaintext = cipher.decrypt(ciphertext)

        # 移除填充
        padding_length = plaintext[-1]
        plaintext = plaintext[:-padding_length]

        with open(output_path, 'wb') as f_out:
            f_out.write(plaintext)

        print(f"解密成功，输出文件: {os.path.abspath(output_path)}")
        return output_path

    except Exception as e:
        print(f"解密过程中出错: {str(e)}")
        return ""

def main():
    parser = argparse.ArgumentParser(description="文件加密/解密工具")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # 加密子命令
    encrypt_parser = subparsers.add_parser('encrypt', help='加密文件')
    encrypt_parser.add_argument("-i", "--input", required=True, help="输入文件路径")
    encrypt_parser.add_argument("-o", "--output", required=True, help="输出文件夹路径")
    encrypt_parser.add_argument("-p", "--password", required=True, help="加密密码")

    # 解密子命令
    decrypt_parser = subparsers.add_parser('decrypt', help='解密文件')
    decrypt_parser.add_argument("-i", "--input", required=True, help="输入文件路径")
    decrypt_parser.add_argument("-o", "--output", required=True, help="输出文件夹路径")
    decrypt_parser.add_argument("-p", "--password", required=True, help="解密密码")

    args = parser.parse_args()

    if args.command == 'encrypt':
        encrypt_file(args.input, args.output, args.password)
    elif args.command == 'decrypt':
        decrypt_file(args.input, args.output, args.password)

if __name__ == "__main__":
    main()

    # 一些使用例子:
    # 加密文件: python crypto_util.py encrypt -i /path/to/input_file -o /path/to/output_folder -p mypassword
    # 解密文件: python crypto_util.py decrypt -i /path/to/input_file.enc -o /path/to/output_folder -p mypassword
