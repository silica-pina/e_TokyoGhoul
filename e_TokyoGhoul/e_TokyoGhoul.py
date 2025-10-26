
from http.client import SWITCHING_PROTOCOLS
import time
from multiprocessing import Process, Value
import tkinter as tk
import time
import numpy as np
from numpy.random import rand

#乱数
#li_normal = list(range(79999)) # 当たり400個 
#li_st = list(range(76240)) # 当たり400個 

#ずっと動かすメイン抽選
def roulette_normal(NORMAL,FLG):
    rng = np.random.default_rng()
    while True:
        if FLG.value == 0:
            NORMAL.value = rng.integers(0,79998)
        else:
            time.sleep(0.001) # 休憩

def roulette_st(ST,FLG):
    rng = np.random.default_rng()
    while True:
        if FLG.value == 1:
            ST.value = rng.integers(0,76239)
        else:
            time.sleep(0.001) # 休憩


#tkinterで状態や乱数、出玉などを表示する
random = 1
cnt = 0
now = 0 #現在の差玉
ren = 0 #連荘数
tokuzu2 = 0 #保留数
def output(NORMAL,ST,FLG):
    global random,cnt
    def key_event(e,NORMAL,ST,FLG):
        global random,cnt
        if e.keysym == "Down":
            if FLG.value == 0:
                random = NORMAL.value
                cnt += 1
                label4["text"] = "回転数：" + str(cnt)
                label7["text"] = "通常"
                normal()
            if FLG.value == 1:
                random = ST.value
                cnt += 1
                label4["text"] = "回転数：" + str(cnt)
                label7["text"] = "ST中"
                rush()

    #抽選機の乱数を表示
    def see_n():
        if FLG.value == 0:
            label2["text"] = NORMAL.value
            root.after(1,see_n)
        else:
            label2["text"] = ST.value
            root.after(1,see_n)

    def normal(): #通常
        global random, cnt, now, ren
        if random <= 1:
            FLG.value = 1
            now += 270
            cnt = 0
            ren += 1
            label3["text"] = "ST"
            label5["text"] = "差玉：" + str(now)
            label8["text"] = "連荘数：" + str(ren)
        elif random < 200:
            now += 270
            cnt = 0
            label3["text"] = "喰種CHARGE"
            label5["text"] = "差玉：" + str(now)
            label8["text"] = "連荘数：" + str(ren)
        elif random < 300:
            now += 1400
            cnt = 0
            label3["text"] = "通常"
            label5["text"] = "差玉：" + str(now)
            label8["text"] = "連荘数：" + str(ren)
        elif random < 400:
            FLG.value = 1
            now += 1400
            cnt = 0
            ren += 1
            label3["text"] = "ST"
            label5["text"] = "差玉：" + str(now)
            label8["text"] = "連荘数：" + str(ren)
        else:
            now -= 15
            label3["text"] = "ハズレ"
            label5["text"] = "差玉：" + str(now)


    def rush():#ST
        global random,cnt,now,ren,tokuzu2
        if tokuzu2 > 0:
            now += 1390
            tokuzu2 -= 1
            label5["text"] = "差玉：" + str(now)
            if random >= 2287:
                if tokuzu2 == 0:
                    ren += 1
                    cnt = 0
                    label8["text"] = "連荘数：" + str(ren)
            else: #3%
                if tokuzu2 == 0:
                    tokuzu2 = 2
        elif cnt < 130:
            if random < 800:
                tokuzu2 = 2
                label3["text"] = "当たり"
            else:
                label3["text"] = "ハズレ"
                label6["text"] = "残り:" + str(130-cnt)
        else:
            ren = 0
            now -= 15
            FLG.value = 0
            label3["text"] = "ST終了"
            label5["text"] = "差玉：" + str(now)
            label6["text"] = "残り:" + str(130-cnt)
            label8["text"] = "連荘数：" + str(ren)

    root = tk.Tk()
    root.title("eTokyoGhoul ↓キーで抽選")
    root.geometry("800x900")
    root.bind("<KeyPress>",lambda e:key_event(e,NORMAL,ST,FLG))
    label2 = tk.Label(font=("Ubunt Mono",100))
    label3 = tk.Label(font=("Ubunt Mono",100))
    label4 = tk.Label(font=("Ubunt Mono",80)) #回転数
    label5 = tk.Label(font=("Ubunt Mono",80)) #差玉
    label6 = tk.Label(font=("Ubunt Mono",80)) #STや時短の残り回転数
    label7 = tk.Label(font=("Ubunt Mono",80)) #状態
    label8 = tk.Label(font=("Ubunt Mono",80)) #連荘数
    label2.pack()
    label3.pack()
    label4.pack()
    label5.pack()
    label6.pack()
    label7.pack()
    label8.pack()
    see_n()
    root.mainloop()

#プロセスを動かす
if __name__=="__main__":
    NORMAL = Value("i",0) #iはintを表す
    ST = Value("i",0)
    FLG = Value("i",0)

    FLG.value = 0 #初期化 状態を表す 0:通常、1：ST

    p1 = Process(target=roulette_normal, args=(NORMAL,FLG))
    p2 = Process(target=roulette_st, args=(ST,FLG))
    p3 = Process(target=output, args=(NORMAL,ST,FLG))
    p1.start()
    p2.start()
    p3.start()
    p1.join()
    p2.join()
    p3.join()