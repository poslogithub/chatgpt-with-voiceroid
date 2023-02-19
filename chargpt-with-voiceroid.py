from revChatGPT.V1 import Chatbot
import os
import speech_recognition as sr
import json
import wave
import psutil
import pyaudio
import tkinter
from tkinter import messagebox, filedialog, Frame
import tkinter.simpledialog as simpledialog
import logging
import logging.handlers
import re
import sys

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

        # cid決定
        cids, speakers = self.get_speaker_list()
        cid = cids[0]

        # access_token入力
        access_token = simpledialog.askstring('access_token Input', 'https://chat.openai.com/api/auth/session から取得できる access_token を入力してください。')
        config = {
            ConfigKey.ACCESS_TOKEN : access_token
        }

        # マイクの準備
        r = sr.Recognizer()
        mic = sr.Microphone()

        # ChatGPTの準備
        chatbot = Chatbot(config, conversation_id=None)
        chatbot.reset_chat()
        #chatbot.refresh_session()

        print("はじめまして！")


        with mic as source:
            r.adjust_for_ambient_noise(source)

            #while True:
                #try:
                #  audio = r.listen(source)
                #  text = r.recognize_google(audio, language='ja-JP')
                #except sr.UnknownValueError:
                #  pass

            for data in chatbot.ask("こんにちは"):
                resp = data["message"]

            print(resp)
            self.speak(cid, resp)


            #res1 = requests.post('http://localhost:50021/audio_query', params={'text': resp['message'], 'speaker': 8})
            #res2 = requests.post('http://localhost:50021/synthesis', params={'speaker': 14}, data=json.dumps(res1.json()))

            #with open('./test.wav', mode='wb') as f:
            #    f.write(res2.content)

            #print("complete")
            #openWave()


if __name__ == "__main__":
  #param = sys.argv
  root = tkinter.Tk()
  app = ChatgptWithVoiceroid(master=root)
  app.run()
