# Made by Kim.Seung.Hwan / ksana1215@interminds.ai
from tkinter import*
import redis
from adult_gui_main import Uipage

rd = redis.StrictRedis(host='localhost', port=6379, db=0)

if __name__ == "__main__":
    rd.flushdb()
    root = Tk()
    app = Uipage(root,rd)
    app.root.mainloop()
