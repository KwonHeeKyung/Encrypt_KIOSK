import subprocess


if __name__ == '__main__':

    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.CREATE_NO_WINDOW
    credit_main = subprocess.Popen("python -u ./src/credit_main.py", creationflags=0x08000000)
    door_main = subprocess.Popen("python -u ./src/door_main.py", creationflags=0x08000000)
    auth_main = subprocess.Popen("python -u ./src/auth_main.py", creationflags=0x08000000)

    # app_main = subprocess.Popen("python -u ./src/app_main.py", creationflags=0x08000000)
    app_main = subprocess.Popen("python -u ./src/adult_app_main.py", creationflags=0x08000000)

    app_main.wait()

    credit_main.kill()
    door_main.kill()
    auth_main.kill()