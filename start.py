import subprocess


if __name__ == '__main__':

    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.CREATE_NO_WINDOW
    credit_main = subprocess.Popen("python -u credit_main.py", creationflags=0x08000000)
    door_main = subprocess.Popen("python -u door_main.py", creationflags=0x08000000)
    auth_main = subprocess.Popen("python -u auth_main.py", creationflags=0x08000000)

    app_main = subprocess.Popen("python -u app_main.py", creationflags=0x08000000)
    # app_main = subprocess.Popen("python -u adult_app_main.py", creationflags=0x08000000)

    app_main.wait()

    credit_main.kill()
    door_main.kill()
    auth_main.kill()