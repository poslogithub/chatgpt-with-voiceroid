import json
import logging
import logging.handlers
import os
import re
import sys
import tkinter
#import tkinter.simpledialog as simpledialog
import wave
import webbrowser
from datetime import datetime
from tkinter import Frame, filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

import psutil
import pyaudio
import speech_recognition as sr
from revChatGPT.V1 import Chatbot

from seikasay2 import SeikaSay2


class ProcessName:
    ASSISTANT_SEIKA = "AssistantSeika.exe"
    SEIKA_SAY2 = "SeikaSay2.exe"

class ConfigKey:
    SEIKA_SAY2_PATH = "seikaSay2Path"
    SPEAKER = "speaker"
    CID = "cid"
    NAME = "name"
    SESSION_URL = "sessionUrl"
    ACCESS_TOKEN = "access_token"


class ConfigValue:
    SPEAKER = "speaker"


class ChatgptWithVoiceroid(Frame):
    def __init__(self, master=None):
        super().__init__(master)

        # 定数
        self.CONFIG_FILE = ".config\\config.json"
        self.LOG_FILE = os.path.basename(__file__).split(".")[0]+".log"
        self.APP_NAME = "ChatGPTの回答をVOICEROIDとかに喋ってもらうやつ"

        # 変数
        self.config = {
            ConfigKey.SEIKA_SAY2_PATH : ".\\"+ProcessName.SEIKA_SAY2,
            ConfigKey.SPEAKER : {
                ConfigKey.CID : 0,
                ConfigKey.NAME : ""
            },
            ConfigKey.SESSION_URL : "https://chat.openai.com/api/auth/session",
            ConfigKey.ACCESS_TOKEN : ""
        }
        self.cids = []
        self.speakers = []
        self.speaker_obj = {}

        # GUI
        self.master.title(self.APP_NAME)
        self.master.geometry("640x400")
        self.sv_message = tkinter.StringVar()
        self.master_frame = tkinter.Frame(self.master)
        self.master_frame.pack()
        self.master_text = ScrolledText(self.master_frame, state='disabled')
        self.master_text.pack()
        self.entry_message = ttk.Entry(self.master_frame, textvariable=self.sv_message)
        self.entry_message.insert(0, "ここにメッセージを入力してEnterを押す")
        self.entry_message.bind('<Return>', self.send_message)
        self.entry_message.pack(fill='x', padx=0, pady=5)
        self.master_quit = ttk.Button(self.master_frame, text="　終了　", command=self.master_frame_quit)
        self.master_quit.pack(fill='x', padx=10, pady=5, side = 'right')
        self.master_save = ttk.Button(self.master_frame, text="　保存　", command=self.master_frame_save)
        self.master_save.pack(fill='x', padx=10, pady=5, side = 'right')

        # logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        must_rollover = False
        if os.path.exists(self.LOG_FILE):  # check before creating the handler, which creates the file
            must_rollover = True
        rotating_handler = logging.handlers.RotatingFileHandler(self.LOG_FILE, backupCount=10)
        rotating_handler.setLevel(logging.DEBUG)
        if must_rollover:
            try:
                rotating_handler.doRollover()
            except PermissionError:
                print("警告: {} のローテーションに失敗しました。ログファイルが出力されません。".format(self.LOG_FILE))
        self.logger.addHandler(stream_handler)
        self.logger.addHandler(rotating_handler)

        # load config
        self.logger.info("Loading {}".format(self.CONFIG_FILE))
        if self.load_config():
            self.logger.info("Loading {}: OK".format(self.CONFIG_FILE))
        else:
            self.logger.info("Loading {}: NG".format(self.CONFIG_FILE))

    def open_access_token_url(self):
        webbrowser.open(self.config.get(ConfigKey.SESSION_URL))
    
    def log_message(self, message, speaker=None):
        if not speaker:
            speaker = "あなた"
        log = speaker+"「"+message+"」"
        self.logger.info(log)
        self.master_text.config(state="normal")
        self.master_text.insert("end", log+"\n")
        self.master_text.yview_moveto(1)
        self.master_text.config(state="disabled")

    def send_message(self, event):
        message = self.sv_message.get()
        self.log_message(message)
        for data in self.chatbot.ask(message):
            resp = data["message"]

        self.log_message(resp, self.get_speaker_name(self.config.get(ConfigKey.SPEAKER).get(ConfigKey.CID)))
        self.speak(self.config.get(ConfigKey.SPEAKER).get(ConfigKey.CID), resp)

    def master_frame_save(self):
        filename = "ChatGPT-With-Voiceroid_{}.txt".format(datetime.now().strftime('%Y%m%d_%H%M%S'))
        path = filedialog.asksaveasfilename(filetype=[("テキストファイル","*.txt")], initialdir=os.getcwd(), initialfile=filename)
        if path:
            with open(path, 'a', encoding="utf_8_sig") as af:
                af.write(self.master_text.get("1.0","end"))

    def master_frame_quit(self):
        if messagebox.askyesno("ChatGPTの回答をVOICEROIDとかに喋ってもらうやつ 終了確認", "終了してよろしいですか？"):
            self.master.destroy()

    def load_config(self, config_file=None):
        if not config_file:
            config_file = self.CONFIG_FILE
        if not os.path.exists(config_file):
            self.save_config(config_file, self.config)
        with open(config_file if config_file else self.CONFIG_FILE, 'r', encoding="utf_8_sig") as rf:
            self.config = json.load(rf)
        return self.config

    def save_config(self, config_file=None, config=None):
        with open(config_file if config_file else self.CONFIG_FILE, 'w', encoding="utf_8_sig") as wf:
            json.dump(config if config else self.config, wf, indent=4, ensure_ascii=False)

    def process_running_check(self, process_postfix):
        for proc in psutil.process_iter():
            try:
                if proc.exe().endswith(process_postfix):
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return None

    def speak(self, cid, text):
        if cid and text:
            return self.seikasay2.speak(cid=cid, text=text)
        else:
            return None
            
    def get_speaker_list(self):
        self.cids, self.speakers = self.seikasay2.list()
        return self.cids, self.speakers

    def get_speaker_name(self, cid):
        for speaker in self.speakers:
            if speaker.startswith(cid):
                try:
                    return re.sub("^"+cid, "", speaker).split(" - ")[0].strip()
                except:
                    return None
        return None

    # 多分いらない
    def openWave(self):
        wf = wave.open("./test.wav", "r")

        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        chunk = 1024
        data = wf.readframes(chunk)
        while data != b'':
            stream.write(data)
            data = wf.readframes(chunk)
        stream.close()
        p.terminate()

    def open_config_window(self):
        speaker_index = self.cids.index(self.config.get(ConfigKey.SPEAKER).get(ConfigKey.CID))
        self.config_window = tkinter.Toplevel(self)
        self.config_window.title(self.APP_NAME + " - 設定ウィンドウ")
        self.config_window.geometry("560x120")
        self.config_window.grab_set()   # モーダルにする
        self.config_window.focus_set()  # フォーカスを新しいウィンドウをへ移す
        self.config_window.transient(self.master)   # タスクバーに表示しない
        self.config_frame = ttk.Frame(self.config_window)
        self.config_frame.grid(row=0, column=0, sticky=tkinter.NSEW, padx=5, pady=5)
        self.sv_access_token = tkinter.StringVar()
        self.sv_access_token.set(self.config.get(ConfigKey.ACCESS_TOKEN))
        self.sv_seikasay2_path = tkinter.StringVar()
        self.sv_seikasay2_path.set(self.config.get(ConfigKey.SEIKA_SAY2_PATH))
        self.sv_speaker = tkinter.StringVar()
        combobox_width = 44
        label_access_token = ttk.Label(self.config_frame, text="Access token: ", anchor="w")
        label_access_token.grid(row=0, column=0, sticky=tkinter.W + tkinter.E, padx=5, pady=5)
        entry_access_token = ttk.Entry(self.config_frame, width=60, textvariable=self.sv_access_token)
        entry_access_token.grid(row=0, column=1, sticky=tkinter.W + tkinter.E, padx=5, pady=5)
        button_access_token = ttk.Button(self.config_frame, text="　開く　", command=self.open_access_token_url)
        button_access_token.grid(row=0, column=2, sticky=tkinter.W + tkinter.E, padx=5, pady=5)
        label_speaker = ttk.Label(self.config_frame, text="話者: ", anchor="w")
        label_speaker.grid(row=1, column=0, sticky=tkinter.W + tkinter.E, padx=5, pady=5)
        combobox_speaker = ttk.Combobox(self.config_frame, width=combobox_width, values=self.speakers, textvariable=self.sv_speaker, state="readonly")
        combobox_speaker.current(speaker_index)
        combobox_speaker.grid(row=1, column=1, sticky=tkinter.W + tkinter.E, padx=5, pady=5)
        button_ok = ttk.Button(self.config_frame, text="　開始　", command=self.config_window_ok)
        button_ok.grid(row=2, column=2, sticky=tkinter.E, padx=5, pady=10)
        self.wait_window(self.config_window)

    def config_window_seikasay2(self):
        path = filedialog.askopenfilename(filetype=[("実行ファイル","*.exe")], initialdir=os.getcwd())
        if path:
            self.sv_seikasay2_path.set(path)

    def config_window_ok(self):
        self.config[ConfigKey.SEIKA_SAY2_PATH] = self.sv_seikasay2_path.get()
        self.config[ConfigKey.SPEAKER][ConfigKey.CID] = self.sv_speaker.get().split(" ")[0]
        self.config[ConfigKey.SPEAKER][ConfigKey.NAME] = self.sv_speaker.get()
        self.config[ConfigKey.ACCESS_TOKEN] = self.sv_access_token.get()
        self.save_config()
        # ChatGPTの準備
        self.chatbot = Chatbot({ ConfigKey.ACCESS_TOKEN : self.config.get(ConfigKey.ACCESS_TOKEN) }, conversation_id=None)
        self.chatbot.reset_chat()
        try:
            for data in self.chatbot.ask("ping"):
                resp = data["message"]
            if resp:
                self.config_window.destroy()
            else:
                messagebox.showerror(self.APP_NAME, "ChatGPTから応答がありませんでした。")
        except Exception as e:
            self.logger.error(e)
            messagebox.showerror(self.APP_NAME, "ChatGPTとの通信に失敗しました。\nAccess Tokenが誤っていないか確認してください。")

    def run(self):
        # AssistantSeika起動チェック
        self.logger.info("AssistantSeika running check")
        running = False
        while not running:
          running = self.process_running_check(ProcessName.ASSISTANT_SEIKA)
          if not running:
            ans = messagebox.askyesno("AssistantSeika 起動確認", "{} プロセスが見つかりませんでした。\r\nAssistantSeikaが起動していない可能性があります。\r\nはい: 再試行\r\nいいえ: 無視して続行".format(ProcessName.ASSISTANT_SEIKA))
            if ans == True:
              pass
            elif ans == False:
              running = True

        # SeikaSay2存在チェック
        running = False
        seika_say2_path = ProcessName.SEIKA_SAY2
        while not running:
            if os.path.exists(seika_say2_path):
                running = True
            else:
                messagebox.showinfo(ProcessName.SEIKA_SAY2+" 存在確認", "{} が見つかりませんでした。\r\nこの後に表示されるファイルダイアログで {} を選択してください。".format(ProcessName.SEIKA_SAY2, ProcessName.SEIKA_SAY2))
                seika_say2_path = filedialog.askopenfilename(filetype=[(ProcessName.SEIKA_SAY2,"*.exe")], initialdir=os.getcwd())
        self.seikasay2 = SeikaSay2(seika_say2_path)

        # AssistantSeikaから話者一覧取得
        self.logger.info("Get speakers from AssistantSeika")
        running = False
        while not running:
            self.get_speaker_list()
            if self.cids:
                running = True
                self.logger.info("Get cids from AssistantSeika: OK")
                break
            else:
                ans = messagebox.askyesno("AssistantSeika 話者一覧取得", "AssistantSeikaの話者一覧が空です。\r\n製品スキャンが未実行か、AssistantSeikaに対応している音声合成製品が未起動である可能性があります。\r\nはい: 再試行\r\nいいえ: 無視して続行")
                if ans == True:
                    pass
                elif ans == False:
                    self.logger.info("Get cids from AssistantSeika: NG")
                    running = True

        self.logger.debug(self.speakers)

        if not self.config.get(ConfigKey.SPEAKER).get(ConfigKey.CID):
            self.config[ConfigKey.SPEAKER][ConfigKey.CID] = self.cids[0]

        # 設定ウィンドウ表示
        self.open_config_window()
        self.logger.info("話者: {}".format(self.config.get(ConfigKey.SPEAKER).get(ConfigKey.NAME)))

        # メインループ開始
        self.master.mainloop()



if __name__ == "__main__":
  #param = sys.argv
  root = tkinter.Tk()
  app = ChatgptWithVoiceroid(master=root)
  app.run()
