import os
import argparse

# 실행방법 : python .\encrypt.py -target C:\Users\kwon\Desktop\ProjectTest\KIOSK_IMD\src


parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)


def get_arguments():
    parser.add_argument("-target", "--target",
                        help="input path of module\n",
                        type=str, required=True)

    _args = parser.parse_args()

    return _args


args = get_arguments()

def search(dirname):
    try:
        filenames = os.listdir(dirname)
        for filename in filenames:
            full_filename = os.path.join(dirname, filename)
            if os.path.isdir(full_filename):
                # search(full_filename)
                pass
            else:
                ext = os.path.splitext(full_filename)[-1]
                if ext == '.py':
                    if filename == 'config.py' or filename == 'encrypt.py' or filename == 'start.py': pass
                    elif filename == 'auth_main.py': pass # DLL때문에 오류나서 auth_main.py도 암호화하지 않음.
                    else:
                        print(filename)
                        os.system("pyarmor obfuscate --exact " + full_filename)

    except PermissionError:
        pass


if __name__ == '__main__':
    search(args.target)
