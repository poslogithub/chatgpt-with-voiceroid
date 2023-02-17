# chatgpt-with-voiceroid
 ChatGPT+Pythonでボイスロイドとリアルタイムで音声会話できるプログラム（パクリ）

## これは何？

1. [ChatGPT+Pythonでボイスロイドとリアルタイムで音声会話できるプログラムを作った](https://zenn.dev/akashixi/articles/303dd79264e1ff)
2. [FireShotとpyocrとtesseract-OCRとAssistantSeikaとVOICEPEAKを組み合わせてChatGPTを喋らせてみた](https://twitter.com/shuttle_j/status/1625144910830784512)

上記2つを組み合わせれば、1.の「VOICEVOXにリクエストを送ってからレスポンスが返ってくるまで」のレイテンシが大きいという問題が解消できるのではないかと考えました。<br />
VOICEVOXはレスポンスに凄く時間がかかります。VOICEROIDは非常に速いです。VOICEPEAKは使ったこと無いので知りません。<br />
VOICEROIDはVOICEVOXのようなHTTP経由の操作ができない（なんで？？？ 公式仕事して？？？？？）ので、2.と同じく[AssistantSeika](https://hgotoh.jp/wiki/doku.php/documents/voiceroid/assistantseika/assistantseika-000)を使います。<br />
1.の方はAssistantSeikaの存在を知らない（多分）、2.の方は[revChatGPT](https://pypi.org/project/revChatGPT/)の存在を知らない（多分）。<br />
そこに付け込んで自分の手柄にしてしまおうというハイエナムーブですね。<br />
