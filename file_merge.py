import os
import sys
import argparse
from itertools import cycle

def merge_files(data_dir, img_dir, output_dir):
    """合并数据文件和图片文件"""
    # 检查输入目录
    if not os.path.exists(data_dir):
        print(f"错误: 数据目录不存在 - {data_dir}")
        sys.exit(1)
    if not os.path.exists(img_dir):
        print(f"错误: 图片目录不存在 - {img_dir}")
        sys.exit(1)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 获取所有数据文件（过滤文件夹）
    data_files = [f for f in os.listdir(data_dir)
                 if os.path.isfile(os.path.join(data_dir, f))]

    # 获取所有PNG图片文件
    img_files = [f for f in os.listdir(img_dir)
                if f.lower().endswith('.png') and
                os.path.isfile(os.path.join(img_dir, f))]

    if not data_files:
        print(f"错误: 目录 {data_dir} 目录中没有文件")
        sys.exit(1)

    if not img_files:
        print(f"错误: 目录 {img_dir} 目录中没有PNG文件")
        sys.exit(1)

    img_cycle = cycle(img_files)  # 创建循环迭代器

    for data_file in data_files:
        img_file = next(img_cycle)
        data_name, data_ext = os.path.splitext(data_file)

        # 构建输出文件名(基于图片名)
        output_name = os.path.splitext(img_file)[0]
        output_ext = '.png'
        output_path = os.path.join(output_dir, f"{output_name}{output_ext}")

        # 处理文件名冲突
        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{output_name}_{counter}{output_ext}")
            counter += 1

        try:
            # 读取文件内容
            with open(os.path.join(data_dir, data_file), 'rb') as f:
                data_content = f.read()
            with open(os.path.join(img_dir, img_file), 'rb') as f:
                img_content = f.read()

            # 将源文件名信息添加到数据内容前
            file_info = f"{data_file}\n".encode('utf-8')
            # 打印文件名
            print(f"合并数据文件: {data_file}")

            merged_data = file_info + data_content

            # 写入合并文件
            with open(output_path, 'wb') as f:
                f.write(img_content)
                f.write(merged_data)

        except Exception as e:
            print(f"文件合并失败: {str(e)}")
            sys.exit(1)

def recover_files(input_dir, output_dir):
    """恢复原始文件"""
    # 检查输入输出目录
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录不存在 - {input_dir}")
        sys.exit(1)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    data_output = os.path.join(output_dir, 'data')
    img_output = os.path.join(output_dir, 'images')

    # 创建输出目录
    os.makedirs(data_output, exist_ok=True)
    os.makedirs(img_output, exist_ok=True)

    # 获取所有合并文件
    merge_files = [f for f in os.listdir(input_dir)
                if f.lower().endswith('.png') and
                os.path.isfile(os.path.join(input_dir, f))]

    if not merge_files:
        print(f"错误: 目录 {input_dir} 中没有 png 文件")
        sys.exit(1)

    for merge_file in merge_files:
        merge_path = os.path.join(input_dir, merge_file)
        base_name = os.path.splitext(merge_file)[0]

        try:
            with open(merge_path, 'rb') as f:
                content = f.read()

                # 查找PNG文件结尾
                png_end = content.find(b'IEND')
                if png_end == -1:
                    print(f"无效的合并文件: {merge_file}")
                    sys.exit(1)

                # 分离图片和数据
                img_content = content[:png_end+8]
                data_content = content[png_end+8:]

                # 提取源文件名(第一行)
                first_newline = data_content.find(b'\n')
                if first_newline == -1:
                    print(f"无效的数据格式: {merge_file}")
                    sys.exit(1)

                original_name = data_content[:first_newline].decode('utf-8')
                # 打印文件名
                print(f"恢复文件: {original_name}")

                actual_data = data_content[first_newline+1:]

                # 保存恢复的文件(使用原始文件名)
                with open(os.path.join(data_output, original_name), 'wb') as f:
                    f.write(actual_data)

                # 保存恢复的图片
                with open(os.path.join(img_output, f"{base_name}.png"), 'wb') as f:
                    f.write(img_content)

        except Exception as e:
            print(f"文件恢复失败: {str(e)}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="文件合并与恢复工具")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # 合并命令
    merge_parser = subparsers.add_parser('merge', help='合并文件')
    merge_parser.add_argument('-d', '--data', required=True, help='数据文件目录')
    merge_parser.add_argument('-i', '--images', required=True, help='png 图片目录')
    merge_parser.add_argument('-o', '--output', required=True, help='输出目录')

    # 恢复命令
    recover_parser = subparsers.add_parser('recover', help='恢复文件')
    recover_parser.add_argument('-i', '--input', required=True, help='输入目录')
    recover_parser.add_argument('-o', '--output', required=True, help='输出目录')

    args = parser.parse_args()

    try:
        if args.command == 'merge':
            merge_files(args.data, args.images, args.output)
        elif args.command == 'recover':
            recover_files(args.input, args.output)
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()

    # 功能说明:
    # 合并文件: 从指定的数据文件目录和图片目录中，将每个数据文件与相应的PNG图片文件合并成一个新的PNG文件。
    # 恢复文件: 从指定的输入目录中，恢复合并后的PNG文件，将其分离为原始的数据文件和图片文件。

    # 一些使用例子:
    # 合并文件: python merge.py merge -d /path/to/data_dir -i /path/to/img_dir -o /path/to/output_dir
    # 恢复文件: python merge.py recover -i /path/to/input_dir -o /path/to/output_dir

    # 注意：
    # 提供的图片必须是 png 格式。合并后的图片文件仍然可以打开。
    # 图片数量可以小于数据文件数量。生成的合并文件会以图片文件名命名。
    # 如果图片名字有重复则会自动加计数后缀。
