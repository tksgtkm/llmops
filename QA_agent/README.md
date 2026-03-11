まずpythonのバージョンを固定する(3.12.9にする)
pyenv install 3.12.9

pyenv global 3.12.9

pyenv versionsでpyenvで使えるインストールしたpythonが確認できる


まずuvをインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

その後依存関係をインストール
uv sync

その後仮想環境をアクティブする
source .venv/bin/activate

(ちなみにダウンするときはdeactivate sourceとか含めない)

コンテナの起動
make start.engine

インデックス作成
make create.index

VSCodeはQA_agentのページだけを開くようにすること