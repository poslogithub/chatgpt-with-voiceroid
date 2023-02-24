import re
import subprocess

class SeikaSay2:

    def __init__(self, path=".\\SeikaSay2.exe"):
        self.path = path

    def get_speak_command(self, cid, text, asynchronize=False, save=None, volume=None, speed=None, pitch=None, alpha=None, intonation=None, emotionEP=None, emotionP=None, overBanner=False):
        if cid and text:
            cmd = "{} -cid {}".format(self.path, cid)
            cmd += " -async" if asynchronize else ""
            cmd += ' -save "{}"'.format(save) if save else ""
            cmd += " -volume {}".format(volume) if volume else ""
            cmd += " -speed {}".format(speed) if speed else ""
            cmd += " -pitch {}".format(pitch) if pitch else ""
            cmd += " -alpha {}".format(alpha) if alpha else ""
            cmd += " -intonation {}".format(intonation) if intonation else ""
            cmd += " -emotion {} {}".format(emotionEP, emotionP) if emotionEP and emotionP else ""
            cmd += " -ob" if overBanner else ""
            cmd += ' -t "{}"'.format(text)
            return cmd
        else:
            return None

    def speak(self, cid, text, asynchronize=False, save=None, volume=None, speed=None, pitch=None, alpha=None, intonation=None, emotionEP=None, emotionP=None, overBanner=False):
        cmd = self.get_speak_command(cid, text, asynchronize, save, volume, speed, pitch, alpha, intonation, emotionEP, emotionP, overBanner)
        if cmd:
            subprocess.run(cmd)
            return text
        else:
            return None
    
    def list(self):
        cids = []
        speakers = []
        cmd = "{} -list".format(self.path)
        try:
            s = subprocess.check_output(cmd)
            for line in s.splitlines():
                if type(line) is bytes:
                    line = line.decode("cp932")
                line = line.strip()
                print(line)
                if re.search(r"^[0-9]", line):
                    cids.append(line.split(" ")[0])
                    speakers.append(line)
        except subprocess.CalledProcessError:
            return None
        return cids, speakers
        
